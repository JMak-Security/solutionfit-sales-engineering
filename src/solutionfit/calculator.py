"""Exact base-case formulas and one-at-a-time sensitivity analysis."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from solutionfit.assumptions import INPUT_NAMES, AssumptionProfile

ZERO = Decimal("0")
TWELVE = Decimal("12")
HUNDRED = Decimal("100")


@dataclass(frozen=True, slots=True)
class CalculationEntry:
    metric: str
    formula_id: str
    formula: str
    inputs: Mapping[str, Decimal]
    value: Decimal | None
    unit: str


@dataclass(frozen=True, slots=True)
class ScenarioMetrics:
    annual_baseline_cost: Decimal
    annual_residual_manual_cost: Decimal
    annual_support_cost: Decimal
    annual_modeled_cost: Decimal
    annual_net_savings: Decimal
    implementation_cost: Decimal
    year_one_modeled_cost: Decimal
    horizon_baseline_cost: Decimal
    horizon_modeled_cost: Decimal
    horizon_net_savings: Decimal
    year_one_roi_percent: Decimal
    payback_months: Decimal | None
    audit_trail: tuple[CalculationEntry, ...]


@dataclass(frozen=True, slots=True)
class SimulationPoint:
    annual_net_savings: Decimal
    implementation_cost: Decimal
    year_one_roi_percent: Decimal


@dataclass(frozen=True, slots=True)
class _CoreMetrics:
    values: dict[str, Decimal]
    annual_baseline_cost: Decimal
    annual_residual_manual_cost: Decimal
    annual_support_cost: Decimal
    annual_modeled_cost: Decimal
    annual_net_savings: Decimal
    implementation_cost: Decimal
    year_one_modeled_cost: Decimal
    horizon_baseline_cost: Decimal
    horizon_modeled_cost: Decimal
    horizon_net_savings: Decimal
    year_one_roi_percent: Decimal
    payback_months: Decimal | None


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    input_name: str
    low_roi_percent: Decimal
    base_roi_percent: Decimal
    high_roi_percent: Decimal
    impact_percentage_points: Decimal


def calculate_metrics(
    profile: AssumptionProfile, overrides: Mapping[str, Decimal] | None = None
) -> ScenarioMetrics:
    core = _calculate_core(profile, overrides)
    audit_inputs = MappingProxyType(dict(core.values))
    entries = (
        CalculationEntry(
            "annual_baseline_cost",
            "cost.baseline.annual.v1",
            "annual_releases * manual_hours_per_release * loaded_hourly_rate",
            audit_inputs,
            core.annual_baseline_cost,
            profile.currency,
        ),
        CalculationEntry(
            "annual_residual_manual_cost",
            "cost.residual_manual.annual.v1",
            "annual_releases * manual_hours_per_release * "
            "(1 - automation_coverage) * loaded_hourly_rate",
            audit_inputs,
            core.annual_residual_manual_cost,
            profile.currency,
        ),
        CalculationEntry(
            "annual_support_cost",
            "cost.support.annual.v1",
            "monthly_support_hours * 12 * support_hourly_rate",
            audit_inputs,
            core.annual_support_cost,
            profile.currency,
        ),
        CalculationEntry(
            "annual_modeled_cost",
            "cost.modeled.annual.v1",
            "annual_residual_manual_cost + annual_support_cost + annual_license_cost",
            audit_inputs,
            core.annual_modeled_cost,
            profile.currency,
        ),
        CalculationEntry(
            "annual_net_savings",
            "savings.net.annual.v1",
            "annual_baseline_cost - annual_modeled_cost",
            audit_inputs,
            core.annual_net_savings,
            profile.currency,
        ),
        CalculationEntry(
            "implementation_cost",
            "cost.implementation.one_time.v1",
            "implementation_hours * implementation_hourly_rate",
            audit_inputs,
            core.implementation_cost,
            profile.currency,
        ),
        CalculationEntry(
            "year_one_modeled_cost",
            "cost.modeled.year_one.v1",
            "annual_modeled_cost + implementation_cost",
            audit_inputs,
            core.year_one_modeled_cost,
            profile.currency,
        ),
        CalculationEntry(
            "horizon_baseline_cost",
            "cost.baseline.horizon.v1",
            "annual_baseline_cost * time_horizon_years",
            audit_inputs,
            core.horizon_baseline_cost,
            profile.currency,
        ),
        CalculationEntry(
            "horizon_modeled_cost",
            "cost.modeled.horizon.v1",
            "annual_modeled_cost * time_horizon_years + implementation_cost",
            audit_inputs,
            core.horizon_modeled_cost,
            profile.currency,
        ),
        CalculationEntry(
            "horizon_net_savings",
            "savings.net.horizon.v1",
            "horizon_baseline_cost - horizon_modeled_cost",
            audit_inputs,
            core.horizon_net_savings,
            profile.currency,
        ),
        CalculationEntry(
            "year_one_roi_percent",
            "roi.year_one.v1",
            "(annual_net_savings - implementation_cost) / implementation_cost * 100",
            audit_inputs,
            core.year_one_roi_percent,
            "percent",
        ),
        CalculationEntry(
            "payback_months",
            "payback.months.v1",
            "implementation_cost / (annual_net_savings / 12), only when savings are positive",
            audit_inputs,
            core.payback_months,
            "months",
        ),
    )
    return ScenarioMetrics(
        annual_baseline_cost=core.annual_baseline_cost,
        annual_residual_manual_cost=core.annual_residual_manual_cost,
        annual_support_cost=core.annual_support_cost,
        annual_modeled_cost=core.annual_modeled_cost,
        annual_net_savings=core.annual_net_savings,
        implementation_cost=core.implementation_cost,
        year_one_modeled_cost=core.year_one_modeled_cost,
        horizon_baseline_cost=core.horizon_baseline_cost,
        horizon_modeled_cost=core.horizon_modeled_cost,
        horizon_net_savings=core.horizon_net_savings,
        year_one_roi_percent=core.year_one_roi_percent,
        payback_months=core.payback_months,
        audit_trail=entries,
    )


def calculate_simulation_point(
    profile: AssumptionProfile, overrides: Mapping[str, Decimal]
) -> SimulationPoint:
    core = _calculate_core(profile, overrides)
    return SimulationPoint(
        annual_net_savings=core.annual_net_savings,
        implementation_cost=core.implementation_cost,
        year_one_roi_percent=core.year_one_roi_percent,
    )


def _calculate_core(
    profile: AssumptionProfile, overrides: Mapping[str, Decimal] | None
) -> _CoreMetrics:
    values = dict(profile.base)
    if overrides:
        if not overrides.keys() <= set(INPUT_NAMES):
            raise ValueError("calculation overrides contain an unknown input")
        for name, value in overrides.items():
            value_range = profile.ranges[name]
            if not value.is_finite() or not value_range.low <= value <= value_range.high:
                raise ValueError(f"calculation override for {name} is outside its declared range")
            if name == "annual_releases" and value != value.to_integral_value():
                raise ValueError("calculation override for annual_releases must be a whole number")
        values.update(overrides)
    annual_releases = values["annual_releases"]
    hours_per_release = values["manual_hours_per_release"]
    hourly_rate = values["loaded_hourly_rate"]
    automation_coverage = values["automation_coverage"]
    annual_license_cost = values["annual_license_cost"]
    monthly_support_hours = values["monthly_support_hours"]
    support_hourly_rate = values["support_hourly_rate"]
    implementation_hours = values["implementation_hours"]
    implementation_hourly_rate = values["implementation_hourly_rate"]

    annual_baseline = annual_releases * hours_per_release * hourly_rate
    residual_manual = annual_releases * hours_per_release * (1 - automation_coverage)
    residual_manual_cost = residual_manual * hourly_rate
    support_cost = monthly_support_hours * TWELVE * support_hourly_rate
    annual_modeled_cost = residual_manual_cost + support_cost + annual_license_cost
    annual_savings = annual_baseline - annual_modeled_cost
    implementation_cost = implementation_hours * implementation_hourly_rate
    year_one_modeled_cost = annual_modeled_cost + implementation_cost
    horizon_baseline_cost = annual_baseline * profile.time_horizon_years
    horizon_modeled_cost = annual_modeled_cost * profile.time_horizon_years + implementation_cost
    horizon_savings = horizon_baseline_cost - horizon_modeled_cost
    roi = (annual_savings - implementation_cost) / implementation_cost * HUNDRED
    payback = implementation_cost / (annual_savings / TWELVE) if annual_savings > ZERO else None
    return _CoreMetrics(
        values=values,
        annual_baseline_cost=annual_baseline,
        annual_residual_manual_cost=residual_manual_cost,
        annual_support_cost=support_cost,
        annual_modeled_cost=annual_modeled_cost,
        annual_net_savings=annual_savings,
        implementation_cost=implementation_cost,
        year_one_modeled_cost=year_one_modeled_cost,
        horizon_baseline_cost=horizon_baseline_cost,
        horizon_modeled_cost=horizon_modeled_cost,
        horizon_net_savings=horizon_savings,
        year_one_roi_percent=roi,
        payback_months=payback,
    )


def analyze_sensitivity(profile: AssumptionProfile) -> tuple[SensitivityResult, ...]:
    results: list[SensitivityResult] = []
    for name, value_range in profile.ranges.items():
        low = calculate_metrics(profile, {name: value_range.low}).year_one_roi_percent
        high = calculate_metrics(profile, {name: value_range.high}).year_one_roi_percent
        base = calculate_metrics(profile).year_one_roi_percent
        results.append(
            SensitivityResult(
                input_name=name,
                low_roi_percent=low,
                base_roi_percent=base,
                high_roi_percent=high,
                impact_percentage_points=abs(high - low),
            )
        )
    return tuple(sorted(results, key=lambda result: result.impact_percentage_points, reverse=True))
