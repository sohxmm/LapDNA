import gzip
from hashlib import sha256
import json

from fastapi.testclient import TestClient

from lapdna.alignment.view import CarStream
from lapdna.analysis.engine import canonical_hash
from lapdna.analysis.views import build_view
from lapdna.main import create_app
from lapdna.models import ComparisonArtifact
from test_native_views import EPOCH, rows


def publication(artifact_payload):
    laps = {}
    for name in ("lap_a", "lap_b"):
        lap = artifact_payload[name]
        view = CarStream(rows([0, .4, .8, 1.2])).view(lap, EPOCH.timestamp(), EPOCH.timestamp() + 1)
        laps[lap["lap_id"]] = view.model_dump(mode="json")
    provenance = {key: value for key, value in artifact_payload["provenance"].items()
                  if key not in ("reference_sha256", "reference_lap_id", "circuit_revision")}
    provenance["methodology_version"] = "distance-v6-fastf1-native"
    result = {"session": artifact_payload["session"], "provenance": provenance,
              "schema_version": "2.0.0", "laps": laps, "failures": {}}
    result["publication_sha256"] = canonical_hash(result)
    return result


def write(tmp_path, data):
    raw = gzip.compress(json.dumps(data).encode(), mtime=0)
    (tmp_path / "session.json.gz").write_bytes(raw)
    (tmp_path / "publication.json").write_text(json.dumps({"sessions": {
        data["session"]["session_id"]: {"path": "session.json.gz", "sha256": sha256(raw).hexdigest()}}}))


def test_opt_in_route_serves_real_native_views_without_reference(tmp_path, artifact_payload):
    data = publication(artifact_payload)
    write(tmp_path, data)
    client = TestClient(create_app(view_dir=tmp_path))
    request = {"session_id": data["session"]["session_id"], "lap_a_id": "test-B", "lap_b_id": "test-A", "requested_tier": "telemetry_view"}
    response = client.post("/api/v1/views/compare", json=request)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["swapped"] is True
    assert result["artifact"]["view_tier"] == "telemetry_view"
    assert result["artifact"]["alignment"] is None
    assert result["artifact"]["legacy_analysis"] is None


def test_missing_publication_and_tampered_bytes_are_never_fallback_data(tmp_path, artifact_payload):
    client = TestClient(create_app(view_dir=tmp_path))
    request = {"session_id": "synthetic-session", "lap_a_id": "test-A", "lap_b_id": "test-B"}
    assert client.post("/api/v1/views/compare", json=request).status_code == 409
    write(tmp_path, publication(artifact_payload))
    (tmp_path / "session.json.gz").write_bytes(b"tampered")
    assert client.post("/api/v1/views/compare", json=request).status_code == 503


def add_alignment(data):
    data.update(reference={"lap_id": "test-A", "length_m": 30., "sha256": "0" * 64,
        "selection_basis": "legacy_v5", "geometry_available": False, "markers_available": False},
        sector_boundaries_m=[7.5, 22.5], alignment_candidates={key: {} for key in data["laps"]}, alignment_failures={})


def test_tier1_and_v5_nested_payload_never_rewrite_legacy_bytes(artifact_payload):
    data = publication(artifact_payload)
    add_alignment(data)
    legacy = ComparisonArtifact.model_validate_json(json.dumps(artifact_payload))
    before = legacy.model_dump_json()
    result = build_view(data, "test-B", "test-A", "analysis", legacy)
    assert result.view_tier == "analysis"
    assert result.legacy_analysis.model_dump_json() == before
    assert legacy.model_dump_json() == before
    tier0 = build_view(data, "test-A", "test-B", "telemetry_view", legacy)
    assert tier0.alignment is tier0.legacy_analysis is None


def test_speed_failure_falls_back_with_reason_without_hiding_native_view(artifact_payload):
    data = publication(artifact_payload)
    add_alignment(data)
    del data["alignment_candidates"]["test-A"]
    data["alignment_failures"]["test-A"] = {"gate": "speed_gap_over_2s", "reason": "Native speed gap exceeds 2 s."}
    result = build_view(data, "test-A", "test-B", "analysis")
    assert result.view_tier == "telemetry_view"
    assert result.lap_a.channels.speed_kph
    assert "exceeds 2 s" in result.unavailable_reasons["aligned_delta"][0]


def test_bridged_progress_cannot_supply_legacy_corner_analysis(artifact_payload):
    data = publication(artifact_payload)
    add_alignment(data)
    legacy = ComparisonArtifact.model_validate_json(json.dumps(artifact_payload))
    # Retain actual fixture source points only; leave a 1.2-second native interval.
    for view in data["laps"].values():
        view["elapsed_ms"] = [view["elapsed_ms"][0], view["elapsed_ms"][-1]]
        for key in view["channels"]:
            view["channels"][key] = [view["channels"][key][0], view["channels"][key][-1]]
            view["sample_masks"][key] = ["measured", "measured"]
    result = build_view(data, "test-A", "test-B", "analysis", legacy)
    assert result.view_tier == "aligned_delta"
    assert result.legacy_analysis is None
    assert result.alignment.lap_a.bridges


def test_view_build_capacity_is_bounded_and_released_on_failure(tmp_path):
    import pytest
    from lapdna.analysis.store import ComparisonBusy
    from lapdna.analysis.view_store import ViewStore
    from lapdna.inventory import SelectionError
    from lapdna.view_models import ViewCompareRequest
    store = ViewStore(tmp_path)
    request = ViewCompareRequest(session_id="missing", lap_a_id="a", lap_b_id="b")
    assert store.capacity.acquire(blocking=False)
    assert store.capacity.acquire(blocking=False)
    with pytest.raises(ComparisonBusy):
        store.compare(request)
    store.capacity.release()
    store.capacity.release()
    with pytest.raises(SelectionError):
        store.compare(request)
    assert store.capacity.acquire(blocking=False)
    assert store.capacity.acquire(blocking=False)
