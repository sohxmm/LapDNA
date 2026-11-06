"""Publish validated classification snapshots from the explicitly fetched source cache.

No upstream download occurs here. Run import_classifications.py first.
"""
import argparse
from collections import defaultdict
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from lapdna.calendar import CalendarSeason, normalize as normalize_calendar
from lapdna.classifications import (
    ClassificationCoverage, ClassificationEvent, ClassificationSeason,
    ClassificationSource, CoverageSeason,
    normalize_jolpica_race, normalize_openf1_session,
)
from lapdna.f1db_classifications import normalize_f1db_race

DEFAULT_CACHE = ROOT / "work/classification-source"
DEFAULT_OUTPUT = ROOT / "services/api/src/lapdna/classification_snapshots"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def aware(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("source retrieval timestamp lacks timezone")
    return parsed


def country_key(value):
    text = "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if c.isalnum())
    return {"usa": "unitedstates", "us": "unitedstates", "uk": "unitedkingdom",
            "greatbritain": "unitedkingdom", "uae": "unitedarabemirates"}.get(text, text)


def match_sprint_event(session, races):
    """Require a unique same-country calendar weekend; never enumerate sessions as rounds."""
    start = aware(session["date_start"]).astimezone(timezone.utc).date()
    candidates = [race for race in races if int(race["season"]) == int(session["year"])
        and 0 <= (date.fromisoformat(race["date"]) - start).days <= 4
        and country_key(race["Circuit"]["Location"]["country"]) == country_key(session["country_name"])]
    if len(candidates) != 1:
        raise ValueError(f"Cannot uniquely match sprint session {session['session_key']} to its calendar event")
    return candidates[0]


def write_json(path, model):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    content = model.model_dump_json(indent=2) + "\n" if hasattr(model, "model_dump_json") else json.dumps(model, indent=2, ensure_ascii=False) + "\n"
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def build_publication(cache, output, calendar_output=None):
    source = load(cache / "jolpica-qualifying.json")
    raw_races = source["payload"]["MRData"]["RaceTable"]["Races"]
    count = sum(len(race["QualifyingResults"]) for race in raw_races)
    expected = int(source["payload"]["MRData"]["total"])
    if count != expected or source.get("actual_records") != expected:
        raise ValueError("The qualifying source archive is incomplete")
    retrieved = aware(source["retrieved_at"])
    events = {}
    raw_by_identity = {}
    for row in raw_races:
        event = normalize_jolpica_race(row, retrieved)
        key = (event.year, event.round)
        if key in events:
            raise ValueError("Duplicate source event")
        events[key] = event
        raw_by_identity[key] = row
    calendar_files = sorted(cache.glob("jolpica-calendar-*.json"))
    calendars = []
    for path in calendar_files:
        record = load(path)
        year = int(path.stem.rsplit("-", 1)[1])
        calendar = normalize_calendar(record["payload"], year, aware(record["retrieved_at"]))
        calendars.append(calendar)
        for row in record["payload"]["MRData"]["RaceTable"]["Races"]:
            raw_by_identity[(int(row["season"]), int(row["round"]))] = row
    if not calendar_files:
        raise ValueError("Fetch full source calendars before matching sprint events")
    calendar_counts = {calendar.year: len(calendar.races) for calendar in calendars}
    # A rate-limited refresh may reuse a previously published, source-stamped
    # calendar for counts. Never assign a new retrieval time to that snapshot.
    if calendar_output:
        for year in {key[0] for key in events}:
            saved = calendar_output / f"{year}.json"
            if year not in calendar_counts and saved.exists():
                previous = CalendarSeason.model_validate_json(saved.read_bytes())
                if previous.year != year:
                    raise ValueError("Existing calendar identity does not match its filename")
                calendar_counts[year] = len(previous.races)
    sources = [ClassificationSource(source="jolpica", source_url=source["source_url"], retrieved_at=retrieved)]
    fallback_count, exclusion_replacements = 0, 0
    archive_path = cache / "f1db-archive.json"
    if archive_path.exists():
        archive = load(archive_path)
        folder = cache / "f1db"
        members = {}
        for name in ("races", "drivers", "constructors", "races-qualifying-results",
                     "races-qualifying-1-results", "races-qualifying-2-results"):
            member = load(folder / f"f1db-{name}.json")
            if member["archive_sha256"] != archive["sha256"]:
                raise ValueError("F1DB members belong to different source revisions")
            members[name] = member["payload"]
        qrows, first, second = defaultdict(list), defaultdict(list), defaultdict(list)
        for name, target in (("races-qualifying-results", qrows),
                             ("races-qualifying-1-results", first),
                             ("races-qualifying-2-results", second)):
            for row in members[name]:
                target[int(row["raceId"])].append(row)
        driver_index = {row["id"]: row for row in members["drivers"]}
        constructor_index = {row["id"]: row for row in members["constructors"]}
        for race in members["races"]:
            identity = (int(race["year"]), int(race["round"]))
            native_rows = qrows[race["id"]]
            excluded = any(row.get("positionText") in {"DSQ", "EX"} for row in native_rows)
            if not native_rows or (identity in events and not excluded):
                continue
            existed = identity in events
            events[identity] = normalize_f1db_race(race, native_rows, driver_index, constructor_index,
                aware(archive["retrieved_at"]), archive["source_url"], archive["release"],
                first[race["id"]], second[race["id"]])
            if existed:
                exclusion_replacements += 1
                events[identity].warnings.append("This complete F1DB classification preserves native exclusion/disqualification status that the Jolpica phase-time response does not expose. No driver rows were combined across providers.")
            else:
                fallback_count += 1
        sources.append(ClassificationSource(source="f1db", source_url=archive["source_url"],
                                             retrieved_at=aware(archive["retrieved_at"])))
    matches, pending = [], []
    for path in sorted(cache.glob("openf1-*-sessions.json")):
        year = int(path.stem.split("-")[1])
        sessions_record = load(path)
        results_record = load(cache / f"openf1-{year}-results.json")
        driver_record = load(cache / f"openf1-{year}-drivers.json")
        results, drivers = defaultdict(list), defaultdict(list)
        for row in results_record["payload"]:
            results[int(row["session_key"])].append(row)
        for row in driver_record["payload"]:
            drivers[int(row["session_key"])].append(row)
        sources.append(ClassificationSource(source="openf1", source_url=results_record["source_url"],
                                             retrieved_at=aware(results_record["retrieved_at"])))
        for session in sessions_record["payload"]:
            if session["session_name"] not in {"Sprint Qualifying", "Sprint Shootout"}:
                continue
            key = int(session["session_key"])
            if not results[key]:
                pending.append({"year": year, "session_key": key, "reason": "No published final result rows"})
                continue
            race = match_sprint_event(session, list(raw_by_identity.values()))
            identity = (year, int(race["round"]))
            event = events.get(identity) or ClassificationEvent(year=year, round=identity[1],
                event_name=race["raceName"], circuit_id=race["Circuit"]["circuitId"],
                sessions=[], warnings=[])
            normalized = normalize_openf1_session(session, results[key], drivers[key],
                aware(results_record["retrieved_at"]), year=year, round=identity[1])
            # A shared event roster can retain the established Jolpica driver identity.
            # Match only explicit same-event racing numbers; no current-team lookup.
            q = next((s for s in event.sessions if s.session_type == "qualifying"), None)
            if q:
                known = {d.driver_number: d for d in q.drivers if d.driver_number}
                for driver in normalized.drivers:
                    other = known.get(driver.driver_number)
                    if other and other.driver_code and driver.driver_code and other.driver_code == driver.driver_code:
                        driver.driver_id = other.driver_id
                        driver.team_id = other.team_id
                normalized = type(normalized).model_validate(normalized.model_dump())
            events[identity] = ClassificationEvent(**{**event.model_dump(), "sessions": [*event.sessions, normalized]})
            matches.append({"year": year, "round": identity[1], "event_name": race["raceName"],
                "source_session": key, "source_country": session["country_name"],
                "session_start": session["date_start"], "race_date": race["date"],
                "driver_results": len(normalized.drivers), "status": normalized.status})
    summaries = []
    publications = []
    for year in sorted({key[0] for key in events}):
        year_events = [events[key] for key in sorted(events) if key[0] == year]
        season = ClassificationSeason(year=year, events=year_events)
        sessions = [s for event in year_events for s in event.sessions]
        rows = [d for s in sessions for d in s.drivers]
        summaries.append(CoverageSeason(year=year, event_count=len(year_events),
            calendar_events=calendar_counts.get(year),
            qualifying_sessions=sum(s.session_type == "qualifying" for s in sessions),
            sprint_qualifying_sessions=sum(s.session_type == "sprint_qualifying" for s in sessions),
            driver_results=len(rows), timed_results=sum(d.status == "timed" for d in rows)))
        publications.append((output / f"{year}.json", season))
    coverage = ClassificationCoverage(generated_at=datetime.now(timezone.utc),
        years=[s.year for s in summaries],
        qualifying_years=[s.year for s in summaries if s.qualifying_sessions],
        sprint_qualifying_years=[s.year for s in summaries if s.sprint_qualifying_sessions],
        seasons=summaries, sources=sources, warnings=[
            "Qualifying classifications span 1950 onward using F1DB whole-event backfill and Jolpica's published archive from 1994. Historical individual timing values may be absent.",
            "Compare published counts with each season's calendar; absent results and timing values are not synthesized.",
            "Before 2006, legacy session times are preserved; the first six 2005 events have two qualifying components. Modern Q1/Q2/Q3 phases are not invented.",
            "Sprint Qualifying phase classifications are imported from OpenF1 from 2023 where published.",
            "2021–2022 sprint weekends used a different format; no separate SQ1/SQ2/SQ3 session is fabricated.",
            "Phase bests are recorded classification values, not individual run or lap inventories.",
            "A latest timed phase is not necessarily a driver's final attempted phase.",
        ])
    # Validate the entire build before replacing any served file.
    for path, season in publications:
        write_json(path, season)
    write_json(output / "coverage.json", coverage)
    if calendar_output:
        for calendar in calendars:
            write_json(calendar_output / f"{calendar.year}.json", calendar)
    report = {"scope": "Public final qualifying classification facts; no raw telemetry or individual lap data",
        "source_driver_records": count, "events": len(events),
        "f1db_backfilled_events": fallback_count,
        "f1db_exclusion_aware_events": exclusion_replacements,
        "qualifying_sessions": sum(s.qualifying_sessions for s in summaries),
        "sprint_qualifying_sessions": sum(s.sprint_qualifying_sessions for s in summaries),
        "driver_results": sum(s.driver_results for s in summaries),
        "timed_results": sum(s.timed_results for s in summaries),
        "years": coverage.years, "sprint_qualifying_years": coverage.sprint_qualifying_years,
        "sprint_calendar_matches": matches, "pending": pending,
        "source_archive_sha256": source["sha256"],
        "publication_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p, _ in publications}}
    write_json(cache / "publication-report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--calendar-output-dir", type=Path, default=ROOT / "services/api/src/lapdna/calendar_snapshots")
    args = parser.parse_args()
    report = build_publication(args.cache_dir.resolve(), args.output_dir.resolve(), args.calendar_output_dir.resolve())
    print(json.dumps({k: v for k, v in report.items() if k not in {"sprint_calendar_matches", "publication_sha256"}}, indent=2))


if __name__ == "__main__":
    main()
