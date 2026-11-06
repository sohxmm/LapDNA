"""Recorded qualifying classifications, separate from lap telemetry artifacts.

Snapshots are read-only publications. No endpoint fetches upstream data.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import re
from typing import Annotated, Literal, Self

from pydantic import Field, ValidationError, model_validator

from lapdna.calendar import client_year, utc_now
from lapdna.models import Contract

ClassificationPhase = Literal["Q1", "Q2", "Q3", "SQ1", "SQ2", "SQ3", "QUALIFYING", "QUALIFYING_1", "QUALIFYING_2"]
ClassificationProvider = Literal["jolpica", "openf1", "f1db"]
Text = Annotated[str, Field(min_length=1, max_length=250)]
MAX_CLASSIFICATION_MS = 30 * 60 * 1000
Millis = Annotated[int, Field(strict=True, gt=0, le=MAX_CLASSIFICATION_MS)]
MAX_FILE = 20 * 1024 * 1024
EMPTY_REASON = "No recorded phase time in this source snapshot."


class ClassificationDriver(Contract):
    driver_id: Text
    driver_number: str | None
    driver_code: str | None
    driver_name: Text
    team_id: str | None
    team_name: str | None
    position: Annotated[int, Field(strict=True, ge=1)] | None
    phase_times_ms: dict[ClassificationPhase, Millis | None]
    latest_timed_phase: ClassificationPhase | None
    latest_time_ms: Millis | None
    status: Literal["timed", "no_time", "disqualified", "did_not_start"]
    reason: str | None


class ClassificationSession(Contract):
    session_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")]
    label: Text
    session_type: Literal["qualifying", "sprint_qualifying"]
    phases: Annotated[list[ClassificationPhase], Field(min_length=1, max_length=3)]
    source: ClassificationProvider
    source_url: Annotated[str, Field(pattern=r"^https://")]
    retrieved_at: datetime
    status: Literal["completed", "partial"]
    drivers: Annotated[list[ClassificationDriver], Field(min_length=1, max_length=100)]
    warnings: list[str]

    @model_validator(mode="after")
    def coherent_session(self) -> Self:
        if self.retrieved_at.tzinfo is None:
            raise ValueError("classification retrieval time requires a timezone")
        allowed = (["SQ1", "SQ2", "SQ3"],) if self.session_type == "sprint_qualifying" else (
            ["Q1", "Q2", "Q3"], ["QUALIFYING"], ["QUALIFYING_1", "QUALIFYING_2"],
        )
        if self.session_type == "qualifying" and self.source == "f1db":
            allowed += (["QUALIFYING_1", "QUALIFYING_2", "QUALIFYING"],)
        if self.phases not in allowed:
            raise ValueError("classification phases must match the actual session format")
        ids = [driver.driver_id for driver in self.drivers]
        if len(ids) != len(set(ids)):
            raise ValueError("classification driver identities must be unique")
        for driver in self.drivers:
            if set(driver.phase_times_ms) != set(self.phases):
                raise ValueError("each driver needs every declared phase, including explicit nulls")
            timed = [phase for phase in self.phases if driver.phase_times_ms[phase] is not None]
            latest = timed[-1] if timed else None
            expected = driver.phase_times_ms[latest] if latest else None
            if (driver.latest_timed_phase, driver.latest_time_ms) != (latest, expected):
                raise ValueError("latest recorded time must match the last timed phase, not the minimum")
            if driver.status in {"timed", "no_time"} and (driver.status == "timed") != bool(timed):
                raise ValueError("driver timing status must agree with recorded values")
            if (not timed or driver.status in {"disqualified", "did_not_start"}) and not driver.reason:
                raise ValueError("an unavailable or restricted result needs an explanation")
        return self


class ClassificationEvent(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    year: Annotated[int, Field(strict=True, ge=1950, le=2100)]
    round: Annotated[int, Field(strict=True, ge=1, le=30)]
    event_name: Text | None
    circuit_id: Text | None
    sessions: list[ClassificationSession]
    warnings: list[str]

    @model_validator(mode="after")
    def unique_sessions(self) -> Self:
        ids = [session.session_id for session in self.sessions]
        kinds = [session.session_type for session in self.sessions]
        if len(ids) != len(set(ids)) or len(kinds) != len(set(kinds)):
            raise ValueError("an event may have one classification per session type")
        if self.sessions and (self.event_name is None or self.circuit_id is None):
            raise ValueError("published classifications require the actual event identity")
        return self


class ClassificationSeason(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    year: Annotated[int, Field(strict=True, ge=1950, le=2100)]
    events: list[ClassificationEvent]

    @model_validator(mode="after")
    def coherent_season(self) -> Self:
        rounds = [event.round for event in self.events]
        if rounds != sorted(set(rounds)) or any(event.year != self.year for event in self.events):
            raise ValueError("season event identities must match and have unique ordered rounds")
        return self


class CoverageSeason(Contract):
    year: Annotated[int, Field(strict=True, ge=1950, le=2100)]
    event_count: Annotated[int, Field(strict=True, ge=0)]
    calendar_events: Annotated[int, Field(strict=True, ge=0)] | None = None
    qualifying_sessions: Annotated[int, Field(strict=True, ge=0)]
    sprint_qualifying_sessions: Annotated[int, Field(strict=True, ge=0)]
    driver_results: Annotated[int, Field(strict=True, ge=0)]
    timed_results: Annotated[int, Field(strict=True, ge=0)]

    @model_validator(mode="after")
    def coherent_counts(self) -> Self:
        if self.timed_results > self.driver_results:
            raise ValueError("timed rows cannot exceed all driver rows")
        if max(self.qualifying_sessions, self.sprint_qualifying_sessions) > self.event_count:
            raise ValueError("session counts cannot exceed event count")
        if self.calendar_events is not None and self.qualifying_sessions > self.calendar_events:
            raise ValueError("qualifying count cannot exceed the source calendar event count")
        return self


class ClassificationSource(Contract):
    source: ClassificationProvider
    source_url: Annotated[str, Field(pattern=r"^https://")]
    retrieved_at: datetime

    @model_validator(mode="after")
    def aware_stamp(self) -> Self:
        if self.retrieved_at.tzinfo is None:
            raise ValueError("source retrieval time requires a timezone")
        return self


class ClassificationCoverage(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    generated_at: datetime
    years: list[int]
    qualifying_years: list[int]
    sprint_qualifying_years: list[int]
    seasons: list[CoverageSeason]
    sources: list[ClassificationSource]
    warnings: list[str]

    @model_validator(mode="after")
    def coherent_coverage(self) -> Self:
        if self.generated_at.tzinfo is None:
            raise ValueError("coverage generation time requires a timezone")
        for values in (self.years, self.qualifying_years, self.sprint_qualifying_years):
            if values != sorted(set(values)):
                raise ValueError("coverage years must be unique and ordered")
        if [season.year for season in self.seasons] != self.years:
            raise ValueError("coverage year summaries must match the declared years")
        if self.qualifying_years != [s.year for s in self.seasons if s.qualifying_sessions]:
            raise ValueError("qualifying coverage must agree with the season counts")
        if self.sprint_qualifying_years != [s.year for s in self.seasons if s.sprint_qualifying_sessions]:
            raise ValueError("sprint qualifying coverage must agree with the season counts")
        return self


class ClassificationsUnavailable(Exception):
    def __init__(self, message: str, status: int = 503, code: str = "classifications_unavailable"):
        self.message, self.status, self.code = message, status, code
        super().__init__(message)


class ClassificationStore:
    def __init__(self, directory: Path | None = None):
        self.directory = (directory if directory is not None else Path(__file__).parent / "classification_snapshots").resolve()

    def _read(self, name: str, model):
        path = (self.directory / name).resolve()
        try:
            path.relative_to(self.directory)
        except ValueError as exc:
            raise ClassificationsUnavailable("A results snapshot requires repair.") from exc
        try:
            if not path.exists():
                return None
            if path.stat().st_size > MAX_FILE:
                raise ValueError("classification snapshot exceeds size limit")
            return model.model_validate_json(path.read_bytes())
        except (OSError, ValueError, ValidationError) as exc:
            raise ClassificationsUnavailable("A results snapshot requires repair.") from exc

    def coverage(self) -> ClassificationCoverage:
        result = self._read("coverage.json", ClassificationCoverage)
        if result is not None:
            return result
        return ClassificationCoverage(generated_at=utc_now(), years=[], qualifying_years=[],
            sprint_qualifying_years=[], seasons=[], sources=[],
            warnings=["No qualifying classifications have been imported."])

    def event(self, year: int, round: int) -> ClassificationEvent:
        if type(year) is not int or not 1950 <= year <= client_year(utc_now()) or type(round) is not int or not 1 <= round <= 30:
            raise ClassificationsUnavailable("Choose an available year and calendar round.", 422, "classification_selection_invalid")
        result = self._read(f"{year}.json", ClassificationSeason)
        if result is not None:
            if result.year != year:
                raise ClassificationsUnavailable("A results snapshot requires repair.")
            for event in result.events:
                if event.round == round:
                    return event
        return ClassificationEvent(year=year, round=round, event_name=None, circuit_id=None, sessions=[],
            warnings=["No imported qualifying classification is available for this event."])


def parse_classification_time(value: str | None) -> int | None:
    """Parse reported clock text without turning no-time/status entries into zero."""
    if value is not None and not isinstance(value, str):
        raise ValueError("reported clock text must be a string or null")
    if value is None or value.strip().upper() in {"", "-", "—", "N/A", "NO TIME", "DNS", "DNF", "DSQ", "DQ", "DNQ", "DNP", "DNPQ"}:
        return None
    match = re.fullmatch(r"(?:(\d+):)?([0-5]?\d)(?:\.(\d{1,3}))?", value.strip())
    if not match:
        raise ValueError("unrecognized qualifying time")
    minutes, seconds, fraction = match.groups()
    result = (int(minutes or 0) * 60 + int(seconds)) * 1000 + int((fraction or "").ljust(3, "0") or 0)
    if not 0 < result <= MAX_CLASSIFICATION_MS:
        raise ValueError("qualifying duration must be positive and bounded")
    return result


def _seconds_ms(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("expected reported seconds or null")
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0:
            raise ValueError("reported seconds must be positive and finite")
        result = int((number * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except InvalidOperation as exc:
        raise ValueError("invalid reported duration") from exc
    if not 0 < result <= MAX_CLASSIFICATION_MS:
        raise ValueError("reported duration exceeds supported range")
    return result


def _positive_position(value) -> int | None:
    if value is None or value == "":
        return None
    text = str(value)
    return int(text) if re.fullmatch(r"[1-9]\d*", text) else None


def _record(identity: dict, times: dict, phases: list, reason: str | None = None,
            status_override: str | None = None) -> ClassificationDriver:
    timed = [phase for phase in phases if times[phase] is not None]
    latest = timed[-1] if timed else None
    return ClassificationDriver(**identity, phase_times_ms=times, latest_timed_phase=latest,
        latest_time_ms=times[latest] if latest else None, status=status_override or ("timed" if timed else "no_time"),
        reason=reason if reason else None if timed else EMPTY_REASON)


def normalize_jolpica_race(row: dict, retrieved_at: datetime) -> ClassificationEvent:
    """Normalize one complete published QualifyingResults race object."""
    year, round = int(row["season"]), int(row["round"])
    rows = row["QualifyingResults"]
    present = lambda value: value is not None and (not isinstance(value, str) or bool(value.strip()))
    if year < 2006 and any(present(item.get("Q3")) for item in rows):
        raise ValueError("unexpected third qualifying component in a legacy session")
    if year >= 2006:
        phases = ["Q1", "Q2", "Q3"]
    elif any(present(item.get("Q2")) for item in rows):
        phases = ["QUALIFYING_1", "QUALIFYING_2"]
    else:
        phases = ["QUALIFYING"]
    source_keys = {"QUALIFYING": "Q1", "QUALIFYING_1": "Q1", "QUALIFYING_2": "Q2"}
    records = []
    for item in rows:
        driver, team = item["Driver"], item.get("Constructor") or {}
        times = {phase: parse_classification_time(item.get(source_keys.get(phase, phase))) for phase in phases}
        records.append(_record({
            "driver_id": driver["driverId"], "driver_number": item.get("number"),
            "driver_code": driver.get("code"), "driver_name": " ".join(
                part for part in [driver.get("givenName"), driver.get("familyName")] if part),
            "team_id": team.get("constructorId"), "team_name": team.get("name"),
            "position": _positive_position(item.get("position")),
        }, times, phases))
    if not records:
        return ClassificationEvent(year=year, round=round, event_name=row["raceName"],
            circuit_id=row["Circuit"]["circuitId"], sessions=[], warnings=["No classification driver rows were published."])
    warnings = [] if year >= 2006 else [
        "Legacy published qualifying time; the historical session format differs from modern Q1/Q2/Q3."
    ]
    if phases == ["QUALIFYING_1", "QUALIFYING_2"]:
        warnings.append("This historical classification used two qualifying components. Published positions are preserved; the latest component time is not an aggregate classification time.")
    session = ClassificationSession(session_id=f"{year}-{round}-qualifying", label="Qualifying",
        session_type="qualifying", phases=phases, source="jolpica",
        source_url=f"https://api.jolpi.ca/ergast/f1/{year}/{round}/qualifying.json?limit=100",
        retrieved_at=retrieved_at, status="completed", drivers=records, warnings=warnings)
    return ClassificationEvent(year=year, round=round, event_name=row["raceName"],
        circuit_id=row["Circuit"]["circuitId"], sessions=[session], warnings=[])


def normalize_openf1_session(session: dict, results: list[dict], drivers: list[dict],
                             retrieved_at: datetime, *, year: int, round: int) -> ClassificationSession:
    """Normalize a final OpenF1 phase-duration array and event-specific driver roster."""
    name = session["session_name"]
    if name not in {"Qualifying", "Sprint Qualifying", "Sprint Shootout"}:
        raise ValueError("source session is not qualifying")
    if int(session["year"]) != year:
        raise ValueError("source session year does not match event")
    key = int(session["session_key"])
    sprint = name != "Qualifying"
    phases = ["SQ1", "SQ2", "SQ3"] if sprint else ["Q1", "Q2", "Q3"]
    roster = {}
    for driver in drivers:
        if int(driver["session_key"]) != key:
            raise ValueError("driver roster belongs to a different source session")
        number = str(driver["driver_number"])
        if number in roster:
            raise ValueError("duplicate driver number in source roster")
        roster[number] = driver
    classified = {}
    for item in results:
        if int(item["session_key"]) != key:
            raise ValueError("classification belongs to a different source session")
        number = str(item["driver_number"])
        if number in classified:
            raise ValueError("duplicate result in source classification")
        if number not in roster:
            raise ValueError("source result has no matching event-specific driver")
        classified[number] = item
    records = []
    for number, driver in roster.items():
        item = classified.get(number)
        values = item.get("duration") if item else None
        if values is None:
            values = [None, None, None]
        if not isinstance(values, list) or len(values) != 3:
            raise ValueError("qualifying duration must contain exactly three phase entries")
        times = {phase: _seconds_ms(value) for phase, value in zip(phases, values, strict=True)}
        notes = []
        status_override = None
        if item:
            for flag, explanation in (("is_dsq", "Source marks this result disqualified."),
                                      ("is_dns", "Source marks this result did not start."),
                                      ("is_dnf", "Source marks this result did not finish.")):
                if item.get(flag) is True:
                    notes.append(explanation)
                    if flag == "is_dsq":
                        status_override = "disqualified"
                    elif flag == "is_dns" and status_override != "disqualified":
                        status_override = "did_not_start"
        if item is None:
            notes.append("This event roster driver has no source classification row.")
        records.append(_record({
            "driver_id": f"openf1_{year}_{number}", "driver_number": number,
            "driver_code": driver.get("name_acronym"), "driver_name": driver.get("full_name") or " ".join(
                part for part in [driver.get("first_name"), driver.get("last_name")] if part),
            "team_id": None, "team_name": driver.get("team_name"),
            "position": _positive_position(item.get("position")) if item else None,
        }, times, phases, " ".join(notes) or None, status_override))
    records.sort(key=lambda record: (record.position is None, record.position or 0, record.driver_name))
    return ClassificationSession(session_id=f"{year}-{round}-{'sprint-qualifying' if sprint else 'qualifying'}",
        label="Sprint Qualifying" if sprint else "Qualifying", session_type="sprint_qualifying" if sprint else "qualifying",
        phases=phases, source="openf1", source_url=f"https://api.openf1.org/v1/session_result?session_key={key}",
        retrieved_at=retrieved_at, status="completed" if len(classified) == len(roster) else "partial",
        drivers=records, warnings=["Phase times are published bests; individual runs are not imported."])
