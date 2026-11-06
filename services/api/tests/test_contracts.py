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
    artifact_payload["estimated_minisectors"][0]["gain_ms"] = None
    comparison = validate(artifact_payload)
    assert comparison.channels_a.speed_kph[1] is None
    assert comparison.delta_ms[1] is None


def test_measured_brake_preserves_switch_and_unknown_samples(artifact_payload):
    artifact_payload["channels_a"]["brake"] = [True, False, None]
    comparison = validate(artifact_payload)
    assert comparison.channels_a.brake == [True, False, None]


def test_missing_brake_is_null_and_cannot_carry_inferred_values(artifact_payload):
    artifact_payload["channel_provenance_a"]["brake"] = {
        "status": "missing", "source_channel": None, "reason": "No native brake channel was returned",
    }
    artifact_payload["channels_a"]["brake"] = [None, None, None]
    assert validate(artifact_payload).channel_provenance_a.brake.status == "missing"
    artifact_payload["channels_a"]["brake"][0] = False
    with pytest.raises(ValidationError, match="only null"):
        validate(artifact_payload)


@pytest.mark.parametrize("source", ["inferred_from_speed", "Throttle", None])
def test_brake_cannot_claim_another_channel_as_its_source(artifact_payload, source):
    artifact_payload["channel_provenance_a"]["brake"]["source_channel"] = source
    with pytest.raises(ValidationError):
        validate(artifact_payload)


def test_channel_evidence_cannot_claim_missing_brake(artifact_payload):
    artifact_payload["channels_a"]["brake"] = [None, None, None]
    artifact_payload["channel_provenance_a"]["brake"] = {
        "status": "missing", "source_channel": None, "reason": "No source brake signal",
    }
    artifact_payload["evidence"] = [{
        "evidence_id": "invented-brake", "metric": "brake_onset", "unit": "m", "start_m": 0.0, "end_m": 1.0,
        "value_a": 0.5, "value_b": None, "difference_b_minus_a": None,
        "native_samples_a": 0, "native_samples_b": 0,
        "max_support_span_ms_a": 0.0, "max_support_span_ms_b": 0.0,
    }]
    with pytest.raises(ValidationError, match="measured source signal"):
        validate(artifact_payload)


def channel_evidence(metric="brake_onset", unit="m", **updates):
    evidence = {
        "evidence_id": "channel-support", "metric": metric, "unit": unit,
        "start_m": 0.0, "end_m": 1.0, "value_a": None, "value_b": None,
        "difference_b_minus_a": None, "native_samples_a": 1, "native_samples_b": 1,
        "max_support_span_ms_a": 0.0, "max_support_span_ms_b": 0.0,
    }
    return evidence | updates


@pytest.mark.parametrize("metric,unit", [
    ("minimum_speed", "km/h"), ("brake_onset", "m"),
    ("throttle_pickup", "m"), ("gear_at_marker", "gear"),
])
@pytest.mark.parametrize("driver", ["a", "b"])
@pytest.mark.parametrize("claim", ["value", "interval"])
def test_channel_claims_require_that_drivers_native_samples(artifact_payload, metric, unit, driver, claim):
    evidence = channel_evidence(metric, unit, **{f"native_samples_{driver}": 0})
    evidence[f"{claim}_{driver}"] = 0.5 if claim == "value" else [0.4, 0.6]
    artifact_payload["evidence"] = [evidence]
    with pytest.raises(ValidationError, match="positive native sample support"):
        validate(artifact_payload)


@pytest.mark.parametrize("metric,unit,channel,known_value", [
    ("minimum_speed", "km/h", "speed_kph", 3.0),
    ("brake_onset", "m", "brake", False),
    ("throttle_pickup", "m", "throttle_pct", 100.0),
    ("gear_at_marker", "gear", "gear", 2),
])
@pytest.mark.parametrize("driver", ["a", "b"])
def test_distant_channel_sample_cannot_support_a_local_claim(artifact_payload, metric, unit, channel, known_value, driver):
    artifact_payload[f"channels_{driver}"][channel] = [None, None, known_value]
    artifact_payload["evidence"] = [channel_evidence(metric, unit, **{f"value_{driver}": 0.5})]
    with pytest.raises(ValidationError, match="local display support"):
        validate(artifact_payload)


