from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import load_profile
from hypothesis import given
from hypothesis import strategies as st

from solutionfit.assumptions import AssumptionProfile
from solutionfit.calculator import (
    analyze_sensitivity,
    calculate_metrics,
    calculate_simulation_point,
)


def test_base_case_matches_hand_calculated_costs(profile: AssumptionProfile) -> None:
    metrics = calculate_metrics(profile)

    assert metrics.annual_baseline_cost == Decimal("72000")
    assert metrics.annual_residual_manual_cost == Decimal("28800")
    assert metrics.annual_support_cost == Decimal("7200")
    assert metrics.annual_modeled_cost == Decimal("48000")
    assert metrics.annual_net_savings == Decimal("24000")
    assert metrics.implementation_cost == Decimal("10800")
    assert metrics.year_one_modeled_cost == Decimal("58800")
    assert metrics.horizon_baseline_cost == Decimal("216000")
    assert metrics.horizon_modeled_cost == Decimal("154800")
    assert metrics.horizon_net_savings == Decimal("61200")
    assert metrics.year_one_roi_percent == Decimal("122.2222222222222222222222222")
    assert metrics.payback_months == Decimal("5.4")


def test_audit_entries_include_formula_ids_inputs_and_values(profile: AssumptionProfile) -> None:
    metrics = calculate_metrics(profile)
    assert len(metrics.audit_trail) == 12
    entry = next(item for item in metrics.audit_trail if item.metric == "annual_baseline_cost")
    assert entry.formula_id == "cost.baseline.annual.v1"
    assert entry.value == Decimal("72000")
    assert entry.inputs["annual_releases"] == Decimal("12")
    assert entry.inputs["loaded_hourly_rate"] == Decimal("75.00")


def test_sensitivity_orders_inputs_by_year_one_roi_impact(profile: AssumptionProfile) -> None:
    results = analyze_sensitivity(profile)
    assert len(results) == 9
    assert results[0].impact_percentage_points >= results[-1].impact_percentage_points
    assert all(
        result.base_roi_percent == calculate_metrics(profile).year_one_roi_percent
        for result in results
    )


def test_override_rejects_unknown_assumption(profile: AssumptionProfile) -> None:
    with pytest.raises(ValueError, match="unknown input"):
        calculate_metrics(profile, {"unknown": Decimal("1")})


@given(
    releases=st.integers(min_value=10, max_value=14),
    hours=st.decimals(min_value=Decimal("60"), max_value=Decimal("100"), places=1),
    rate=st.decimals(min_value=Decimal("60"), max_value=Decimal("90"), places=2),
)
def test_baseline_cost_formula_is_multiplicative(
    releases: int, hours: Decimal, rate: Decimal
) -> None:
    metrics = calculate_metrics(
        load_profile(),
        {
            "annual_releases": Decimal(releases),
            "manual_hours_per_release": hours,
            "loaded_hourly_rate": rate,
        },
    )
    assert metrics.annual_baseline_cost == Decimal(releases) * hours * rate


def test_override_must_remain_inside_declared_range(profile: AssumptionProfile) -> None:
    with pytest.raises(ValueError, match="outside its declared range"):
        calculate_metrics(profile, {"automation_coverage": Decimal("1.1")})


def test_fast_simulation_calculation_matches_audited_path_at_range_boundaries(
    profile: AssumptionProfile,
) -> None:
    for name, value_range in profile.ranges.items():
        for value in (value_range.low, value_range.base, value_range.high):
            audited = calculate_metrics(profile, {name: value})
            fast = calculate_simulation_point(profile, {name: value})
            assert fast.annual_net_savings == audited.annual_net_savings
            assert fast.implementation_cost == audited.implementation_cost
            assert fast.year_one_roi_percent == audited.year_one_roi_percent
