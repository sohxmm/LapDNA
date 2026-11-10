"""The opt-in envelope must not alter legacy serialization or observation gates."""
from hashlib import sha256
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from lapdna.main import create_app
from lapdna.view_models import ChannelSpan, ViewCompareRequest

ROOT = Path(__file__).resolve().parents[3]


def test_legacy_runtime_bytes_remain_frozen():
    receipt = json.loads((ROOT / "config/telemetry-coverage.json").read_bytes())["gate_attribution"]
    for name, expected in receipt["runtime_sha256"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def test_view_tiers_are_opt_in_and_old_detail_levels_survive():
    schema = create_app().openapi()
    assert "/api/v1/views/compare" in schema["paths"]
    assert schema["components"]["schemas"]["ViewCompareRequest"]["properties"]["requested_tier"]["enum"] == [
        "telemetry_view", "aligned_delta", "analysis"]
    assert "requested_tier" not in schema["components"]["schemas"]["CompareRequest"]["properties"]
    assert ViewCompareRequest(session_id="session", lap_a_id="a", lap_b_id="b").requested_tier == "aligned_delta"


@pytest.mark.parametrize("channel", ["gear", "brake"])
def test_discrete_gaps_can_never_claim_a_connector(channel):
    with pytest.raises(ValidationError, match="cannot be bridged"):
        ChannelSpan(channel=channel, start_elapsed_ms=0, end_elapsed_ms=1000,
                    state="bridged", render_hint="dashed_connector", reason="Native interval")
