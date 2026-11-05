"""Selection uses the imported roster, phase and capability before reading a pair."""

import json

from fastapi.testclient import TestClient

from lapdna.main import create_app


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def setup_client(tmp_path, index=None, artifact=None):
    session_dir = tmp_path / "sessions"
    artifact_dir = tmp_path / "artifacts"
    if index:
        write_json(session_dir / f"{index['session']['session_id']}.json", index)
    if artifact:
        write_json(artifact_dir / f"{artifact['comparison_id']}.json", artifact)
    return TestClient(create_app(artifact_dir, session_dir))


def request(index):
    return {
        "session_id": index["session"]["session_id"],
        "lap_a_id": index["laps"][0]["lap_id"],
        "lap_b_id": index["laps"][1]["lap_id"],
    }


def sector_only(payload):
    result = {key: payload[key] for key in ("schema_version", "comparison_id", "session", "lap_a", "lap_b", "pairing")}
    result.update(
        detail_level="sector_only", fallback_reason="Synthetic missing native car data.",
        quality={"status": "warn", "warnings": ["Sector times only."],
                 "checks": [item for item in payload["quality"]["checks"] if item["metric"] == "sector_sum"]},
        sector_delta_ms=[25.0, 50.0, 25.0], cumulative_delta_ms=[25.0, 75.0, 100.0],
        provenance={key: value for key, value in payload["provenance"].items()
                    if key not in ("reference_sha256", "reference_lap_id", "circuit_revision")},
    )
    return result


def test_empty_inventory_and_unimported_session(tmp_path, index_payload):
    client = setup_client(tmp_path)
    assert client.get("/api/v1/sessions").json()["sessions"] == []
    assert client.get("/api/v1/sessions/missing/laps").status_code == 404
    response = client.post("/api/v1/compare", json=request(index_payload))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "data_not_imported"


def test_roster_includes_driver_without_lap_and_unprepared_pair(tmp_path, index_payload):
    index_payload["drivers"].append({"driver_number": "903", "driver_name": "Synthetic C", "driver_code": "TSC"})
    client = setup_client(tmp_path, index_payload)
    assert client.get("/api/v1/sessions").json()["sessions"][0]["driver_count"] == 3
    assert client.get("/api/v1/sessions/synthetic-session/laps").json()["drivers"] == index_payload["drivers"]
    response = client.post("/api/v1/compare", json=request(index_payload))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "comparison_not_prepared"


def test_reversed_request_preserves_canonical_dataset(tmp_path, index_payload, artifact_payload):
    client = setup_client(tmp_path, index_payload, artifact_payload)
    body = request(index_payload)
    body["lap_a_id"], body["lap_b_id"] = body["lap_b_id"], body["lap_a_id"]
    result = client.post("/api/v1/compare", json=body)
    assert result.status_code == 200
    assert result.json()["swapped"] is True
    assert result.json()["artifact"]["delta_ms"][-1] == 100.0


def test_cross_phase_requires_explicit_choice_on_cache_hit(tmp_path, index_payload, artifact_payload):
    index_payload["laps"][0]["phase"] = artifact_payload["lap_a"]["phase"] = "Q1"
    artifact_payload["pairing"] = {"mode": "cross_phase", "warnings": ["Q1 and Q3 conditions may differ."]}
    client = setup_client(tmp_path, index_payload, artifact_payload)
    body = request(index_payload)
    response = client.post("/api/v1/compare", json=body)
    assert response.status_code == 422 and response.json()["error"]["code"] == "cross_phase_not_enabled"
    result = client.post("/api/v1/compare", json={**body, "allow_cross_phase": True}).json()
    assert result["artifact"]["pairing"]["mode"] == "cross_phase"


def test_stale_snapshot_is_ignored(tmp_path, index_payload, artifact_payload):
    index_payload["source_snapshot_sha256"] = "2" * 64
    client = setup_client(tmp_path, index_payload, artifact_payload)
    assert client.post("/api/v1/compare", json=request(index_payload)).json()["error"]["code"] == "comparison_not_prepared"


def test_corrupt_cached_lap_identity_fails_visibly(tmp_path, index_payload, artifact_payload):
    artifact_payload["lap_b"]["driver_number"] = "913"
    client = setup_client(tmp_path, index_payload, artifact_payload)
    assert client.post("/api/v1/compare", json=request(index_payload)).status_code == 503


def test_ineligible_lap_cannot_use_cached_artifact(tmp_path, index_payload, artifact_payload):
    index_payload["laps"][1].update(capability="unavailable", reasons=["Deleted lap."])
    client = setup_client(tmp_path, index_payload, artifact_payload)
    assert client.post("/api/v1/compare", json=request(index_payload)).json()["error"]["code"] == "lap_unavailable"


def test_sector_only_result_has_no_spatial_invention(tmp_path, index_payload, artifact_payload):
    index_payload["laps"][1].update(capability="sector_only", reasons=["Missing telemetry."])
    artifact = sector_only(artifact_payload)
    client = setup_client(tmp_path, index_payload, artifact)
    body = request(index_payload)
    response = client.post("/api/v1/compare", json=body)
    assert response.status_code == 200
    result = response.json()["artifact"]
    assert result["detail_level"] == "sector_only"
    assert result["cumulative_delta_ms"] == [25.0, 75.0, 100.0]
    assert "distance_m" not in result and "corners" not in result and "analysis" not in result
    unavailable = client.post("/api/v1/compare", json={**body, "detail_level": "telemetry"})
    assert unavailable.json()["error"]["code"] == "telemetry_unavailable"


def test_sector_only_rejects_false_cumulative_delta_and_turn_coordinates(tmp_path, index_payload, artifact_payload):
    for key, value in (("cumulative_delta_ms", [25.0, 50.0, 100.0]), ("corners", [])):
        fixture = sector_only(artifact_payload)
        fixture[key] = value
        client = setup_client(tmp_path, index_payload, fixture)
        assert client.get(f"/api/v1/comparisons/{fixture['comparison_id']}").status_code == 503


def test_sector_only_reconciles_each_recorded_lap(tmp_path, index_payload, artifact_payload):
    fixture = sector_only(artifact_payload)
    fixture["lap_b"]["sector_times_ms"][2] += 25
    fixture["sector_delta_ms"][2] += 25
    fixture["cumulative_delta_ms"][2] += 25
    client = setup_client(tmp_path, index_payload, fixture)
    assert client.get(f"/api/v1/comparisons/{fixture['comparison_id']}").status_code == 503
