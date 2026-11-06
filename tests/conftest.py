from __future__ import annotations

import json
from pathlib import Path

import pytest

from solutionfit.assumptions import AssumptionProfile, parse_profile

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PROFILE = ROOT / "examples" / "fictional-scenario-v1.json"


def load_profile() -> AssumptionProfile:
    return parse_profile(load_profile_payload())


def load_profile_payload() -> dict[str, object]:
    with SAMPLE_PROFILE.open("r", encoding="utf-8") as file:
        payload: object = json.load(file)
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise ValueError("sample profile must be an object with string keys")
    return {key: value for key, value in payload.items()}


@pytest.fixture
def profile() -> AssumptionProfile:
    return load_profile()


@pytest.fixture
def profile_payload() -> object:
    return load_profile_payload()
