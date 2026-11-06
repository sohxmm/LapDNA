"""Download public final qualifying classifications into a resumable private cache.

This fetches results/identities only, never car telemetry or individual laps.
Run from the repository root with its Python environment. Publication/normalization
is a separate reviewed step; raw caches are deliberately outside version control.
"""

import argparse
import hashlib
import io
import json
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE = ROOT / "work" / "classification-source"
MAX_BYTES = 20 * 1024 * 1024
JOLPICA = "https://api.jolpi.ca/ergast/f1"
OPENF1 = "https://api.openf1.org/v1"
F1DB_TAG = "v2026.19.0"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


class Fetcher:
    def __init__(self, cache, requests_per_second=2.5, refresh=False):
        self.cache = cache
        self.interval = 1 / requests_per_second
        self.refresh = refresh
        self.last = 0.0
        self.network_requests = 0
        self.cache_hits = 0

    def get(self, filename, url, allow_empty=False):
        path = self.cache / filename
        if path.exists() and not self.refresh:
            stored = json.loads(path.read_text(encoding="utf-8"))
            if stored.get("source_url") == url and "payload" in stored:
                self.cache_hits += 1
                return stored
        for attempt in range(4):
            delay = max(0, self.interval - (time.monotonic() - self.last))
            if delay:
                time.sleep(delay)
            self.last = time.monotonic()
            request = Request(url, headers={"User-Agent": "LapDNA/0.3 classification-import", "Accept": "application/json"})
            try:
                self.network_requests += 1
                with urlopen(request, timeout=30) as response:
                    body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise ValueError("source response exceeds 20 MiB limit")
                payload = json.loads(body)
                envelope = {"source_url": url, "retrieved_at": stamp(), "sha256": hashlib.sha256(body).hexdigest(), "payload": payload}
                save(path, envelope)
                return envelope
            except HTTPError as error:
                if error.code == 404 and allow_empty:
                    envelope = {"source_url": url, "retrieved_at": stamp(), "sha256": hashlib.sha256(b"[]").hexdigest(), "payload": [], "source_status": 404}
                    save(path, envelope)
                    return envelope
                if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise
                retry = error.headers.get("Retry-After", "")
                if retry.isdigit() and float(retry) > 45:
                    raise RuntimeError(f"Source rate limit: Retry-After is {retry}s. Cached progress is preserved; rerun after that delay.") from error
                delay = min(45, max(2 ** (attempt + 1), float(retry) if retry.isdigit() else 0))
                print(f"Source HTTP {error.code}; retrying after {delay:g}s", flush=True)
                time.sleep(delay)
            except (URLError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
        raise RuntimeError("source fetch did not complete")


def import_jolpica(fetcher):
    """Paginate the whole result archive; page boundaries can split a race."""
    offset, expected, received = 0, None, 0
    races, seen, pages = {}, set(), []
    while expected is None or offset < expected:
        url = f"{JOLPICA}/qualifying.json?limit=100&offset={offset}"
        record = fetcher.get(f"pages/jolpica-qualifying-{offset:06}.json", url)
        body = record["payload"]["MRData"]
        total, limit, actual_offset = int(body["total"]), int(body["limit"]), int(body["offset"])
        if expected is None:
            expected = total
        if expected != total or actual_offset != offset or not 1 <= limit <= 100:
            raise ValueError("Jolpica archive changed or returned mismatched pagination; refresh the import")
        count = 0
        for race in body["RaceTable"]["Races"]:
            key = (str(race["season"]), str(race["round"]))
            if key not in races:
                races[key] = {**race, "QualifyingResults": []}
            for driver in race["QualifyingResults"]:
                identity = (*key, driver["Driver"]["driverId"])
                if identity in seen:
                    raise ValueError(f"duplicate qualifying identity: {identity}")
                seen.add(identity)
                races[key]["QualifyingResults"].append(driver)
                count += 1
        if count != min(limit, expected - offset):
            raise ValueError("Jolpica page is incomplete")
        pages.append({"source_url": url, "retrieved_at": record["retrieved_at"], "sha256": record["sha256"], "records": count})
        received += count
        offset += count
        if len(pages) % 10 == 0 or received == expected:
            print(f"Jolpica: {received}/{expected} classification records", flush=True)
    ordered = sorted(races.values(), key=lambda race: (int(race["season"]), int(race["round"])))
    payload = {"MRData": {"total": str(expected), "RaceTable": {"Races": ordered}}}
    envelope = {"source_url": f"{JOLPICA}/qualifying.json", "retrieved_at": stamp(),
                "sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "payload": payload, "pages": pages, "expected_records": expected, "actual_records": received}
    save(fetcher.cache / "jolpica-qualifying.json", envelope)
    years = sorted({int(race["season"]) for race in ordered})
    return {"years": years, "events": len(ordered), "driver_records": received,
            "first_event": {key: ordered[0][key] for key in ("season", "round", "raceName")},
            "last_event": {key: ordered[-1][key] for key in ("season", "round", "raceName")}}


def import_openf1(fetcher, through_year):
    summary = []
    for year in range(2023, through_year + 1):
        sessions = fetcher.get(f"openf1-{year}-sessions.json", f"{OPENF1}/sessions?year={year}")["payload"]
        meetings = fetcher.get(f"openf1-{year}-meetings.json", f"{OPENF1}/meetings?year={year}")["payload"]
        if not isinstance(sessions, list) or not isinstance(meetings, list):
            raise ValueError("OpenF1 metadata did not return arrays")
        if not sessions:
            summary.append({"year": year, "sessions": 0, "status": "no_sessions"})
            continue
        keys = [int(session["session_key"]) for session in sessions]
        # Strict numeric bounds one beyond the integer keys include the endpoints.
        query = f"session_key%3E={min(keys) - 1}&session_key%3C={max(keys) + 1}"
        results = fetcher.get(f"openf1-{year}-results.json", f"{OPENF1}/session_result?{query}", allow_empty=True)["payload"]
        drivers = fetcher.get(f"openf1-{year}-drivers.json", f"{OPENF1}/drivers?{query}", allow_empty=True)["payload"]
        if not isinstance(results, list) or not isinstance(drivers, list):
            raise ValueError("OpenF1 classification/driver responses did not return arrays")
        result_sessions = {int(row["session_key"]) for row in results}
        driver_sessions = {int(row["session_key"]) for row in drivers}
        sprint = [session for session in sessions if session["session_name"] in ("Sprint Qualifying", "Sprint Shootout")]
        entries = [{"session_key": session["session_key"], "meeting_key": session["meeting_key"],
                    "session_name": session["session_name"], "date_start": session["date_start"],
                    "circuit_short_name": session["circuit_short_name"],
                    "has_results": int(session["session_key"]) in result_sessions,
                    "has_drivers": int(session["session_key"]) in driver_sessions,
                    "result_rows": sum(row["session_key"] == session["session_key"] for row in results)} for session in sprint]
        summary.append({"year": year, "sessions": len(sessions), "meetings": len(meetings),
                        "result_rows": len(results), "driver_rows": len(drivers), "sprint_qualifying": entries})
        print(f"OpenF1 {year}: {len(sessions)} sessions; {len(results)} result rows; {len(sprint)} sprint-qualifying metadata entries", flush=True)
    return summary


def import_calendars(fetcher, years):
    calendars = []
    # Calendars are small but numerous; limit their network calls to one/second.
    previous_interval = fetcher.interval
    fetcher.interval = max(fetcher.interval, 1.0)
    for year in years:
        url = f"{JOLPICA}/{year}/races.json?limit=100"
        record = fetcher.get(f"jolpica-calendar-{year}.json", url)
        body = record["payload"]["MRData"]
        table = body["RaceTable"]
        if str(table["season"]) != str(year) or len(table["Races"]) != int(body["total"]):
            raise ValueError(f"incomplete or mismatched calendar for {year}")
        if any(str(race["season"]) != str(year) for race in table["Races"]):
            raise ValueError(f"calendar row belongs to another year: {year}")
        calendars.append({"year": year, "races": len(table["Races"]), "retrieved_at": record["retrieved_at"], "source_url": url})
    fetcher.interval = previous_interval
    print(f"Jolpica calendars: {len(calendars)} complete seasons", flush=True)
    return calendars


def import_f1db(fetcher):
    """Read a small pinned public data release, extracting an explicit allowlist."""
    base = f"https://github.com/f1db/f1db/releases/download/{F1DB_TAG}"
    archive_name = "f1db-json-splitted.zip"
    archive_path = fetcher.cache / f"f1db-{F1DB_TAG}-json-splitted.zip"
    provenance_path = fetcher.cache / "f1db-archive.json"
    previous = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else None
    if archive_path.exists() and previous and not fetcher.refresh:
        content = archive_path.read_bytes()
        if hashlib.sha256(content).hexdigest() != previous["sha256"]:
            raise ValueError("cached F1DB archive digest mismatch")
        provenance = previous
        fetcher.cache_hits += 1
    else:
        def download(url, maximum):
            request = Request(url, headers={"User-Agent": "LapDNA/0.3 classification-import", "Accept": "application/octet-stream"})
            fetcher.network_requests += 1
            with urlopen(request, timeout=30) as response:
                value = response.read(maximum + 1)
            if len(value) > maximum:
                raise ValueError("F1DB download exceeds limit")
            return value
        content = download(f"{base}/{archive_name}", 10 * 1024 * 1024)
        checksums = download(f"{base}/checksums_sha256.txt", 64 * 1024).decode()
        digest = hashlib.sha256(content).hexdigest()
        expected = next((line.split()[0] for line in checksums.splitlines() if line.split()[-1].lstrip("*") == archive_name), None)
        if digest != expected:
            raise ValueError("F1DB release checksum mismatch")
        fetcher.cache.mkdir(parents=True, exist_ok=True)
        temporary = archive_path.with_suffix(".tmp")
        temporary.write_bytes(content)
        temporary.replace(archive_path)
        provenance = {"source_url": f"{base}/{archive_name}", "retrieved_at": stamp(), "sha256": digest,
                      "release": F1DB_TAG, "bytes": len(content), "checksum_url": f"{base}/checksums_sha256.txt",
                      "licence": "CC-BY-4.0", "attribution": "F1DB (https://github.com/f1db/f1db)"}
        save(provenance_path, provenance)
    allowed = {"f1db-drivers.json", "f1db-constructors.json", "f1db-races.json", "f1db-seasons.json",
               "f1db-circuits.json", "f1db-grands-prix.json", "f1db-races-qualifying-results.json",
               "f1db-races-qualifying-1-results.json", "f1db-races-qualifying-2-results.json",
               "f1db-races-sprint-qualifying-results.json"}
    extracted, total_bytes = [], 0
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        members = archive.infolist()
        for member in members:
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in member.filename or ":" in member.filename:
                raise ValueError("unsafe path in F1DB data archive")
            if member.is_dir() or path.name not in allowed:
                continue
            if member.file_size > MAX_BYTES:
                raise ValueError("F1DB data member exceeds limit")
            total_bytes += member.file_size
            if total_bytes > 100 * 1024 * 1024:
                raise ValueError("F1DB selected data exceeds total extraction limit")
            body = archive.read(member)
            payload = json.loads(body)
            envelope = {"source_url": provenance["source_url"], "retrieved_at": provenance["retrieved_at"],
                        "sha256": hashlib.sha256(body).hexdigest(), "archive_sha256": provenance["sha256"],
                        "archive_member": member.filename, "release": F1DB_TAG,
                        "licence": provenance["licence"], "attribution": provenance["attribution"], "payload": payload}
            save(fetcher.cache / "f1db" / path.name, envelope)
            extracted.append({"name": path.name, "bytes": len(body), "records": len(payload) if isinstance(payload, list) else None})
    if not {"f1db-drivers.json", "f1db-constructors.json", "f1db-races.json", "f1db-races-qualifying-results.json"}.issubset({item["name"] for item in extracted}):
        print("F1DB archive member names: " + ", ".join(member.filename for member in members), flush=True)
        raise ValueError("F1DB required metadata/classification members absent")
    report = {**provenance, "files": extracted}
    save(fetcher.cache / "f1db-summary.json", report)
    print(f"F1DB {F1DB_TAG}: {len(extracted)} selected files; {total_bytes} uncompressed bytes", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--through-year", type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument("--calendar-from", type=int, default=1950)
    parser.add_argument("--source", choices=("all", "jolpica", "openf1", "f1db"), default="all")
    parser.add_argument("--requests-per-second", type=float, default=2.5)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if not 0 < args.requests_per_second <= 3:
        parser.error("request rate must be above zero and at most 3 per second")
    if not 2023 <= args.through_year <= datetime.now(timezone.utc).year:
        parser.error("OpenF1 through-year must be 2023 through current year")
    if not 1950 <= args.calendar_from <= args.through_year:
        parser.error("calendar-from must be 1950 through through-year")
    fetcher = Fetcher(args.cache_dir.resolve(), args.requests_per_second, args.refresh)
    manifest_path = fetcher.cache / "manifest.json"
    report = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    report.update(imported_at=stamp(), scope="Final classifications and event/session driver metadata only; no telemetry or individual laps", cache_dir=str(fetcher.cache))
    # Write useful session metadata first, while the longer archive pagination runs.
    if args.source in ("all", "openf1"):
        report["openf1"] = import_openf1(fetcher, args.through_year)
        save(fetcher.cache / "openf1-summary.json", report["openf1"])
    if args.source in ("all", "jolpica"):
        report["jolpica"] = import_jolpica(fetcher)
        report["calendars"] = import_calendars(fetcher, range(args.calendar_from, args.through_year + 1))
    if args.source in ("all", "f1db"):
        report["f1db"] = import_f1db(fetcher)
        if args.source == "f1db":
            report["calendars"] = import_calendars(fetcher, range(args.calendar_from, args.through_year + 1))
    report.update(network_requests=fetcher.network_requests, cache_hits=fetcher.cache_hits, finished_at=stamp())
    save(fetcher.cache / "manifest.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
