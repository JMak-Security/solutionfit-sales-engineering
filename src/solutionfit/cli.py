"""Command-line proposal and scenario exports."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

from solutionfit.assumptions import AssumptionProfile, parse_profile
from solutionfit.calculator import analyze_sensitivity, calculate_metrics
from solutionfit.reporting import ProposalReport, render_markdown, render_pdf, write_json
from solutionfit.simulation import run_simulation


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an auditable proposal from a local assumption profile."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    calculate = subparsers.add_parser("calculate", help="calculate and export a scenario proposal")
    calculate.add_argument("--input", type=Path, required=True)
    calculate.add_argument("--json", type=Path, default=Path("output/proposal.json"))
    calculate.add_argument("--markdown", type=Path, default=Path("output/proposal.md"))
    calculate.add_argument("--pdf", type=Path, default=Path("output/proposal.pdf"))
    calculate.add_argument("--runs", type=int, default=10_000)
    calculate.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _load_profile(path: Path) -> AssumptionProfile:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file, parse_float=Decimal, parse_int=Decimal)
    return parse_profile(payload)


def _run(args: argparse.Namespace) -> int:
    profile = _load_profile(args.input)
    report = ProposalReport(
        profile=profile,
        metrics=calculate_metrics(profile),
        sensitivity=analyze_sensitivity(profile),
        simulation=run_simulation(profile, runs=args.runs, seed=args.seed),
    )
    write_json(report, args.json)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    render_pdf(report, args.pdf)
    print(
        f"Built fictional scenario report for assumption version {profile.assumption_version}; "
        f"annual net savings {profile.currency} {report.metrics.annual_net_savings:,.2f}; "
        f"Monte Carlo runs {report.simulation.runs}; seed {report.simulation.seed}."
    )
    return 0


def main() -> int:
    args = _arguments()
    try:
        return _run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"solutionfit: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
