from __future__ import annotations

import copy
from decimal import Decimal

import pytest
from conftest import load_profile_payload
from hypothesis import given, settings
from hypothesis import strategies as st

from solutionfit.assumptions import AssumptionProfile, parse_profile
from solutionfit.calculator import calculate_metrics


def test_profile_accepts_visible_versioned_fictional_assumptions(
    profile: AssumptionProfile,
) -> None:
    assert profile.product_name.startswith("QualityPath")
    assert profile.assumption_version == "1.0.0"
    assert profile.scenario_label == "Illustrative assumptions only; not customer data"
    assert profile.base["automation_coverage"] == Decimal("0.60")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("remove_currency", None, "missing currency"),
        ("is_fictional", False, "is_fictional must be true"),
        ("scenario_label", "Customer forecast", "scenario_label"),
        ("currency", "usd", "three-letter uppercase"),
        ("time_horizon_years", 11, "time_horizon_years"),
    ],
)
def test_profile_rejects_invalid_top_level_fields(
    profile_payload: object, field: str, value: object, message: str
) -> None:
    payload = copy.deepcopy(profile_payload)
    assert isinstance(payload, dict)
    if field == "remove_currency":
        payload.pop("currency")
    else:
        payload[field] = value
    with pytest.raises(ValueError, match=message):
        parse_profile(payload)


def test_profile_rejects_invalid_ranges_and_unknown_fields(profile_payload: object) -> None:
    payload = copy.deepcopy(profile_payload)
    assert isinstance(payload, dict)
    ranges = payload["ranges"]
    assert isinstance(ranges, dict)
    ranges["automation_coverage"] = {"low": "0.8", "base": "0.6", "high": "0.9"}
    with pytest.raises(ValueError, match="low <= base <= high"):
        parse_profile(payload)

    payload = copy.deepcopy(profile_payload)
    assert isinstance(payload, dict)
    base = payload["base"]
    assert isinstance(base, dict)
    base["unexpected_input"] = "1"
    with pytest.raises(ValueError, match="unexpected unexpected_input"):
        parse_profile(payload)


@settings(max_examples=30)
@given(coverage=st.decimals(min_value=Decimal("0"), max_value=Decimal("1"), places=2))
def test_residual_manual_cost_never_exceeds_baseline(
    coverage: Decimal,
) -> None:
    payload = load_profile_payload()
    base = payload["base"]
    ranges = payload["ranges"]
    assert isinstance(base, dict)
    assert isinstance(ranges, dict)
    base["automation_coverage"] = str(coverage)
    ranges["automation_coverage"] = {
        "low": "0",
        "base": str(coverage),
        "high": "1",
    }

    metrics = calculate_metrics(parse_profile(payload))
    assert Decimal("0") <= metrics.annual_residual_manual_cost <= metrics.annual_baseline_cost


def test_profile_rejects_nonfinite_and_nonintegral_release_values(profile_payload: object) -> None:
    payload = copy.deepcopy(profile_payload)
    assert isinstance(payload, dict)
    base = payload["base"]
    ranges = payload["ranges"]
    assert isinstance(base, dict)
    assert isinstance(ranges, dict)
    base["annual_license_cost"] = "NaN"
    with pytest.raises(ValueError, match="finite number"):
        parse_profile(payload)

    payload = copy.deepcopy(profile_payload)
    assert isinstance(payload, dict)
    ranges = payload["ranges"]
    assert isinstance(ranges, dict)
    ranges["annual_releases"] = {"low": "10.5", "base": "12", "high": "14"}
    with pytest.raises(ValueError, match="whole numbers"):
        parse_profile(payload)
