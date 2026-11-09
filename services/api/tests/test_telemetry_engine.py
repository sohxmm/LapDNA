"""Analytical pair examples and bounded serving behavior; no live network/data."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import gzip
import json
from threading import Event

import pytest
from fastapi.testclient import TestClient

from lapdna.analysis.engine import ComparisonUnavailable, build_comparison, quality, summaries
from lapdna.analysis.store import PilotStore
from lapdna.inventory import CompareRequest, SessionLapIndex, SessionStore
from lapdna.main import create_app
from lapdna.store import ArtifactNotFound, ArtifactStore, InvalidArtifact


@pytest.fixture
def publication(artifact_payload):
    fixture = deepcopy(artifact_payload)
    metrics = {"test-segment": {field: {"count": 3, "span_ms": 500., "minimum": 1., "maximum": 3.,
                                        "onset": None, "pickup": None} for field in ("speed", "brake", "throttle")}}
    provenance = {**fixture["provenance"], "source": "openf1_tracinginsights", "fastf1_version": None,
                  "provider_version": "SYNTHETIC analytic fixture", "source_retrieved_at": "2024-01-01T00:00:00Z",
                  "source_urls": ["https://example.invalid/synthetic"], "verification_scope": "Artificial test only",
                  "components": [{"source": source, "version": "test", "url": "https://example.invalid/test",
                                  "sha256": "0" * 64, "retrieved_at": "2024-01-01T00:00:00Z"}
                                 for source in ("openf1", "tracinginsights")]}
    return {"publication_sha256": "2" * 64, "session": fixture["session"], "provenance": provenance,
            "distance_m": fixture["distance_m"], "geometry": fixture["geometry"],
            "sector_boundaries_m": fixture["sector_boundaries_m"], "reference_lap_id": "test-A", "reference_sha256": "0" * 64,
            "regions": [{key: value for key, value in fixture["segments"][0].items() if key in (
                "segment_id", "kind", "label", "speed_class", "start_m", "end_m")}], "corners": [],
            "laps": {lap["lap_id"]: {"metadata": lap, "channels": fixture[f"channels_{slot}"],
                     "metrics": deepcopy(metrics), "integrated_length_m": 2., "scale_factor": 1.,
                     "native_count": 3, "max_native_gap_ms": 500.}
                     for lap, slot in ((fixture["lap_a"], "a"), (fixture["lap_b"], "b"))}}


def write_bundle(tmp_path, publication):
    path = tmp_path / "normalized" / f"{publication['session']['session_id']}.json.gz"
    path.parent.mkdir(parents=True)
    compressed = gzip.compress(json.dumps(publication).encode())
    path.write_bytes(compressed)
    (tmp_path / "publication.json").write_text(json.dumps({
        "session_id": publication["session"]["session_id"], "publication_sha256": publication["publication_sha256"],
        "files": {str(path.relative_to(tmp_path)).replace("\\", "/"): sha256(compressed).hexdigest()},
    }))
    return path


def test_analytical_pair_keeps_raw_elapsed_and_separate_accounting(publication):
    original = deepcopy(publication)
    result = build_comparison(publication, "test-A", "test-B")
    assert result.detail_level == "telemetry"
    assert result.delta_ms == [0., 50., 100.]
    assert sum(segment.gain_ms for segment in result.segments) == pytest.approx(100.)
    assert sum(bin.gain_ms for bin in result.estimated_minisectors) == pytest.approx(100.)
    gain = next(item for item in result.evidence if item.metric == "segment_gain")
    assert (gain.value_a, gain.value_b, gain.difference_b_minus_a) == (1000., 1100., 100.)
    assert result.observations == []
    assert result.insufficient_evidence_reason
    assert publication == original


def test_reverse_order_reuses_canonical_reference_and_artifact(publication):
    forward = build_comparison(publication, "test-A", "test-B")
    reverse = build_comparison(publication, "test-B", "test-A")
    assert reverse.model_dump() == forward.model_dump()


def test_perturbed_official_sector_does_not_repair_curve(publication):
    raw = deepcopy(publication["laps"]["test-A"]["channels"])
    publication["laps"]["test-A"]["metadata"]["sector_times_ms"] = [450., 300., 250.]
    with pytest.raises(ComparisonUnavailable, match="raw interior"):
        build_comparison(publication, "test-A", "test-B", "telemetry")
    fallback = build_comparison(publication, "test-A", "test-B")
    assert fallback.detail_level == "sector_only"
    assert "distance_m" not in fallback.model_dump()
    assert publication["laps"]["test-A"]["channels"] == raw


def test_individual_errors_cannot_cancel_into_pair_pass(publication):
    publication["laps"]["test-A"]["metadata"]["sector_times_ms"] = [450., 300., 250.]
    publication["laps"]["test-B"]["metadata"]["sector_times_ms"] = [475., 350., 275.]
    report = quality(publication, publication["laps"]["test-A"], publication["laps"]["test-B"])
    assert report["status"] == "block"
    assert any(item["driver"] == "A" and item["status"] == "block" for item in report["checks"])
    assert all(item["status"] == "pass" for item in report["checks"] if item["driver"] == "pair")


def test_explicit_telemetry_never_silently_downgrades(publication):
    publication["laps"]["test-B"].pop("channels")
    with pytest.raises(ComparisonUnavailable, match="lack a verified"):
        build_comparison(publication, "test-A", "test-B", "telemetry")
    assert build_comparison(publication, "test-A", "test-B").detail_level == "sector_only"


def test_timing_integrity_failure_blocks_both_tiers(publication):
    publication["laps"]["test-A"]["metadata"]["lap_time_ms"] += 25.
    for mode in ("sector_only", "auto"):
        with pytest.raises(ComparisonUnavailable, match="does not reconcile"):
            build_comparison(publication, "test-A", "test-B", mode)


def test_missing_optional_brake_remains_null(publication):
    publication["laps"]["test-A"]["channels"]["brake"] = [None, None, None]
    result = build_comparison(publication, "test-A", "test-B")
    assert result.channel_provenance_a.brake.status == "missing"
    assert result.channels_a.brake == [None, None, None]
    assert result.channel_provenance_b.brake.status == "measured"


def test_selected_sector_mode_describes_choice_honestly(publication):
    result = build_comparison(publication, "test-A", "test-B", "sector_only")
    assert "selected" in result.fallback_reason
    assert "lack" not in result.fallback_reason


def test_cache_restart_and_exact_id_resolution_use_local_publication(tmp_path, publication):
    write_bundle(tmp_path, publication)
    first = PilotStore(tmp_path).compare(publication["session"]["session_id"], "test-A", "test-B", "auto")
    restarted = PilotStore(tmp_path)
    assert restarted.resolve(first.comparison_id).model_dump() == first.model_dump()
    with pytest.raises(ArtifactNotFound):
        restarted.resolve("cmp_" + "f" * 24)


def test_corrupt_compressed_publication_is_rejected(tmp_path, publication):
    path = write_bundle(tmp_path, publication)
    path.write_bytes(path.read_bytes() + b"corrupt")
    with pytest.raises(InvalidArtifact, match="digest"):
        PilotStore(tmp_path).load(publication["session"]["session_id"])


def test_identical_concurrent_builds_share_one_result(tmp_path, publication, monkeypatch):
    import lapdna.analysis.store as module
    write_bundle(tmp_path, publication)
    engine = PilotStore(tmp_path)
    entered, release = Event(), Event()
    actual, calls = module.build_comparison, []
    def building(*args):
        calls.append(args)
        entered.set()
        assert release.wait(2)
        return actual(*args)
    monkeypatch.setattr(module, "build_comparison", building)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(engine.compare, publication["session"]["session_id"], "test-A", "test-B", "auto") for _ in range(3)]
        assert entered.wait(2)
        release.set()
        assert len({future.result().comparison_id for future in futures}) == 1
    assert len(calls) == 1


def test_computation_validation_error_is_not_exposed(tmp_path, index_payload):
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    session_id = index_payload["session"]["session_id"]
    (session_dir / f"{session_id}.json").write_text(json.dumps(index_payload))
    class Broken:
        def compare(self, *_args):
            raise ValueError("private internal dataset values must not appear in the response")
    sessions = SessionStore(session_dir, engine=Broken())
    request = CompareRequest(session_id=session_id, lap_a_id="test-A", lap_b_id="test-B")
    with pytest.raises(InvalidArtifact) as error:
        sessions.compare(request, ArtifactStore(tmp_path / "artifacts"))
    assert "private internal" not in str(error.value)


@pytest.mark.parametrize("change", ["too_many", "nonmonotone", "channel_length"])
def test_publication_bounds_are_checked_before_computation(tmp_path, publication, change):
    if change == "too_many":
        publication["distance_m"] = list(range(5001))
    elif change == "nonmonotone":
        publication["distance_m"] = [0., 2., 1.]
    else:
        publication["laps"]["test-A"]["channels"]["gear"] = [1]
    write_bundle(tmp_path, publication)
    with pytest.raises(InvalidArtifact):
        PilotStore(tmp_path).load(publication["session"]["session_id"])


def test_negligible_class_net_does_not_name_a_driver_advantage(publication):
    region = publication["regions"][0]
    region.update(kind="corner", speed_class="low")
    for record in publication["laps"].values():
        record["metrics"]["test-segment"]["speed"].update(count=10, span_ms=250.)
    analysis = summaries(publication, publication["laps"]["test-A"], publication["laps"]["test-B"], [0., .5, 1.])[3]
    assert "negligible estimated net" in analysis["text"]
    assert "TSA net" not in analysis["text"]
    assert "advantage" not in analysis["text"]


def test_event_team_colours_survive_comparison_and_reversal(publication):
    publication["laps"]["test-A"]["metadata"].update(team_name="McLaren", team_colour="#FF8000")
    publication["laps"]["test-B"]["metadata"].update(team_name="Mercedes", team_colour="#27F4D2")
    result = build_comparison(publication, "test-A", "test-B")
    assert result.lap_a.team_colour == "#FF8000"
    assert result.lap_b.team_colour == "#27F4D2"
    assert build_comparison(publication, "test-B", "test-A").model_dump() == result.model_dump()


def test_catalogue_loads_two_sessions_and_resolves_only_matching_session(tmp_path, publication):
    from lapdna.analysis.engine import comparison_identity
    write_bundle(tmp_path, publication)
    first = json.loads((tmp_path / "publication.json").read_text())
    other = deepcopy(publication)
    other["session"]["session_id"] = "2024-4-suzuka-Q"
    other["session"]["circuit_id"] = "suzuka"
    other["publication_sha256"] = "3" * 64
    folder = tmp_path / "second"
    folder.mkdir()
    second_path = write_bundle(folder, other)
    target = tmp_path / "normalized" / second_path.name
    target.write_bytes(second_path.read_bytes())
    second = json.loads((folder / "publication.json").read_text())
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    catalogue = {"catalogue_version": 2, "sessions": {}}
    for manifest in (first, second):
        filename = manifest["session_id"] + ".json"
        raw = json.dumps(manifest).encode()
        (manifests / filename).write_bytes(raw)
        catalogue["sessions"][manifest["session_id"]] = {"manifest": "manifests/" + filename, "sha256": sha256(raw).hexdigest()}
    (tmp_path / "publication.json").write_text(json.dumps(catalogue))
    store = PilotStore(tmp_path)
    assert store.load(publication["session"]["session_id"])["publication_sha256"] == "2" * 64
    assert store.load(other["session"]["session_id"])["publication_sha256"] == "3" * 64
    identifier = comparison_identity(other, "test-A", "test-B", "telemetry")
    restarted = PilotStore(tmp_path)
    assert restarted.resolve(identifier).session.circuit_id == "suzuka"
    assert list(restarted._publications) == [other["session"]["session_id"]]
    entry = next(iter(catalogue["sessions"].values()))
    entry["sha256"] = "0" * 64
    (tmp_path / "publication.json").write_text(json.dumps(catalogue))
    with pytest.raises(InvalidArtifact, match="digest"):
        PilotStore(tmp_path).load(publication["session"]["session_id"])


def test_primary_fastf1_provenance_does_not_claim_composite_sources(publication):
    publication["method"] = "distance-v5-fastf1-native"
    publication["provenance"].update(source="fastf1", fastf1_version="3.9.2", provider_version="FastF1 3.9.2 raw native")
    result = build_comparison(publication, "test-A", "test-B")
    assert result.provenance.source == "fastf1"
    assert result.provenance.methodology_version == "distance-v5-fastf1-native"
    assert result.channel_provenance_a.speed_kph.source_channel == "Speed"
    assert result.channel_provenance_a.brake.source_channel == "Brake"
    assert all("from OpenF1" not in text and "identity-matched TracingInsights" not in text for text in result.quality.warnings)


def test_wet_pairing_preserves_native_channels_and_reports_unknown_conditions(publication):
    original = deepcopy(publication["laps"]["test-A"]["channels"])
    publication["laps"]["test-A"]["metadata"]["compound"] = "INTERMEDIATE"
    publication["laps"]["test-B"]["metadata"]["compound"] = "WET"
    publication["laps"]["test-A"]["weather_context"] = "rain_reported"
    publication["laps"]["test-B"]["weather_context"] = "unknown"
    result = build_comparison(publication, "test-A", "test-B")
    assert result.detail_level == "telemetry"
    assert any("wet-weather tyres" in warning for warning in result.pairing.warnings)
    assert any("rainfall within 90 seconds" in warning for warning in result.pairing.warnings)
    assert any("unavailable" in warning for warning in result.pairing.warnings)
    assert result.channels_a.model_dump() == original
