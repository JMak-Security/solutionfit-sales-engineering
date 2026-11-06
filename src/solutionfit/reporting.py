"""Proposal rendering with input, formula, and simulation provenance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

from solutionfit.assumptions import INPUT_NAMES, AssumptionProfile
from solutionfit.calculator import (
    CalculationEntry,
    ScenarioMetrics,
    SensitivityResult,
)
from solutionfit.simulation import SimulationResult

_CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class ProposalReport:
    profile: AssumptionProfile
    metrics: ScenarioMetrics
    sensitivity: tuple[SensitivityResult, ...]
    simulation: SimulationResult


def _decimal_text(value: Decimal, places: Decimal = _CENT) -> str:
    return f"{value.quantize(places):,.2f}"


def _audit_entry(entry: CalculationEntry) -> dict[str, object]:
    return {
        "metric": entry.metric,
        "formula_id": entry.formula_id,
        "formula": entry.formula,
        "inputs": {name: str(value) for name, value in entry.inputs.items()},
        "value": str(entry.value) if entry.value is not None else None,
        "unit": entry.unit,
    }


def report_payload(report: ProposalReport) -> dict[str, object]:
    profile = report.profile
    metrics = report.metrics
    simulation = report.simulation
    return {
        "schema_version": "1",
        "product": {
            "name": profile.product_name,
            "is_fictional": True,
            "scenario_label": profile.scenario_label,
        },
        "assumption_set": {
            "version": profile.assumption_version,
            "currency": profile.currency,
            "time_horizon_years": profile.time_horizon_years,
            "notes": list(profile.notes),
            "inputs": {
                name: {
                    "low": str(profile.ranges[name].low),
                    "base": str(profile.base[name]),
                    "high": str(profile.ranges[name].high),
                }
                for name in INPUT_NAMES
            },
        },
        "calculations": {
            "annual_baseline_cost": str(metrics.annual_baseline_cost),
            "annual_residual_manual_cost": str(metrics.annual_residual_manual_cost),
            "annual_support_cost": str(metrics.annual_support_cost),
            "annual_modeled_cost": str(metrics.annual_modeled_cost),
            "annual_net_savings": str(metrics.annual_net_savings),
            "implementation_cost": str(metrics.implementation_cost),
            "year_one_modeled_cost": str(metrics.year_one_modeled_cost),
            "horizon_baseline_cost": str(metrics.horizon_baseline_cost),
            "horizon_modeled_cost": str(metrics.horizon_modeled_cost),
            "horizon_net_savings": str(metrics.horizon_net_savings),
            "year_one_roi_percent": str(metrics.year_one_roi_percent),
            "payback_months": (
                str(metrics.payback_months) if metrics.payback_months is not None else None
            ),
            "audit_trail": [_audit_entry(entry) for entry in metrics.audit_trail],
        },
        "sensitivity": [
            {
                "input": result.input_name,
                "formula_id": "roi.year_one.v1",
                "low_roi_percent": str(result.low_roi_percent),
                "base_roi_percent": str(result.base_roi_percent),
                "high_roi_percent": str(result.high_roi_percent),
                "impact_percentage_points": str(result.impact_percentage_points),
                "input_range": {
                    "low": str(profile.ranges[result.input_name].low),
                    "base": str(profile.ranges[result.input_name].base),
                    "high": str(profile.ranges[result.input_name].high),
                },
            }
            for result in report.sensitivity
        ],
        "simulation": {
            "runs": simulation.runs,
            "seed": simulation.seed,
            "distribution": simulation.distribution,
            "independence_assumption": simulation.independence_assumption,
            "percentile_method": simulation.percentile_method,
            "roi_percentiles": {
                "p10": str(simulation.roi_p10_percent),
                "p50": str(simulation.roi_p50_percent),
                "p90": str(simulation.roi_p90_percent),
            },
            "year_one_net_savings_percentiles": {
                "p10": str(simulation.net_savings_p10),
                "p50": str(simulation.net_savings_p50),
                "p90": str(simulation.net_savings_p90),
            },
            "probability_positive_roi": str(simulation.probability_positive_roi),
            "probability_formula": "simulated positive-ROI runs / total runs",
        },
        "caveat": (
            "Illustrative scenario only. Values are assumptions, not a quote, forecast, "
            "customer result, or guarantee."
        ),
    }


def render_markdown(report: ProposalReport) -> str:
    profile = report.profile
    metrics = report.metrics
    simulation = report.simulation
    payback = (
        f"{_decimal_text(metrics.payback_months)} months"
        if metrics.payback_months is not None
        else "Not reached under these assumptions"
    )
    cost_rows = [
        ("Annual baseline cost", metrics.annual_baseline_cost),
        ("Annual modeled cost", metrics.annual_modeled_cost),
        ("Annual net savings", metrics.annual_net_savings),
        ("One-time implementation cost", metrics.implementation_cost),
        (f"{profile.time_horizon_years}-year baseline cost", metrics.horizon_baseline_cost),
        (f"{profile.time_horizon_years}-year modeled cost", metrics.horizon_modeled_cost),
        (f"{profile.time_horizon_years}-year net savings", metrics.horizon_net_savings),
    ]
    lines = [
        f"# Proposal scenario: {profile.scenario_label}",
        "",
        f"**Product:** {profile.product_name} — fictional sample product.",
        f"**Assumption version:** {profile.assumption_version} | **Currency:** {profile.currency}",
        "",
        "> Illustrative model only; not a quote, forecast, customer result, or guarantee.",
        "",
        "## Cost comparison",
        "",
        "| Metric | Modeled value |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {name} | {profile.currency} {_decimal_text(value)} |" for name, value in cost_rows
    )
    lines.extend(
        [
            f"| Year-one ROI | {_decimal_text(metrics.year_one_roi_percent)}% |",
            f"| Payback | {payback} |",
            "",
            "## Versioned assumptions",
            "",
            "| Input | Low | Base | High |",
            "|---|---:|---:|---:|",
        ]
    )
    for name in INPUT_NAMES:
        value_range = profile.ranges[name]
        lines.append(f"| {name} | {value_range.low} | {value_range.base} | {value_range.high} |")
    lines.extend(["", "## Sensitivity: year-one ROI", ""])
    lines.extend(
        [
            "| Input varied | Low ROI | Base ROI | High ROI | Range impact (pp) |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for result in report.sensitivity:
        lines.append(
            f"| {result.input_name} | {_decimal_text(result.low_roi_percent)}% | "
            f"{_decimal_text(result.base_roi_percent)}% | "
            f"{_decimal_text(result.high_roi_percent)}% | "
            f"{_decimal_text(result.impact_percentage_points)} |"
        )
    lines.extend(
        [
            "",
            "Each sensitivity row varies one input while holding all others at base values.",
            "",
            "## Monte Carlo estimate",
            "",
            f"- Runs: {simulation.runs}; seed: {simulation.seed}.",
            f"- Distribution: {simulation.distribution}.",
            f"- Percentile method: {simulation.percentile_method}.",
            f"- ROI P10 / P50 / P90: {_decimal_text(simulation.roi_p10_percent)}% / "
            f"{_decimal_text(simulation.roi_p50_percent)}% / "
            f"{_decimal_text(simulation.roi_p90_percent)}%.",
            f"- Probability of positive year-one ROI: "
            f"{_decimal_text(simulation.probability_positive_roi * Decimal('100'))}%.",
            f"- Independence caveat: {simulation.independence_assumption}",
            "",
            "## Calculation audit",
            "",
            "| Formula ID | Output | Formula | Result |",
            "|---|---|---|---:|",
        ]
    )
    for entry in metrics.audit_trail:
        value = "Not defined" if entry.value is None else str(entry.value)
        lines.append(
            f"| `{entry.formula_id}` | `{entry.metric}` | {entry.formula} | {value} {entry.unit} |"
        )
    lines.extend(
        [
            "",
            "Every audit row records all base inputs in the JSON export. Exact calculations use "
            "`Decimal`; currency is rounded only for display.",
            "",
            "## Assumption notes",
            "",
        ]
    )
    lines.extend(f"- {note}" for note in profile.notes)
    lines.append("")
    return "\n".join(lines)


def render_pdf(report: ProposalReport, destination: Path) -> None:
    profile = report.profile
    metrics = report.metrics
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SmallBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
        )
    )
    story: list[Flowable] = [
        Paragraph(escape(f"{profile.product_name} Proposal Scenario"), styles["Title"]),
        Paragraph(escape(profile.scenario_label), styles["Heading2"]),
        Paragraph(
            "Fictional product; illustrative assumptions only. This is not a quote, forecast, "
            "customer result, or guarantee.",
            styles["BodyText"],
        ),
        Spacer(1, 0.18 * inch),
        Paragraph("Scenario summary", styles["Heading1"]),
    ]
    summary_rows = [
        ["Metric", "Value"],
        [
            "Annual baseline cost",
            f"{profile.currency} {_decimal_text(metrics.annual_baseline_cost)}",
        ],
        ["Annual modeled cost", f"{profile.currency} {_decimal_text(metrics.annual_modeled_cost)}"],
        ["Annual net savings", f"{profile.currency} {_decimal_text(metrics.annual_net_savings)}"],
        ["Implementation cost", f"{profile.currency} {_decimal_text(metrics.implementation_cost)}"],
        ["Year-one ROI", f"{_decimal_text(metrics.year_one_roi_percent)}%"],
        [
            "Payback",
            (
                f"{_decimal_text(metrics.payback_months)} months"
                if metrics.payback_months is not None
                else "Not reached under assumptions"
            ),
        ],
        [
            f"{profile.time_horizon_years}-year net savings",
            f"{profile.currency} {_decimal_text(metrics.horizon_net_savings)}",
        ],
    ]
    story.extend(
        [
            Table(summary_rows, colWidths=[3.0 * inch, 3.5 * inch], repeatRows=1),
            Spacer(1, 0.18 * inch),
            Paragraph("Versioned input ranges", styles["Heading1"]),
        ]
    )
    input_rows = [["Input", "Low", "Base", "High"]]
    input_rows.extend(
        [
            [
                name,
                str(profile.ranges[name].low),
                str(profile.base[name]),
                str(profile.ranges[name].high),
            ]
            for name in INPUT_NAMES
        ]
    )
    story.extend(
        [
            Table(input_rows, repeatRows=1),
            Spacer(1, 0.18 * inch),
            Paragraph("Calculation audit", styles["Heading1"]),
        ]
    )
    audit_rows: list[list[object]] = [["Formula ID", "Formula", "Result"]]
    for entry in metrics.audit_trail:
        result = "Not defined" if entry.value is None else str(entry.value)
        audit_rows.append(
            [
                Paragraph(escape(entry.formula_id), styles["SmallBody"]),
                Paragraph(escape(entry.formula), styles["SmallBody"]),
                Paragraph(escape(f"{result} {entry.unit}"), styles["SmallBody"]),
            ]
        )
    story.extend(
        [
            Table(audit_rows, colWidths=[1.55 * inch, 3.7 * inch, 1.25 * inch], repeatRows=1),
            Spacer(1, 0.18 * inch),
            Paragraph("Sensitivity: year-one ROI", styles["Heading1"]),
        ]
    )
    sensitivity_rows: list[list[object]] = [["Input", "Low ROI", "Base ROI", "High ROI"]]
    sensitivity_rows.extend(
        [
            [
                result.input_name,
                f"{_decimal_text(result.low_roi_percent)}%",
                f"{_decimal_text(result.base_roi_percent)}%",
                f"{_decimal_text(result.high_roi_percent)}%",
            ]
            for result in report.sensitivity
        ]
    )
    story.extend(
        [
            Table(sensitivity_rows, repeatRows=1),
            Spacer(1, 0.18 * inch),
            Paragraph("Monte Carlo estimate", styles["Heading1"]),
            Paragraph(
                escape(
                    f"{report.simulation.runs} runs; seed {report.simulation.seed}; "
                    f"{report.simulation.distribution}; ROI P10/P50/P90 "
                    f"{_decimal_text(report.simulation.roi_p10_percent)}% / "
                    f"{_decimal_text(report.simulation.roi_p50_percent)}% / "
                    f"{_decimal_text(report.simulation.roi_p90_percent)}%; "
                    f"{report.simulation.percentile_method}. "
                    f"{report.simulation.independence_assumption}"
                ),
                styles["SmallBody"],
            ),
        ]
    )
    for note in profile.notes:
        story.append(Paragraph(escape(note), styles["SmallBody"]))

    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7C7D6")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]
    )
    for item in story:
        if isinstance(item, Table):
            item.setStyle(table_style)
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(destination),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"{profile.product_name} fictional proposal scenario",
        author="SolutionFit",
    )
    document.build(story)


def write_json(report: ProposalReport, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report_payload(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
