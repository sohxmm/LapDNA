import json

import pytest
from pydantic import ValidationError

from lapdna.models import ComparisonArtifact


def validate(payload):
    return ComparisonArtifact.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize("mutation", [
    lambda p: p["distance_m"].__setitem__(1, 0),
    lambda p: p["channels_a"]["speed_kph"].pop(),
    lambda p: p["channels_a"]["speed_kph"].__setitem__(0, float("nan")),
    lambda p: p["channels_a"]["brake"].__setitem__(0, 1),
    lambda p: p["channels_a"]["gear"].__setitem__(0, 2.5),
    lambda p: p["channels_a"]["throttle_pct"].__setitem__(0, 101),
    lambda p: p["delta_ms"].__setitem__(1, -50),
    lambda p: p["valid"].__setitem__(1, False),
    lambda p: p["geometry"]["x"].__setitem__(1, None),
    lambda p: p["segments"][0]["evidence_ids"].append("missing"),
    lambda p: p["segments"][0].__setitem__("start_m", 1.0),
    lambda p: p["segments"][0].__setitem__("gain_ms", 99.0),
    lambda p: p["quality"]["checks"].pop(),
    lambda p: p["quality"]["checks"][0].__setitem__("status", "block"),
    lambda p: p.__setitem__("insufficient_evidence_reason", None),
    lambda p: p["provenance"].__setitem__("generated_at", "2024-01-01T00:00:00"),
    lambda p: p.__setitem__("unexpected", True),
])
def test_invalid_artifacts_are_rejected(artifact_payload, mutation):
    mutation(artifact_payload)
    with pytest.raises(ValidationError):
        validate(artifact_payload)


def test_nullable_channels_preserve_gaps(artifact_payload):
    artifact_payload["channels_a"]["speed_kph"][1] = None
    artifact_payload["channels_a"]["time_raw_ms"][1] = None
    artifact_payload["delta_ms"][1] = None
    artifact_payload["valid"][1] = False
    artifact_payload["segments"][0]["gain_ms"] = None
    artifact_payload["segments"][0]["gain_sensitivity_ms"] = None
    comparison = validate(artifact_payload)
    assert comparison.channels_a.speed_kph[1] is None
    assert comparison.delta_ms[1] is None


def test_contract_accepts_negative_delta_with_matching_elapsed_times(artifact_payload):
    artifact_payload["lap_a"], artifact_payload["lap_b"] = artifact_payload["lap_b"], artifact_payload["lap_a"]
    artifact_payload["channels_a"], artifact_payload["channels_b"] = artifact_payload["channels_b"], artifact_payload["channels_a"]
    artifact_payload["delta_ms"] = [-x for x in artifact_payload["delta_ms"]]
    artifact_payload["segments"][0]["gain_ms"] *= -1
    artifact_payload["segments"][0]["gain_sensitivity_ms"] = {"minimum_ms": -100.0, "maximum_ms": -100.0}
    for check in artifact_payload["quality"]["checks"]:
        if check["driver"] == "pair":
            for key in ("official_ms", "observed_ms", "residual_ms"):
                check[key] *= -1
        else:
            check["driver"] = "B" if check["driver"] == "A" else "A"
    comparison = validate(artifact_payload)
    assert comparison.delta_ms[-1] == -100.0
