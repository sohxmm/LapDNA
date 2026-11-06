"""Published source acceptance and historical field fidelity."""
from datetime import datetime, timezone
from pathlib import Path

from lapdna.classifications import ClassificationCoverage, ClassificationSeason, ClassificationStore
from lapdna.f1db_classifications import normalize_f1db_race


def historical_row():
    race = {"id": 1, "year": 1983, "round": 1, "officialName": "Artificial historical qualifying",
            "circuitId": "test", "qualifyingFormat": "TWO_SESSION"}
    row = {"raceId": 1, "year": 1983, "round": 1, "driverId": "test-driver", "driverNumber": "12",
           "constructorId": "old-team", "positionNumber": 1, "positionText": "1", "timeMillis": 90500}
    return race, row


def test_historical_components_and_overall_keep_their_own_reported_values():
    race, row = historical_row()
    event = normalize_f1db_race(race, [row], {"test-driver": {"name": "Test Driver", "abbreviation": "TES"}},
        {"old-team": {"id": "old-team", "name": "Historical Team"}}, datetime.now(timezone.utc),
        "https://example.invalid/pinned-release", "test-version",
        [{**row, "timeMillis": 91500}], [{**row, "timeMillis": 90500}])
    driver = event.sessions[0].drivers[0]
    assert driver.phase_times_ms == {"QUALIFYING_1": 91500, "QUALIFYING_2": 90500, "QUALIFYING": 90500}
    assert driver.team_name == "Historical Team" and driver.driver_number == "12"
    assert driver.latest_time_ms == 90500


def test_unsupported_historical_component_is_null_without_corrupting_overall_time():
    race, row = historical_row()
    event = normalize_f1db_race(race, [row], {"test-driver": {"name": "Test Driver"}},
        {"old-team": {"id": "old-team", "name": "Historical Team"}}, datetime.now(timezone.utc),
        "https://example.invalid/pinned-release", "test-version",
        [{**row, "timeMillis": 3_600_000}], [{**row, "timeMillis": 90500}])
    driver = event.sessions[0].drivers[0]
    assert driver.phase_times_ms["QUALIFYING_1"] is None
    assert driver.phase_times_ms["QUALIFYING"] == 90500
    assert "outside" in driver.reason


def test_published_mexico_2026_recorded_times_and_disqualification():
    event = ClassificationStore().event(2026, 19)
    session = next(item for item in event.sessions if item.session_type == "qualifying")
    by_code = {driver.driver_code: driver for driver in session.drivers}
    assert len(by_code) == 22
    assert by_code["HAM"].team_name == "Ferrari"
    assert by_code["HAM"].phase_times_ms == {"Q1": 77341, "Q2": 76953, "Q3": 76514}
    assert by_code["LEC"].phase_times_ms["Q3"] - by_code["HAM"].phase_times_ms["Q3"] == 119
    assert by_code["LAW"].status == "disqualified" and by_code["LAW"].position is None
    assert not any(item.session_type == "sprint_qualifying" for item in event.sessions)


def test_published_year_coverage_matches_every_validated_season_snapshot():
    folder = ClassificationStore().directory
    coverage = ClassificationCoverage.model_validate_json((folder / "coverage.json").read_bytes())
    for summary in coverage.seasons:
        season = ClassificationSeason.model_validate_json((folder / f"{summary.year}.json").read_bytes())
        sessions = [session for event in season.events for session in event.sessions]
        assert len(season.events) == summary.event_count
        assert sum(s.session_type == "qualifying" for s in sessions) == summary.qualifying_sessions
        assert sum(s.session_type == "sprint_qualifying" for s in sessions) == summary.sprint_qualifying_sessions
        assert sum(len(s.drivers) for s in sessions) == summary.driver_results
    assert coverage.years[0] == 1950


def test_event_specific_team_is_not_a_current_team_lookup():
    past = ClassificationStore().event(2019, 18).sessions[0]
    present = ClassificationStore().event(2026, 19).sessions[0]
    assert next(driver for driver in past.drivers if driver.driver_code == "HAM").team_name == "Mercedes"
    assert next(driver for driver in present.drivers if driver.driver_code == "HAM").team_name == "Ferrari"
