"""Small, provenance-preserving calendar adapter. It never imports telemetry."""

import json
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Annotated, Callable, Literal
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, ValidationError, model_validator

from lapdna.models import Contract

MIN_YEAR = 1950
MAX_BODY = 2 * 1024 * 1024
TTL = timedelta(hours=6)
MAX_CACHED_YEARS = 12
SOURCE_BASE = "https://api.jolpi.ca/ergast/f1"
UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(UTC)


def client_year(now: datetime) -> int:
    try:
        zone = ZoneInfo("Asia/Kolkata")
    except ZoneInfoNotFoundError:
        zone = timezone(timedelta(hours=5, minutes=30))
    return now.astimezone(zone).year


class Seasons(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    current_year: int
    min_year: Literal[1950] = 1950
    years: list[int]


class CalendarRace(Contract):
    race_id: str
    year: int
    round: Annotated[int, Field(ge=1, le=30)]
    name: str
    circuit_id: str
    circuit_name: str
    country: str
    locality: str
    race_date: date
    race_start_at: datetime | None
    qualifying_date: date | None
    qualifying_start_at: datetime | None
    qualifying_status: Literal["upcoming", "start_time_passed", "time_unknown"]


class CalendarSeason(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    year: Annotated[int, Field(ge=1950)]
    source: Literal["jolpica"] = "jolpica"
    source_url: str
    retrieved_at: datetime
    stale: bool
    warnings: list[str]
    races: list[CalendarRace]

    @model_validator(mode="after")
    def coherent_year(self):
        if self.retrieved_at.tzinfo is None:
            raise ValueError("calendar provenance needs an aware retrieval timestamp")
        rounds = [race.round for race in self.races]
        if len(set(rounds)) != len(rounds) or rounds != sorted(rounds):
            raise ValueError("calendar rounds must be unique and ordered")
        if any(race.year != self.year or race.race_id != f"{self.year}-{race.round}" for race in self.races):
            raise ValueError("race identities must match their season and round")
        return self


class CalendarUnavailable(Exception):
    def __init__(self, message: str, status: int = 503, code: str = "calendar_unavailable"):
        self.message, self.status, self.code = message, status, code
        super().__init__(message)


def fetch_calendar(year: int) -> dict:
    request = Request(
        f"{SOURCE_BASE}/{year}/races.json?limit=100",
        headers={"User-Agent": "LapDNA/0.2 calendar-metadata", "Accept": "application/json"},
    )
    with urlopen(request, timeout=5) as response:
        raw = response.read(MAX_BODY + 1)
    if len(raw) > MAX_BODY:
        raise ValueError("calendar response exceeds limit")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError("calendar source returned an unexpected document")
    return result


def source_stamp(day: str | None, time: str | None) -> datetime | None:
    if not day or not time:
        return None
    stamp = datetime.fromisoformat(day + "T" + time.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("calendar source timestamp lacks a timezone")
    return stamp


def normalize(payload: dict, year: int, retrieved_at: datetime) -> CalendarSeason:
    table = payload["MRData"]["RaceTable"]
    if str(table.get("season")) != str(year):
        raise ValueError("calendar source returned a different season")
    source_rows = table["Races"]
    total = int(payload["MRData"]["total"])
    if not isinstance(source_rows, list) or total != len(source_rows):
        raise ValueError("calendar source response was incomplete")
    races = []
    for row in source_rows:
        if str(row["season"]) != str(year):
            raise ValueError("calendar race belongs to another season")
        circuit, phase = row["Circuit"], row.get("Qualifying") or {}
        quali = source_stamp(phase.get("date"), phase.get("time"))
        number = int(row["round"])
        races.append(CalendarRace(
            race_id=f"{year}-{number}", year=year, round=number, name=row["raceName"],
            circuit_id=circuit["circuitId"], circuit_name=circuit["circuitName"],
            country=circuit["Location"]["country"], locality=circuit["Location"]["locality"],
            race_date=date.fromisoformat(row["date"]),
            race_start_at=source_stamp(row["date"], row.get("time")),
            qualifying_date=date.fromisoformat(phase["date"]) if phase.get("date") else None,
            qualifying_start_at=quali,
            qualifying_status="time_unknown" if quali is None else "start_time_passed" if quali <= retrieved_at else "upcoming",
        ))
    return CalendarSeason(
        year=year, source_url=f"{SOURCE_BASE}/{year}/races.json?limit=100",
        retrieved_at=retrieved_at, stale=False, warnings=[], races=sorted(races, key=lambda race: race.round),
    )


class CalendarService:
    """Bounded warm-instance cache with explicit provenance-stamped snapshot fallback."""

    def __init__(self, fetch: Callable[[int], dict] = fetch_calendar, now: Callable[[], datetime] = utc_now,
                 snapshot_dir: Path | None = None):
        self.fetch, self.now = fetch, now
        self.snapshot_dir = snapshot_dir if snapshot_dir is not None else Path(__file__).parent / "calendar_snapshots"
        self.cache: OrderedDict[int, CalendarSeason] = OrderedDict()
        self.retry_after: OrderedDict[int, datetime] = OrderedDict()
        self.lock = Lock()

    def seasons(self) -> Seasons:
        current = client_year(self.now())
        return Seasons(current_year=current, years=list(range(current, MIN_YEAR - 1, -1)))

    def _for_response(self, value: CalendarSeason, stale: bool, warning: str | None = None) -> CalendarSeason:
        now = self.now()
        races = [race.model_copy(update={"qualifying_status": "time_unknown" if race.qualifying_start_at is None
                 else "start_time_passed" if race.qualifying_start_at <= now else "upcoming"}) for race in value.races]
        return value.model_copy(update={"stale": stale, "warnings": [warning] if warning else [], "races": races})

    def get(self, year: int) -> CalendarSeason:
        current = client_year(self.now())
        if year < MIN_YEAR or year > current:
            raise CalendarUnavailable(f"Choose a season between {MIN_YEAR} and {current}.", 422, "year_unavailable")
        # Serializes cold loads and makes repeated concurrent requests share the cache.
        with self.lock:
            previous = self.cache.get(year)
            if self.now() < self.retry_after.get(year, datetime.min.replace(tzinfo=UTC)):
                fallback = previous or self._snapshot(year)
                if fallback is not None:
                    return self._for_response(fallback, True, "The calendar source is unavailable. Showing its last saved calendar; dates or rounds may have changed.")
                raise CalendarUnavailable("The calendar source is unavailable. Please retry later.")
            if previous is not None and self.now() - previous.retrieved_at < TTL:
                self.cache.move_to_end(year)
                return self._for_response(previous, False)
            try:
                value = normalize(self.fetch(year), year, self.now())
            except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
                self.retry_after[year] = self.now() + timedelta(minutes=1)
                self.retry_after.move_to_end(year)
                while len(self.retry_after) > MAX_CACHED_YEARS:
                    self.retry_after.popitem(last=False)
                fallback = previous or self._snapshot(year)
                if fallback is None:
                    raise CalendarUnavailable("The calendar source is unavailable. Please retry later.") from exc
                return self._for_response(fallback, True, "The calendar source is unavailable. Showing its last saved calendar; dates or rounds may have changed.")
            self.cache[year] = value
            self.retry_after.pop(year, None)
            self.cache.move_to_end(year)
            while len(self.cache) > MAX_CACHED_YEARS:
                self.cache.popitem(last=False)
            return self._for_response(value, False)

    def _snapshot(self, year: int) -> CalendarSeason | None:
        path = self.snapshot_dir / f"{year}.json"
        try:
            if path.stat().st_size > MAX_BODY:
                return None
            result = CalendarSeason.model_validate_json(path.read_bytes())
            if result.year != year:
                return None
            return result
        except (OSError, ValueError, ValidationError):
            return None
