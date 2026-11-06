import json

from fastapi.testclient import TestClient

from lapdna.main import create_app
from lapdna.store import ArtifactNotFound, ArtifactStore


def test_health_and_missing_artifact_directory(tmp_path):
    client = TestClient(create_app(tmp_path / "missing"))
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert client.get("/api/v1/catalog").json() == {
        "schema_version": "1.2.0", "comparisons": [],
    }


def test_validated_artifact_and_catalog(tmp_path, artifact_payload):
    identifier = artifact_payload["comparison_id"]
    (tmp_path / f"{identifier}.json").write_text(json.dumps(artifact_payload), encoding="utf-8")
    client = TestClient(create_app(tmp_path))
    response = client.get(f"/api/v1/comparisons/{identifier}")
    assert response.status_code == 200
    assert response.json()["delta_ms"] == [0.0, 50.0, 100.0]
    summary = client.get("/api/v1/catalog").json()["comparisons"][0]
    assert summary["comparison_id"] == identifier
    assert "channels_a" not in summary


def test_corrupt_artifact_is_not_silently_an_empty_catalog(tmp_path):
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    client = TestClient(create_app(tmp_path))
    for endpoint in ("/api/v1/catalog", "/api/v1/comparisons/broken"):
        response = client.get(endpoint)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "artifact_invalid"
        assert str(tmp_path) not in response.text


def test_missing_and_invalid_identifiers(tmp_path):
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/v1/comparisons/missing").status_code == 404
    assert client.get("/api/v1/comparisons/invalid.id").status_code == 422
    store = ArtifactStore(tmp_path)
    try:
        store.load("../secret")
    except ArtifactNotFound:
        pass
    else:
        raise AssertionError("A path traversal must not be accepted")


def test_filename_identity_must_match(tmp_path, artifact_payload):
    (tmp_path / "different.json").write_text(json.dumps(artifact_payload), encoding="utf-8")
    response = TestClient(create_app(tmp_path)).get("/api/v1/comparisons/different")
    assert response.status_code == 503


def test_quality_blocked_artifact_is_withheld(tmp_path, artifact_payload):
    artifact_payload["quality"]["status"] = "block"
    identifier = artifact_payload["comparison_id"]
    (tmp_path / f"{identifier}.json").write_text(json.dumps(artifact_payload), encoding="utf-8")
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/v1/catalog").json()["comparisons"] == []
    response = client.get(f"/api/v1/comparisons/{identifier}")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "quality_blocked"


def test_cors_is_limited_to_configured_local_origins(tmp_path):
    client = TestClient(create_app(tmp_path))
    local = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    external = client.get("/api/v1/health", headers={"Origin": "https://unrelated.example"})
    assert local.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in external.headers
