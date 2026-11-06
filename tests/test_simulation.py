from __future__ import annotations

import copy
import random
from decimal import Decimal

import pytest

from solutionfit.assumptions import INPUT_NAMES, AssumptionProfile, parse_profile
from solutionfit.calculator import calculate_metrics
from solutionfit.simulation import _percentile, run_simulation


def test_simulation_is_seeded_and_percentiles_are_ordered(profile: AssumptionProfile) -> None:
    first = run_simulation(profile, runs=300, seed=7)
    second = run_simulation(profile, runs=300, seed=7)
    assert first == second
    assert first.runs == 300
    assert first.seed == 7
    assert first.roi_p10_percent <= first.roi_p50_percent <= first.roi_p90_percent
    assert Decimal("0") <= first.probability_positive_roi <= Decimal("1")


def test_optimized_simulation_matches_full_audited_reference(profile: AssumptionProfile) -> None:
    runs = 100
    seed = 19
    generator = random.Random(seed)  # noqa: S311 - reference sample must reproduce the seed.
    roi_samples: list[Decimal] = []
    savings_samples: list[Decimal] = []
    positive = 0
    for _ in range(runs):
        sampled: dict[str, Decimal] = {}
        for name in INPUT_NAMES:
            value_range = profile.ranges[name]
            draw = generator.triangular(
                float(value_range.low), float(value_range.high), float(value_range.base)
            )
            sample = Decimal(round(draw)) if name == "annual_releases" else Decimal(str(draw))
            sampled[name] = sample
        metrics = calculate_metrics(profile, sampled)
        roi_samples.append(metrics.year_one_roi_percent)
        savings_samples.append(metrics.annual_net_savings - metrics.implementation_cost)
        positive += metrics.year_one_roi_percent > 0

    optimized = run_simulation(profile, runs=runs, seed=seed)
    assert optimized.roi_p10_percent == _percentile(roi_samples, Decimal("0.10"))
    assert optimized.roi_p50_percent == _percentile(roi_samples, Decimal("0.50"))
    assert optimized.roi_p90_percent == _percentile(roi_samples, Decimal("0.90"))
    assert optimized.net_savings_p10 == _percentile(savings_samples, Decimal("0.10"))
    assert optimized.net_savings_p50 == _percentile(savings_samples, Decimal("0.50"))
    assert optimized.net_savings_p90 == _percentile(savings_samples, Decimal("0.90"))
    assert optimized.probability_positive_roi == Decimal(positive) / Decimal(runs)


@pytest.mark.parametrize("runs", [0, 100_001])
def test_simulation_rejects_unbounded_run_counts(profile: AssumptionProfile, runs: int) -> None:
    with pytest.raises(ValueError, match="runs must be between"):
        run_simulation(profile, runs=runs)


def test_simulation_rejects_seed_outside_signed_64_bit_range(profile: AssumptionProfile) -> None:
    with pytest.raises(ValueError, match="seed must be between"):
        run_simulation(profile, runs=1, seed=2**63)


def test_simulation_handles_fixed_ranges_without_division_by_zero(
    profile_payload: object,
) -> None:
    payload = copy.deepcopy(profile_payload)
    assert isinstance(payload, dict)
    base = payload["base"]
    ranges = payload["ranges"]
    assert isinstance(base, dict)
    assert isinstance(ranges, dict)
    for name, value in base.items():
        ranges[name] = {"low": value, "base": value, "high": value}
    profile = parse_profile(payload)
    result = run_simulation(profile, runs=10, seed=1)
    assert result.roi_p10_percent == result.roi_p50_percent == result.roi_p90_percent
