import gzip
from hashlib import sha256
import json

from fastapi.testclient import TestClient

from lapdna.alignment.view import CarStream
from lapdna.analysis.engine import canonical_hash
from lapdna.main import create_app
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
