"""Offline tests for recorded session classifications and publication boundaries."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from lapdna.classifications import (
    ClassificationCoverage, ClassificationEvent, ClassificationSeason, ClassificationStore,
    CoverageSeason, normalize_jolpica_race, normalize_openf1_session, parse_classification_time,
)
from lapdna.main import create_app

STAMP = datetime(2026, 11, 7, 0, tzinfo=timezone.utc)


def race(year=2024):
    return {
        "season": str(year), "round": "16", "raceName": "Artificial Grand Prix",
        "Circuit": {"circuitId": "artificial"},
        "QualifyingResults": [
            {"number": "7", "position": "1", "Driver": {
                "driverId": "test_one", "givenName": "Test", "familyName": "One", "code": "ONE",
            }, "Constructor": {"constructorId": "historical_team", "name": "Event Team"},
             "Q1": "1:15.100", "Q2": "1:14.000", "Q3": "1:14.500"},
            {"number": "8", "position": "2", "Driver": {
                "driverId": "test_two", "givenName": "Test", "familyName": "Two",
            }, "Constructor": {"constructorId": "other_team", "name": "Other Event Team"},
             "Q1": "1:16.100", "Q2": "1:15.000"},
            {"number": "9", "position": "3", "Driver": {
                "driverId": "test_three", "givenName": "Test", "familyName": "Three",
            }, "Constructor": {"constructorId": "third_team", "name": "Third Event Team"}},
        ],
    }


def open_session():
    return {"year": 2024, "session_key": 123, "session_name": "Sprint Qualifying"}


def roster():
    return [
        {"session_key": 123, "driver_number": 7, "name_acronym": "ONE",
         "full_name": "Test One", "team_name": "Actual Sprint Team"},
        {"session_key": 123, "driver_number": 8, "name_acronym": "TWO",
         "full_name": "Test Two", "team_name": "Another Sprint Team"},
    ]


def results():
    return [{"session_key": 123, "driver_number": 7, "position": 1,
             "duration": [75.123, 74.001, 74.200]},
            {"session_key": 123, "driver_number": 8, "position": 2,
             "duration": [76.123, None, None]}]


def normalize_open(rows=None, drivers=None, session=None):
    return normalize_openf1_session(session or open_session(), rows if rows is not None else results(),
        drivers if drivers is not None else roster(), STAMP, year=2024, round=5)


@pytest.mark.parametrize("value,expected", [
    ("1:16.514", 76514), ("2:03.01", 123010), ("59.999", 59999), ("53.904", 53904),
    (None, None), ("", None), ("DNS", None), ("No Time", None), ("-", None),
])
def test_clock_parser_preserves_milliseconds_and_no_time(value, expected):
    assert parse_classification_time(value) == expected


@pytest.mark.parametrize("value", ["0:00.000", "1:60.123", "NaN", "Infinity", "-1:15.123", "1:15.1234", "31:00.000", 75, True])
def test_clock_parser_rejects_malformed_or_nonpositive_values(value):
    with pytest.raises(ValueError):
        parse_classification_time(value)


def test_latest_recorded_phase_is_not_the_fastest_across_phases():
    session = normalize_jolpica_race(race(), STAMP).sessions[0]
    driver = session.drivers[0]
    assert driver.phase_times_ms == {"Q1": 75100, "Q2": 74000, "Q3": 74500}
    assert (driver.latest_timed_phase, driver.latest_time_ms) == ("Q3", 74500)
    assert session.drivers[1].phase_times_ms["Q3"] is None
    assert session.drivers[1].latest_timed_phase == "Q2"
    assert session.drivers[2].status == "no_time" and session.drivers[2].reason


def test_event_team_and_driver_identity_are_not_current_roster_defaults():
    original = normalize_jolpica_race(race(), STAMP)
    changed = race(2025)
    changed["QualifyingResults"][0]["Constructor"] = {"constructorId": "new_team", "name": "New Event Team"}
    later = normalize_jolpica_race(changed, STAMP)
    assert original.sessions[0].drivers[0].team_name == "Event Team"
    assert later.sessions[0].drivers[0].team_name == "New Event Team"
    assert original.sessions[0].drivers[0].driver_id == later.sessions[0].drivers[0].driver_id


def test_pre_knockout_time_is_not_mislabelled_modern_q1():
    data = race(1994)
    for driver in data["QualifyingResults"]:
        driver.pop("Q2", None)
        driver.pop("Q3", None)
    value = normalize_jolpica_race(data, STAMP).sessions[0]
    assert value.phases == ["QUALIFYING"]
    assert value.drivers[0].phase_times_ms == {"QUALIFYING": 75100}
    assert value.warnings


def test_historical_two_component_qualifying_preserves_both_without_fabricating_aggregate():
    data = race(2005)
    data["QualifyingResults"][0].pop("Q3")
    value = normalize_jolpica_race(data, STAMP).sessions[0]
    assert value.phases == ["QUALIFYING_1", "QUALIFYING_2"]
    assert value.drivers[0].phase_times_ms == {"QUALIFYING_1": 75100, "QUALIFYING_2": 74000}
    assert value.drivers[0].latest_time_ms == 74000
    assert value.drivers[0].position == 1
    assert "not an aggregate" in value.warnings[-1]


def test_unrecognized_legacy_third_component_cannot_be_silently_discarded():
    with pytest.raises(ValueError, match="unexpected third"):
        normalize_jolpica_race(race(2005), STAMP)


def test_f1db_legacy_components_and_reported_overall_time_are_preserved_separately():
    payload = normalize_jolpica_race(race(), STAMP).model_dump()
    session = payload["sessions"][0]
    session["source"] = "f1db"
    session["source_url"] = "https://github.com/f1db/f1db/releases/tag/v2026.19.0"
    session["phases"] = ["QUALIFYING_1", "QUALIFYING_2", "QUALIFYING"]
    session["drivers"] = [session["drivers"][0]]
    driver = session["drivers"][0]
    driver["phase_times_ms"] = {"QUALIFYING_1": 75100, "QUALIFYING_2": 74000, "QUALIFYING": 149100}
    driver["latest_timed_phase"] = "QUALIFYING"
    driver["latest_time_ms"] = 149100
    event = ClassificationEvent.model_validate(payload)
    assert event.sessions[0].drivers[0].phase_times_ms == driver["phase_times_ms"]
    assert event.sessions[0].drivers[0].latest_time_ms == 149100
    for source in ("jolpica", "openf1"):
        session["source"] = source
        with pytest.raises(ValidationError, match="actual session format"):
            ClassificationEvent.model_validate(payload)


def test_duplicate_provider_positions_are_preserved_but_duplicate_drivers_rejected():
    value = race()
    value["QualifyingResults"][1]["position"] = "1"
    assert [d.position for d in normalize_jolpica_race(value, STAMP).sessions[0].drivers][:2] == [1, 1]
    value["QualifyingResults"].append(deepcopy(value["QualifyingResults"][0]))
    with pytest.raises(ValidationError, match="identities"):
        normalize_jolpica_race(value, STAMP)


def test_session_rejects_invented_minimum_as_latest_or_inconsistent_phase_keys():
    payload = normalize_jolpica_race(race(), STAMP).model_dump()
    payload["sessions"][0]["drivers"][0]["latest_time_ms"] = 74000
    with pytest.raises(ValidationError, match="last timed phase"):
        ClassificationEvent.model_validate(payload)
    payload = normalize_jolpica_race(race(), STAMP).model_dump()
    payload["sessions"][0]["drivers"][1]["phase_times_ms"].pop("Q3")
    with pytest.raises(ValidationError, match="every declared phase"):
        ClassificationEvent.model_validate(payload)


def test_sprint_duration_arrays_are_exact_phase_bests_with_session_specific_roster():
    value = normalize_open()
    assert value.session_type == "sprint_qualifying" and value.phases == ["SQ1", "SQ2", "SQ3"]
    assert value.drivers[0].phase_times_ms == {"SQ1": 75123, "SQ2": 74001, "SQ3": 74200}
    assert value.drivers[0].latest_time_ms == 74200
    assert value.drivers[0].team_name == "Actual Sprint Team"
    assert value.source == "openf1"


def test_missing_sprint_result_keeps_roster_driver_and_partial_status():
    value = normalize_open(rows=results()[:1])
    assert value.status == "partial" and len(value.drivers) == 2
    missing = next(row for row in value.drivers if row.driver_number == "8")
    assert missing.phase_times_ms == {"SQ1": None, "SQ2": None, "SQ3": None}
    assert missing.status == "no_time" and "no source classification" in missing.reason


@pytest.mark.parametrize("flag,status", [("is_dsq", "disqualified"), ("is_dns", "did_not_start"), ("is_dnf", "timed")])
def test_native_result_restrictions_preserve_recorded_times(flag, status):
    rows = results()
    rows[0][flag] = True
    driver = normalize_open(rows=rows).drivers[0]
    assert driver.status == status and driver.reason
    assert driver.phase_times_ms["SQ3"] == 74200


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -10, 0, "74.200", True])
def test_sprint_normalization_rejects_invalid_duration_types(value):
    rows = results()
    rows[0]["duration"][0] = value
    with pytest.raises(ValueError):
        normalize_open(rows=rows)


def test_source_session_identity_and_duration_shape_are_checked():
    rows = results()
    rows[0]["session_key"] = 124
    with pytest.raises(ValueError, match="different source session"):
        normalize_open(rows=rows)
    rows = results()
    rows[0]["duration"] = [75.123, 74.001]
    with pytest.raises(ValueError, match="exactly three"):
        normalize_open(rows=rows)
    with pytest.raises(ValueError, match="not qualifying"):
        normalize_open(session={**open_session(), "session_name": "Sprint"})


def write_season(directory):
    directory.mkdir(parents=True, exist_ok=True)
    season = ClassificationSeason(year=2024, events=[normalize_jolpica_race(race(), STAMP)])
    (directory / "2024.json").write_text(season.model_dump_json(), encoding="utf-8")
    return season


def test_published_file_round_trip_and_honest_missing_event(tmp_path):
    write_season(tmp_path)
    store = ClassificationStore(tmp_path)
    assert store.event(2024, 16).sessions[0].drivers[0].latest_time_ms == 74500
    assert store.event(2024, 17).sessions == []
    assert store.event(2023, 1).warnings
    assert store.coverage().years == []


def test_api_returns_classifications_without_touching_telemetry(tmp_path):
    directory = tmp_path / "classifications"
    write_season(directory)
    client = TestClient(create_app(tmp_path / "artifacts", tmp_path / "sessions", classification_dir=directory))
    response = client.get("/api/v1/classifications/2024/16")
    assert response.status_code == 200 and response.json()["schema_version"] == "1.0.0"
    assert response.json()["sessions"][0]["drivers"][0]["team_name"] == "Event Team"
    assert client.get("/api/v1/classifications/2024/17").json()["sessions"] == []
    assert client.get("/api/v1/classifications/coverage").json()["years"] == []
    assert client.get("/api/v1/sessions").json()["sessions"] == []


def test_corrupt_wrong_year_or_oversized_publications_fail_without_paths_leaking(tmp_path, monkeypatch):
    client = TestClient(create_app(tmp_path / "artifacts", tmp_path / "sessions", classification_dir=tmp_path))
    (tmp_path / "2024.json").write_text("{", encoding="utf-8")
    response = client.get("/api/v1/classifications/2024/16")
    assert response.status_code == 503 and str(tmp_path) not in response.text
    write_season(tmp_path)
    (tmp_path / "2023.json").write_bytes((tmp_path / "2024.json").read_bytes())
    assert client.get("/api/v1/classifications/2023/16").status_code == 503
    monkeypatch.setattr("lapdna.classifications.MAX_FILE", 2)
    assert client.get("/api/v1/classifications/2024/16").status_code == 503


def test_path_year_and_round_validation(tmp_path):
    client = TestClient(create_app(tmp_path / "artifacts", tmp_path / "sessions", classification_dir=tmp_path))
    for path in ("1949/1", "2100/1", "2024/0", "2024/31", "abc/1"):
        assert client.get("/api/v1/classifications/" + path).status_code == 422


def test_source_and_publication_timestamps_require_timezone():
    with pytest.raises(ValidationError, match="timezone"):
        normalize_jolpica_race(race(), STAMP.replace(tzinfo=None))
    with pytest.raises(ValidationError, match="timezone"):
        ClassificationCoverage(generated_at=STAMP.replace(tzinfo=None), years=[], qualifying_years=[],
            sprint_qualifying_years=[], seasons=[], sources=[], warnings=[])


def test_coverage_lists_and_counts_cannot_contradict_each_other():
    row = CoverageSeason(year=2024, event_count=1, qualifying_sessions=1,
        sprint_qualifying_sessions=0, driver_results=3, timed_results=2)
    with pytest.raises(ValidationError, match="qualifying coverage"):
        ClassificationCoverage(generated_at=STAMP, years=[2024], qualifying_years=[],
            sprint_qualifying_years=[], seasons=[row], sources=[], warnings=[])
    with pytest.raises(ValidationError, match="timed rows"):
        CoverageSeason(year=2024, event_count=1, qualifying_sessions=1,
            sprint_qualifying_sessions=0, driver_results=1, timed_results=2)


def test_partial_historical_coverage_keeps_calendar_denominator():
    row = CoverageSeason(year=1996, event_count=7, calendar_events=16, qualifying_sessions=7,
        sprint_qualifying_sessions=0, driver_results=150, timed_results=140)
    assert row.qualifying_sessions < row.calendar_events
    with pytest.raises(ValidationError, match="source calendar"):
        CoverageSeason(year=1996, event_count=17, calendar_events=16, qualifying_sessions=17,
            sprint_qualifying_sessions=0, driver_results=400, timed_results=390)


def test_symlink_cannot_read_a_publication_outside_configured_root(tmp_path):
    outside = tmp_path / "outside"
    write_season(outside)
    inside = tmp_path / "inside"
    inside.mkdir()
    try:
        (inside / "2024.json").symlink_to(outside / "2024.json")
    except OSError:
        pytest.skip("host does not permit symlink creation")
    client = TestClient(create_app(tmp_path / "artifacts", tmp_path / "sessions", classification_dir=inside))
    assert client.get("/api/v1/classifications/2024/16").status_code == 503
