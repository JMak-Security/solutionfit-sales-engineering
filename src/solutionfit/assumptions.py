"""Versioned and bounded scenario assumption profiles."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Final

INPUT_NAMES: Final = (
    "annual_releases",
    "manual_hours_per_release",
    "loaded_hourly_rate",
    "automation_coverage",
    "annual_license_cost",
    "monthly_support_hours",
    "support_hourly_rate",
    "implementation_hours",
    "implementation_hourly_rate",
)

_MINIMUMS: Final[dict[str, Decimal]] = {
    "annual_releases": Decimal("1"),
    "manual_hours_per_release": Decimal("0.01"),
    "loaded_hourly_rate": Decimal("0.01"),
    "automation_coverage": Decimal("0"),
    "annual_license_cost": Decimal("0"),
    "monthly_support_hours": Decimal("0"),
    "support_hourly_rate": Decimal("0.01"),
    "implementation_hours": Decimal("0.01"),
    "implementation_hourly_rate": Decimal("0.01"),
}
_MAXIMUMS: Final[dict[str, Decimal]] = {
    "annual_releases": Decimal("3650"),
    "manual_hours_per_release": Decimal("2000"),
    "loaded_hourly_rate": Decimal("1000000"),
    "automation_coverage": Decimal("1"),
    "annual_license_cost": Decimal("1000000000"),
    "monthly_support_hours": Decimal("744"),
    "support_hourly_rate": Decimal("1000000"),
    "implementation_hours": Decimal("100000"),
    "implementation_hourly_rate": Decimal("1000000"),
}
_INTEGER_INPUTS: Final = frozenset({"annual_releases"})
_TOP_LEVEL_KEYS: Final = frozenset(
    {
        "schema_version",
        "assumption_version",
        "product_name",
        "is_fictional",
        "scenario_label",
        "currency",
        "time_horizon_years",
        "base",
        "ranges",
        "notes",
    }
)


@dataclass(frozen=True, slots=True)
class ValueRange:
    low: Decimal
    base: Decimal
    high: Decimal


@dataclass(frozen=True, slots=True)
class AssumptionProfile:
    schema_version: str
    assumption_version: str
    product_name: str
    scenario_label: str
    currency: str
    time_horizon_years: int
    base: Mapping[str, Decimal]
    ranges: Mapping[str, ValueRange]
    notes: tuple[str, ...]


def _object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field} must be a JSON object with string keys")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be a finite number")
    return result


def _exact_keys(value: dict[str, object], expected: frozenset[str], field: str) -> None:
    missing = expected - value.keys()
    extra = value.keys() - expected
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unexpected {', '.join(sorted(extra))}")
        raise ValueError(f"{field} has invalid fields: {'; '.join(details)}")


def parse_profile(payload: object) -> AssumptionProfile:
    data = _object(payload, "profile")
    _exact_keys(data, _TOP_LEVEL_KEYS, "profile")

    schema_version = _text(data["schema_version"], "schema_version")
    if schema_version != "1":
        raise ValueError("schema_version must be '1'")
    assumption_version = _text(data["assumption_version"], "assumption_version")
    product_name = _text(data["product_name"], "product_name")
    if data["is_fictional"] is not True:
        raise ValueError("is_fictional must be true for this sample product")
    scenario_label = _text(data["scenario_label"], "scenario_label")
    label = scenario_label.casefold()
    if "illustrative" not in label and "not customer data" not in label:
        raise ValueError(
            "scenario_label must identify illustrative assumptions or non-customer data"
        )

    currency = _text(data["currency"], "currency")
    if re.fullmatch(r"[A-Z]{3}", currency) is None:
        raise ValueError("currency must be a three-letter uppercase code")

    horizon_value = _decimal(data["time_horizon_years"], "time_horizon_years")
    if horizon_value != horizon_value.to_integral_value() or not 1 <= horizon_value <= 10:
        raise ValueError("time_horizon_years must be an integer from 1 through 10")
    horizon = int(horizon_value)

    raw_base = _object(data["base"], "base")
    raw_ranges = _object(data["ranges"], "ranges")
    expected_inputs = frozenset(INPUT_NAMES)
    _exact_keys(raw_base, expected_inputs, "base")
    _exact_keys(raw_ranges, expected_inputs, "ranges")

    base: dict[str, Decimal] = {}
    ranges: dict[str, ValueRange] = {}
    for name in INPUT_NAMES:
        base_value = _decimal(raw_base[name], f"base.{name}")
        range_values = _object(raw_ranges[name], f"ranges.{name}")
        _exact_keys(range_values, frozenset({"low", "base", "high"}), f"ranges.{name}")
        low = _decimal(range_values["low"], f"ranges.{name}.low")
        range_base = _decimal(range_values["base"], f"ranges.{name}.base")
        high = _decimal(range_values["high"], f"ranges.{name}.high")
        if not low <= range_base <= high:
            raise ValueError(f"ranges.{name} must satisfy low <= base <= high")
        if range_base != base_value:
            raise ValueError(f"ranges.{name}.base must equal base.{name}")
        if low < _MINIMUMS[name] or high > _MAXIMUMS[name]:
            raise ValueError(f"ranges.{name} is outside allowed bounds")
        if name in _INTEGER_INPUTS and any(
            value != value.to_integral_value() for value in (low, range_base, high)
        ):
            raise ValueError(f"ranges.{name} must contain whole numbers")
        base[name] = base_value
        ranges[name] = ValueRange(low=low, base=range_base, high=high)

    raw_notes = data["notes"]
    if not isinstance(raw_notes, list) or not raw_notes:
        raise ValueError("notes must be a non-empty list of explanatory strings")
    notes: list[str] = []
    for note in raw_notes:
        if not isinstance(note, str) or not note.strip():
            raise ValueError("notes must be a non-empty list of explanatory strings")
        notes.append(note.strip())
    return AssumptionProfile(
        schema_version=schema_version,
        assumption_version=assumption_version,
        product_name=product_name,
        scenario_label=scenario_label,
        currency=currency,
        time_horizon_years=horizon,
        base=MappingProxyType(base),
        ranges=MappingProxyType(ranges),
        notes=tuple(notes),
    )