def test_unsupported_brake_claim_cannot_reach_observations(artifact_payload):
    artifact_payload["channels_a"]["brake"] = [None, None, False]
    evidence = channel_evidence(value_a=0.5, native_samples_a=0)
    artifact_payload["evidence"] = [evidence]
    artifact_payload["observations"] = [{
        "observation_id": "unsupported-claim", "template_id": "control_pattern",
        "segment_id": "test-segment", "text": "A applied the brake at 0.5 m.",
        "evidence_ids": [evidence["evidence_id"]],
    }]
    with pytest.raises(ValidationError, match="positive native sample support"):
        validate(artifact_payload)


def test_narrow_window_can_use_known_bracketing_display_samples(artifact_payload):
    artifact_payload["channels_a"]["brake"] = [False, False, None]
    artifact_payload["evidence"] = [channel_evidence(start_m=0.25, end_m=0.75, value_a=0.5)]
    assert validate(artifact_payload).evidence[0].value_a == 0.5
    artifact_payload["channels_a"]["brake"][1] = None
    with pytest.raises(ValidationError, match="local display support"):
        validate(artifact_payload)


def test_transition_bracket_may_extend_outside_analysis_window(artifact_payload):
    artifact_payload["evidence"] = [channel_evidence(
        start_m=0.95, end_m=1.05, interval_a=[0.9, 1.1], native_samples_b=0,
    )]
    assert validate(artifact_payload).evidence[0].interval_a == (0.9, 1.1)


def test_contract_accepts_negative_delta_with_matching_elapsed_times(artifact_payload):
    artifact_payload["lap_a"], artifact_payload["lap_b"] = artifact_payload["lap_b"], artifact_payload["lap_a"]
    artifact_payload["channels_a"], artifact_payload["channels_b"] = artifact_payload["channels_b"], artifact_payload["channels_a"]
    artifact_payload["delta_ms"] = [-x for x in artifact_payload["delta_ms"]]
    artifact_payload["segments"][0]["gain_ms"] *= -1
    artifact_payload["estimated_minisectors"][0]["gain_ms"] *= -1
    artifact_payload["segments"][0]["gain_sensitivity_ms"] = {"minimum_ms": -100.0, "maximum_ms": -100.0}
    for check in artifact_payload["quality"]["checks"]:
        if check["driver"] == "pair":
            for key in ("official_ms", "observed_ms", "residual_ms"):
                check[key] *= -1
        else:
            check["driver"] = "B" if check["driver"] == "A" else "A"
    comparison = validate(artifact_payload)
    assert comparison.delta_ms[-1] == -100.0


def test_corner_summary_reconciles_to_reference_class_and_segment_gains(artifact_payload):
    segment = artifact_payload["segments"][0]
    segment.update(kind="corner", speed_class="medium")
    artifact_payload["corners"] = [{
        "marker_id": "T1", "number": 1, "label": "T1", "distance_m": 1.0, "segment_id": segment["segment_id"],
        "reference_speed_kph": 150.0, "speed_class": "medium",
    }]
    summary = artifact_payload["analysis"]["categories"][1]
    summary.update(included_segment_ids=[segment["segment_id"]], independent_units=1, distance_coverage=1.0,
                   gains_a_ms=100.0, gains_b_ms=0.0, net_gain_ms=100.0, a_wins=1,
                   sensitivity={"minimum_ms": 100.0, "maximum_ms": 100.0})
    assert validate(artifact_payload).analysis.categories[1].net_gain_ms == 100.0
    summary["net_gain_ms"] = 90.0
    with pytest.raises(ValidationError):
        validate(artifact_payload)
    summary["net_gain_ms"] = 100.0
    artifact_payload["corners"][0]["speed_class"] = "low"
    with pytest.raises(ValidationError):
        validate(artifact_payload)


@pytest.mark.parametrize("mutation", [
    lambda data: data["estimated_minisectors"][0].update(source="official_timing"),
    lambda data: data["estimated_minisectors"][0].update(end_m=1),
    lambda data: data["estimated_minisectors"][0].update(gain_ms=-100.0),
    lambda data: data["pairing"].update(mode="cross_phase", warnings=["Test"]),
    lambda data: data["lap_b"].update(phase="Q1"),
    lambda data: data["analysis"].update(pattern="high_medium_gain_low_loss", pattern_driver="A"),
    lambda data: data["analysis"]["categories"][1].update(assessment="a_advantage"),
])
def test_unfounded_chart_and_analysis_claims_fail_validation(artifact_payload, mutation):
    mutation(artifact_payload)
    with pytest.raises(ValidationError):
        validate(artifact_payload)
