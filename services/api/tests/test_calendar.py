"""Calendar tests use artificial metadata and never require source access."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from lapdna.calendar import (
    MAX_CACHED_YEARS, CalendarService, CalendarUnavailable, client_year, normalize,
)
from lapdna.main import create_app

NOW = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)


def source(year=2026):
    return {"MRData": {"total": "1", "RaceTable": {"season": str(year), "Races": [{
        "season": str(year), "round": "1", "raceName": "Artificial Calendar Grand Prix",
        "date": f"{year}-11-08", "time": "15:00:00Z",
        "Qualifying": {"date": f"{year}-11-07", "time": "14:00:00Z"},
        "Circuit": {"circuitId": "test-circuit", "circuitName": "Test circuit", "Location": {
            "country": "Test Country", "locality": "Test locality",
        }},
    }]}}}


def unavailable(_year):
    raise OSError("provider secret/path must not escape")


def test_normalizes_actual_date_fields_without_inferring_completion():
    value = normalize(source(), 2026, NOW)
    event = value.races[0]
    assert event.race_id == "2026-1"
    assert event.qualifying_status == "upcoming"
    assert event.qualifying_start_at.isoformat() == "2026-11-07T14:00:00+00:00"
    service = CalendarService(fetch=source, now=lambda: NOW + timedelta(days=2))
    assert service.get(2026).races[0].qualifying_status == "start_time_passed"


def test_absent_or_date_only_qualifying_timestamp_stays_unknown():
    data = source()
    row = data["MRData"]["RaceTable"]["Races"][0]
    row["Qualifying"].pop("time")
    event = normalize(data, 2026, NOW).races[0]
    assert str(event.qualifying_date) == "2026-11-07"
    assert event.qualifying_start_at is None
    assert event.qualifying_status == "time_unknown"
    row.pop("Qualifying")
    assert normalize(data, 2026, NOW).races[0].qualifying_date is None


def test_rejects_partial_or_wrong_year_source():
    data = source()
    data["MRData"]["total"] = "2"
    with pytest.raises(ValueError, match="incomplete"):
        normalize(data, 2026, NOW)
    with pytest.raises(ValueError, match="different season"):
        normalize(source(2024), 2026, NOW)


def test_cache_reuses_source_but_updates_scheduled_start_status(tmp_path):
    clock = [datetime(2026, 11, 7, 13, tzinfo=timezone.utc)]
    calls = []
    def fetch(year):
        calls.append(year)
        return source(year)
    service = CalendarService(fetch=fetch, now=lambda: clock[0], snapshot_dir=tmp_path)
    assert service.get(2026).races[0].qualifying_status == "upcoming"
    clock[0] += timedelta(hours=2)
    result = service.get(2026)
    assert result.races[0].qualifying_status == "start_time_passed"
    assert result.retrieved_at == datetime(2026, 11, 7, 13, tzinfo=timezone.utc)
    assert calls == [2026]


def test_cache_has_bounded_number_of_years(tmp_path):
    service = CalendarService(fetch=source, now=lambda: NOW, snapshot_dir=tmp_path)
    for year in range(1950, 1950 + MAX_CACHED_YEARS + 2):
        service.get(year)
    assert len(service.cache) == MAX_CACHED_YEARS
    assert 1950 not in service.cache


def test_snapshot_fallback_is_marked_stale_and_preserves_retrieval(tmp_path):
    old = NOW - timedelta(days=3)
    (tmp_path / "2026.json").write_text(normalize(source(), 2026, old).model_dump_json(), encoding="utf-8")
    result = CalendarService(fetch=unavailable, now=lambda: NOW, snapshot_dir=tmp_path).get(2026)
    assert result.stale is True
    assert result.retrieved_at == old
    assert result.source == "jolpica" and "last saved" in result.warnings[0]


def test_recent_bundled_calendar_uses_the_same_freshness_window_without_a_network_call(tmp_path):
    stamp = NOW - timedelta(hours=1)
    (tmp_path / "2026.json").write_text(normalize(source(), 2026, stamp).model_dump_json(), encoding="utf-8")
    calls = []
    def fail(year):
        calls.append(year)
        raise OSError("unavailable")
    service = CalendarService(fetch=fail, now=lambda: NOW, snapshot_dir=tmp_path)
    result = service.get(2026)
    assert result.retrieved_at == stamp
    assert not result.stale and calls == []


def test_old_warm_cache_can_be_used_after_source_failure(tmp_path):
    clock = [NOW]
    service = CalendarService(fetch=source, now=lambda: clock[0], snapshot_dir=tmp_path)
    original = service.get(2026)
    clock[0] += timedelta(hours=7)
    service.fetch = unavailable
    result = service.get(2026)
    assert result.stale and result.races == original.races
    assert result.retrieved_at == original.retrieved_at


def test_source_failure_without_snapshot_is_honest_503(tmp_path):
    service = CalendarService(fetch=unavailable, now=lambda: NOW, snapshot_dir=tmp_path)
    with pytest.raises(CalendarUnavailable):
        service.get(2026)
    client = TestClient(create_app(tmp_path / "artifacts", tmp_path / "sessions", calendar_service=service))
    response = client.get("/api/v1/calendar/2026")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "calendar_unavailable"
    assert "secret" not in response.text


def test_year_validation_and_season_list_use_client_timezone(tmp_path):
    boundary = datetime(2025, 12, 31, 20, tzinfo=timezone.utc)
    assert client_year(boundary) == 2026
    service = CalendarService(fetch=source, now=lambda: boundary, snapshot_dir=tmp_path)
    client = TestClient(create_app(tmp_path / "artifacts", tmp_path / "sessions", calendar_service=service))
    seasons = client.get("/api/v1/seasons").json()
    assert seasons["current_year"] == 2026
    assert seasons["years"][0] == 2026 and seasons["years"][-1] == 1950
    for year in (1949, 2027):
        assert client.get(f"/api/v1/calendar/{year}").status_code == 422


def test_calendar_route_returns_normalized_not_raw_source(tmp_path):
    service = CalendarService(fetch=source, now=lambda: NOW, snapshot_dir=tmp_path)
    client = TestClient(create_app(tmp_path / "artifacts", tmp_path / "sessions", calendar_service=service))
    value = client.get("/api/v1/calendar/2026").json()
    assert value["schema_version"] == "1.0.0"
    assert value["races"][0]["name"] == "Artificial Calendar Grand Prix"
    assert value["source_url"].endswith("2026/races.json?limit=100")
    assert "MRData" not in value


def test_malformed_or_mismatched_snapshot_cannot_masquerade_as_data(tmp_path):
    (tmp_path / "2026.json").write_text("{", encoding="utf-8")
    service = CalendarService(fetch=unavailable, now=lambda: NOW, snapshot_dir=tmp_path)
    with pytest.raises(CalendarUnavailable):
        service.get(2026)
    (tmp_path / "2026.json").write_text(normalize(source(2024), 2024, NOW).model_dump_json(), encoding="utf-8")
    with pytest.raises(CalendarUnavailable):
        service.get(2026)


def test_source_outage_backoff_prevents_repeated_upstream_requests(tmp_path):
    calls = []
    clock = [NOW]
    def fail(year):
        calls.append(year)
        raise OSError("unavailable")
    service = CalendarService(fetch=fail, now=lambda: clock[0], snapshot_dir=tmp_path)
    for _ in range(2):
        with pytest.raises(CalendarUnavailable):
            service.get(2026)
    assert calls == [2026]
    clock[0] += timedelta(minutes=2)
    with pytest.raises(CalendarUnavailable):
        service.get(2026)
    assert calls == [2026, 2026]
