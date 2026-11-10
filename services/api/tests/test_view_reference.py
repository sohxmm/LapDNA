from copy import deepcopy

from lapdna.alignment.view_delta import prepare_progress
from lapdna.alignment.view_reference import select_speed_reference
from lapdna.view_models import NativeLapView
from test_view_store import publication
import json


def ready(payload):
    data = publication(payload)
    data.update(alignment_candidates={}, alignment_failures={}, reference=None, sector_boundaries_m=[])
    for identifier, row in data["laps"].items():
        lap = prepare_progress(NativeLapView.model_validate_json(json.dumps(row)))
        data["alignment_candidates"][identifier] = {"integrated_length_m": lap.integrated_length_m,
                                                   "cumulative_bound_m": lap.cumulative_bound_m[-1], "bridges": len(lap.bridges)}
    return data


def test_reference_recovers_with_no_geometry_markers_positions_or_legacy_reference(artifact_payload):
    original = ready(artifact_payload)
    before = deepcopy(original)
    result = select_speed_reference(original)
    assert original == before
    assert result["reference"]["lap_id"] == "test-A"
    assert result["reference"]["selection_basis"] == "speed_only"
    assert result["reference"]["geometry_available"] is False
    assert result["reference"]["markers_available"] is False
    assert result["sector_boundaries_m"]
    assert result == select_speed_reference(original)


def test_fastest_unalignable_lap_cannot_be_reference(artifact_payload):
    data = ready(artifact_payload)
    del data["alignment_candidates"]["test-A"]
    assert select_speed_reference(data)["reference"]["lap_id"] == "test-B"


def test_no_speed_candidate_does_not_remove_native_views(artifact_payload):
    data = ready(artifact_payload)
    data["alignment_candidates"] = {}
    result = select_speed_reference(data)
    assert result["reference"] is None
    assert result["laps"] == data["laps"]


def test_geometry_of_a_different_lap_cannot_influence_choice_or_be_relabelled(artifact_payload):
    data = ready(artifact_payload)
    data["reference"] = {"lap_id": "test-B", "length_m": 30., "sha256": "0"*64,
                         "selection_basis": "legacy_v5", "geometry_available": True, "markers_available": True}
    result = select_speed_reference(data)
    assert result["reference"]["lap_id"] == "test-A"
    assert result["reference"]["geometry_available"] is False
    assert result["reference"]["markers_available"] is False


def test_source_conditions_are_preserved_without_becoming_a_reference_gate(artifact_payload):
    from lapdna.analysis.views import build_view
    data = ready(artifact_payload)
    data["legacy_publication_sha256"] = "f" * 64
    data["laps"]["test-A"]["metadata"]["compound"] = "WET"
    legacy = {"publication_sha256": "f" * 64, "laps": {
        "test-A": {"weather_context": "rain_reported"}, "test-B": {"weather_context": "unknown"}}}
    result = select_speed_reference(data, legacy)
    assert result["reference"]["lap_id"] == "test-A"
    warnings = build_view(result, "test-A", "test-B", "telemetry_view").warnings
    assert any("rainfall" in warning.lower() for warning in warnings)
    assert any("wet-weather" in warning for warning in warnings)
    assert any("no dry-track assumption" in warning for warning in warnings)
