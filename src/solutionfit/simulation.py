"""Seeded Monte Carlo estimates over explicitly declared assumption ranges."""

from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal

from solutionfit.assumptions import INPUT_NAMES, AssumptionProfile
from solutionfit.calculator import calculate_simulation_point

_MAX_RUNS = 100_000
_MIN_SEED = -(2**63)
_MAX_SEED = 2**63 - 1


@dataclass(frozen=True, slots=True)
class SimulationResult:
    runs: int
    seed: int
    distribution: str
    independence_assumption: str
    percentile_method: str
    roi_p10_percent: Decimal
    roi_p50_percent: Decimal
    roi_p90_percent: Decimal
    net_savings_p10: Decimal
    net_savings_p50: Decimal
    net_savings_p90: Decimal
    probability_positive_roi: Decimal


def _percentile(samples: list[Decimal], fraction: Decimal) -> Decimal:
    ordered = sorted(samples)
    position = Decimal(len(ordered) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = position - lower_index
    return ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * weight


def run_simulation(
    profile: AssumptionProfile, runs: int = 10_000, seed: int = 42
) -> SimulationResult:
    if not 1 <= runs <= _MAX_RUNS:
        raise ValueError(f"runs must be between 1 and {_MAX_RUNS}")
    if not _MIN_SEED <= seed <= _MAX_SEED:
        raise ValueError(f"seed must be between {_MIN_SEED} and {_MAX_SEED}")
    generator = random.Random(seed)  # noqa: S311 - deterministic statistical simulation.
    roi_samples: list[Decimal] = []
    savings_samples: list[Decimal] = []
    positive_roi_count = 0

    for _ in range(runs):
        sampled: dict[str, Decimal] = {}
        for name in INPUT_NAMES:
            value_range = profile.ranges[name]
            if value_range.low == value_range.high:
                sample = value_range.low
            else:
                draw = generator.triangular(
                    float(value_range.low), float(value_range.high), float(value_range.base)
                )
                sample = Decimal(round(draw)) if name == "annual_releases" else Decimal(str(draw))
            sampled[name] = sample
        point = calculate_simulation_point(profile, sampled)
        roi_samples.append(point.year_one_roi_percent)
        savings_samples.append(point.annual_net_savings - point.implementation_cost)
        if point.year_one_roi_percent > 0:
            positive_roi_count += 1

    positive_probability = Decimal(positive_roi_count) / Decimal(runs)
    return SimulationResult(
        runs=runs,
        seed=seed,
        distribution=(
            "independent triangular(low, base, high); annual_releases rounded to whole values"
        ),
        independence_assumption="Input ranges are sampled independently; correlations are unknown.",
        percentile_method="linear interpolation at position (sample_count - 1) * percentile",
        roi_p10_percent=_percentile(roi_samples, Decimal("0.10")),
        roi_p50_percent=_percentile(roi_samples, Decimal("0.50")),
        roi_p90_percent=_percentile(roi_samples, Decimal("0.90")),
        net_savings_p10=_percentile(savings_samples, Decimal("0.10")),
        net_savings_p50=_percentile(savings_samples, Decimal("0.50")),
        net_savings_p90=_percentile(savings_samples, Decimal("0.90")),
        probability_positive_roi=positive_probability,
    )
