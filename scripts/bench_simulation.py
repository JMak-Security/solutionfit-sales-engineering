from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import sys
import time
from pathlib import Path

from solutionfit.assumptions import AssumptionProfile, parse_profile
from solutionfit.simulation import run_simulation

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "fictional-scenario-v1.json"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark local scenario Monte Carlo.")
    parser.add_argument("--runs", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--profile", type=Path, default=Path("simulation.prof"))
    args = parser.parse_args()
    if not 1 <= args.runs <= 100_000:
        parser.error("--runs must be between 1 and 100000")
    return args


def _load_sample() -> AssumptionProfile:
    with SAMPLE.open("r", encoding="utf-8") as file:
        return parse_profile(json.load(file))


def main() -> int:
    args = _arguments()
    profile = _load_sample()

    started = time.perf_counter()
    result = run_simulation(profile, runs=args.runs, seed=args.seed)
    elapsed = time.perf_counter() - started

    profiler = cProfile.Profile()
    profiler.enable()
    profiled_result = run_simulation(profile, runs=args.runs, seed=args.seed)
    profiler.disable()
    output = io.StringIO()
    pstats.Stats(profiler, stream=output).sort_stats("tottime").print_stats(10)
    args.profile.parent.mkdir(parents=True, exist_ok=True)
    profiler.dump_stats(str(args.profile))

    print(
        json.dumps(
            {
                "runs": result.runs,
                "seed": result.seed,
                "elapsed_seconds": round(elapsed, 6),
                "runs_per_second": round(args.runs / elapsed, 2),
                "python": sys.version.split()[0],
                "profile_file": str(args.profile),
                "profiled_result_matches": profiled_result == result,
                "roi_p50_percent": str(result.roi_p50_percent),
                "probability_positive_roi": str(result.probability_positive_roi),
                "top_internal_functions": output.getvalue(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if profiled_result == result else 1


if __name__ == "__main__":
    raise SystemExit(main())
