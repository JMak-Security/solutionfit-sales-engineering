from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from solutionfit.assumptions import AssumptionProfile
from solutionfit.calculator import analyze_sensitivity, calculate_metrics
from solutionfit.cli import main
from solutionfit.reporting import (
    ProposalReport,
    render_markdown,
    render_pdf,
    report_payload,
    write_json,
)
from solutionfit.simulation import run_simulation


def _report(profile: AssumptionProfile) -> ProposalReport:
    return ProposalReport(
        profile=profile,
        metrics=calculate_metrics(profile),
        sensitivity=analyze_sensitivity(profile),
        simulation=run_simulation(profile, runs=50, seed=3),
    )


def test_json_and_markdown_keep_full_provenance(profile: AssumptionProfile, tmp_path: Path) -> None:
    report = _report(profile)
    json_path = tmp_path / "nested" / "proposal.json"
    write_json(report, json_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["product"]["is_fictional"] is True
    assert len(payload["calculations"]["audit_trail"]) == 12
    assert set(payload["calculations"]["audit_trail"][0]["inputs"]) == set(profile.base)
    assert payload["simulation"]["seed"] == 3
    assert payload["assumption_set"]["version"] == "1.0.0"

    markdown = render_markdown(report)
    assert "not a quote, forecast" in markdown
    assert "cost.baseline.annual.v1" in markdown
    assert "independently" in markdown
    assert report_payload(report)["caveat"]


def test_pdf_export_has_valid_signature_and_nonempty_content(
    profile: AssumptionProfile, tmp_path: Path
) -> None:
    destination = tmp_path / "proposal.pdf"
    render_pdf(_report(profile), destination)
    contents = destination.read_bytes()
    assert contents.startswith(b"%PDF-")
    assert contents.rstrip().endswith(b"%%EOF")


def test_cli_generates_json_markdown_and_pdf(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().parents[1] / "examples" / "fictional-scenario-v1.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "solutionfit",
            "calculate",
            "--input",
            str(source),
            "--runs",
            "100",
            "--seed",
            "11",
            "--json",
            str(tmp_path / "result.json"),
            "--markdown",
            str(tmp_path / "result.md"),
            "--pdf",
            str(tmp_path / "result.pdf"),
        ],
    )
    assert main() == 0
    assert "annual net savings USD 24,000.00" in capsys.readouterr().out
    assert (tmp_path / "result.json").is_file()
    assert (tmp_path / "result.md").is_file()
    assert (tmp_path / "result.pdf").is_file()
