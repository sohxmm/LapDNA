"""Resumable historical OpenF1 import with unmodified source records.

The adapter keeps field presence rather than coercing missing car channels to
zero. The eligibility policy below is specific to OpenF1; it does not invent
FastF1's accuracy/deletion/generated flags. Analytical quality is a later gate.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.openf1.org/v1"
MAX_SOURCE_BYTES = 128 * 1024 * 1024
POLICY_VERSION = "openf1-lap-v1"
METADATA_ENDPOINTS = ("sessions", "drivers", "laps", "stints", "race_control", "weather", "pit", "session_result")
CAR_FIELDS = ("speed", "throttle", "n_gear", "brake", "rpm", "drs")


class ImportFailure(RuntimeError):
    """A sanitized source/import failure with an operator-useful category."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def milliseconds(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return None
    return round(value * 1000)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(value, separators=(",", ":"), allow_nan=False), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


class OpenF1Client:
    """Small bounded client; matching, hashed cache hits make no requests."""

    def __init__(self, cache_dir: Path, *, refresh: bool = False, opener: Callable = urlopen, sleep: Callable = time.sleep):
        self.cache_dir = cache_dir
        self.refresh = refresh
        self.opener = opener
        self.sleep = sleep
        self.records: list[dict[str, Any]] = []
        self.requests = 0
        self.cache_hits = 0
        cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, endpoint: str, session_key: int, driver_number: int | None = None, *, start: datetime | None = None, end: datetime | None = None) -> list[dict[str, Any]]:
        if endpoint not in (*METADATA_ENDPOINTS, "car_data", "location"):
            raise ImportFailure("invalid_endpoint", "Only the reviewed OpenF1 source endpoints are supported")
        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        if start is not None:
            params["date>"] = start.isoformat()
        if end is not None:
            params["date<"] = end.isoformat()
        url = BASE_URL + "/" + endpoint + "?" + urlencode(params)
        stem = endpoint + ("-" + str(driver_number) if driver_number is not None else "")
        if start is not None or end is not None:
            stem += "-" + hashlib.sha256(url.encode()).hexdigest()[:16]
        def validate(payload):
            self._validate(payload, session_key, driver_number)
            if start is not None or end is not None:
                for row in payload:
                    when = timestamp(row.get("date"))
                    if when is None or (start is not None and when < start) or (end is not None and when > end):
                        raise ImportFailure("source_filter_mismatch", "Source returned native rows outside the requested UTC interval")
        raw_path, metadata_path = self.cache_dir / (stem + ".json"), self.cache_dir / (stem + ".meta.json")
        if not self.refresh and raw_path.exists() and metadata_path.exists():
            raw = raw_path.read_bytes()
            meta = json.loads(metadata_path.read_text(encoding="utf-8"))
            if meta.get("source_url") == url and meta.get("sha256") == hashlib.sha256(raw).hexdigest():
                payload = json.loads(raw)
                validate(payload)
                self.cache_hits += 1
                self.records.append(meta)
                return payload
        for attempt in range(3):
            try:
                # Historical free tier: at most 30 requests per minute.
                self.sleep(2.05)
                self.requests += 1
                with self.opener(Request(url, headers={"User-Agent": "LapDNA/0.1 historical analysis import", "Accept": "application/json"}), timeout=60) as response:
                    raw = response.read(MAX_SOURCE_BYTES + 1)
                if len(raw) > MAX_SOURCE_BYTES:
                    raise ImportFailure("source_too_large", "Source response exceeds the reviewed file-size bound")
                payload = json.loads(raw)
                validate(payload)
                meta = {"source_url": url, "retrieved_at": utc_now(), "sha256": hashlib.sha256(raw).hexdigest(), "rows": len(payload), "bytes": len(raw)}
                temporary = raw_path.with_suffix(".json.tmp")
                try:
                    temporary.write_bytes(raw)
                    temporary.replace(raw_path)
                    atomic_json(metadata_path, meta)
                finally:
                    temporary.unlink(missing_ok=True)
                self.records.append(meta)
                return payload
            except HTTPError as exc:
                if exc.code in (401, 403):
                    raise ImportFailure("access_required", f"OpenF1 denied historical access with HTTP {exc.code}") from None
                if exc.code == 404:
                    raise ImportFailure("source_missing", "The requested historical source resource was not found") from None
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise ImportFailure("source_http_error", f"Historical source returned HTTP {exc.code}") from None
                retry = exc.headers.get("Retry-After", "")
                delay = float(retry) if re.fullmatch(r"\d+(?:\.\d+)?", retry) else 2 ** (attempt + 1)
                if delay > 45:
                    raise ImportFailure("retry_later", "Source requested a long retry window; cached progress is retained") from None
                self.sleep(delay)
            except (URLError, TimeoutError) as exc:
                if attempt == 2:
                    raise ImportFailure("source_unreachable", "Historical source request failed after bounded retries") from exc
                self.sleep(2 ** (attempt + 1))
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ImportFailure("invalid_source_json", "Historical source returned invalid JSON") from None
        raise AssertionError("unreachable")

    @staticmethod
    def _validate(payload: Any, session_key: int, driver_number: int | None) -> None:
        if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
            raise ImportFailure("invalid_source_shape", "Expected a list of source records")
        for row in payload:
            if row.get("session_key") != session_key:
                raise ImportFailure("foreign_session", "Source response contains an unexpected session")
            if driver_number is not None and row.get("driver_number") != driver_number:
                raise ImportFailure("foreign_driver", "Source response contains an unexpected driver")


def phase_windows(control: list[dict[str, Any]]) -> list[dict[str, Any]]:
    windows = []
    for phase in (1, 2, 3):
        starts = [timestamp(row.get("date")) for row in control if row.get("qualifying_phase") == phase and (row.get("message") == "SESSION STARTED" or row.get("message") == "GREEN LIGHT - PIT EXIT OPEN")]
        finishes = [timestamp(row.get("date")) for row in control if row.get("qualifying_phase") == phase and row.get("message") == "SESSION FINISHED"]
        starts, finishes = [value for value in starts if value], [value for value in finishes if value]
        if not starts or not finishes:
            raise ImportFailure("phase_unavailable", f"No complete source status boundaries for Q{phase}")
        windows.append({"phase": f"Q{phase}", "start_utc": min(starts).isoformat(), "chequered_utc": max(finishes).isoformat()})
    return windows


def deletion_records(control: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    records = {}
    for row in sorted(control, key=lambda item: item.get("date", "")):
        message = row.get("message", "")
        car, lap = re.search(r"\bCAR (\d+)\b", message), re.search(r"\bLAP (\d+)\b", message)
        if car and lap and ("DELETED" in message or "REINSTATED" in message):
            records[(int(car[1]), int(lap[1]))] = {"deleted": "REINSTATED" not in message, "message": message, "date": row.get("date")}
    return records


def caution_intervals(control: list[dict[str, Any]]) -> list[tuple[datetime, datetime | None]]:
    open_flags: dict[tuple[Any, Any], datetime] = {}
    intervals = []
    for row in sorted(control, key=lambda item: item.get("date", "")):
        when = timestamp(row.get("date"))
        if when is None:
            continue
        key = (row.get("scope"), row.get("sector"))
        if row.get("flag") in ("YELLOW", "DOUBLE YELLOW", "RED", "VSC", "SAFETY CAR"):
            open_flags.setdefault(key, when)
        elif row.get("flag") in ("CLEAR", "GREEN"):
            if row.get("scope") == "Track":
                for start in open_flags.values():
                    intervals.append((start, when))
                open_flags.clear()
            elif key in open_flags:
                intervals.append((open_flags.pop(key), when))
    intervals.extend((start, None) for start in open_flags.values())
    return intervals


def normalize_laps(raw_laps: list[dict[str, Any]], control: list[dict[str, Any]], stints: list[dict[str, Any]], weather: list[dict[str, Any]], session_key: int) -> list[dict[str, Any]]:
    windows, deleted, cautions = phase_windows(control), deletion_records(control), caution_intervals(control)
    result = []
    by_driver: dict[int, list[dict[str, Any]]] = {}
    for lap in raw_laps:
        by_driver.setdefault(lap["driver_number"], []).append(lap)
    for number, source_laps in by_driver.items():
        source_laps.sort(key=lambda lap: lap["lap_number"])
        for index, lap in enumerate(source_laps):
            start = timestamp(lap.get("date_start"))
            duration = milliseconds(lap.get("lap_duration"))
            end = start + timedelta(milliseconds=duration) if start and duration else None
            sectors = [milliseconds(lap.get(f"duration_sector_{sector}")) for sector in (1, 2, 3)]
            phase = next((window["phase"] for window in reversed(windows) if start and start >= timestamp(window["start_utc"])), None)
            tyre = next((stint for stint in stints if stint.get("driver_number") == number and stint.get("lap_start", 0) <= lap["lap_number"] <= stint.get("lap_end", -1)), None)
            deletion = deleted.get((number, lap["lap_number"]))
            pit_in = any(2064 in (lap.get(f"segments_sector_{sector}") or []) for sector in (1, 2, 3)) and not lap.get("is_pit_out_lap")
            reasons = []
            if start is None: reasons.append("lap_start_missing")
            if duration is None or any(value is None for value in sectors): reasons.append("recorded_timing_incomplete")
            if duration and all(value is not None for value in sectors) and abs(sum(sectors) - duration) > 5: reasons.append("sector_sum_mismatch")
            if lap.get("is_pit_out_lap") is not False: reasons.append("pit_out_or_unknown")
            if pit_in: reasons.append("pit_lane_segment")
            if phase is None: reasons.append("phase_unknown")
            if deletion and deletion["deleted"]: reasons.append("lap_deleted")
            if start and end and any(start < (finish or datetime.max.replace(tzinfo=timezone.utc)) and end > begin for begin, finish in cautions): reasons.append("caution_during_lap")
            if not tyre or tyre.get("compound") not in ("SOFT", "MEDIUM", "HARD"): reasons.append("dry_compound_unverified")
            rain = [row for row in weather if start and end and (when := timestamp(row.get("date"))) and start - timedelta(seconds=90) <= when <= end + timedelta(seconds=90)]
            if not rain or any(row.get("rainfall") not in (0, False) for row in rain): reasons.append("dry_weather_unverified")
            result.append({**lap, "lap_id": f"openf1_{session_key}_{number}_{lap['lap_number']}", "driver_number": str(number), "phase": phase, "lap_time_ms": duration, "sector_times_ms": sectors,
                "lap_start_utc": start.isoformat() if start else None, "lap_end_utc": end.isoformat() if end else None,
                "next_lap_start_utc": source_laps[index + 1].get("date_start") if index + 1 < len(source_laps) else None,
                "timing_edge_basis": "OpenF1 approximate date_start plus recorded lap_duration; imposed endpoint",
                "compound": tyre.get("compound") if tyre else None, "stint_number": tyre.get("stint_number") if tyre else None,
                "tyre_life_laps": tyre.get("tyre_age_at_start", 0) + lap["lap_number"] - tyre.get("lap_start", lap["lap_number"]) + 1 if tyre else None,
                "source_flags": {"FastF1Generated": None, "IsAccurate": None, "Deleted": deletion["deleted"] if deletion else None, "deletion_evidence": deletion},
                "eligibility_policy": POLICY_VERSION, "timing_candidate": not reasons, "exclusion_reasons": reasons})
    return sorted(result, key=lambda lap: (int(lap["driver_number"]), lap["lap_number"]))


def channel_statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    present = Counter()
    invalid = Counter()
    missing = Counter()
    for row in rows:
        for field in CAR_FIELDS:
            if field not in row or row[field] is None:
                missing[field] += 1
                continue
            present[field] += 1
            value = row[field]
            numeric = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
            valid = numeric and (0 <= value <= 400 if field == "speed" else 0 <= value <= 100 if field == "throttle" else value in range(9) if field == "n_gear" else value in (0, 100) if field == "brake" else value >= 0)
            if not valid: invalid[field] += 1
    return {"rows": len(rows), "present": dict(present), "missing": dict(missing), "invalid": dict(invalid), "values_are_unmodified_source_records": True}


def fetch_markers(cache_dir: Path, *, refresh: bool = False, circuit_key: int = 39, year: int = 2024, turn_count: int = 11) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch the reviewed Monza layout annotations, separately from telemetry."""
    url = f"https://api.multiviewer.app/api/v1/circuits/{circuit_key}/{year}"
    path, meta_path = cache_dir / "markers.json", cache_dir / "markers.meta.json"
    if not refresh and path.exists() and meta_path.exists():
        raw, meta = path.read_bytes(), json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("source_url") == url and meta.get("sha256") == hashlib.sha256(raw).hexdigest():
            return json.loads(raw), meta
    try:
        with urlopen(Request(url, headers={"User-Agent": "LapDNA/0.1 reviewed circuit annotation import"}), timeout=30) as response:
            raw = response.read(1024 * 1024 + 1)
    except HTTPError as exc:
        raise ImportFailure("markers_http_error", f"Circuit annotation source returned HTTP {exc.code}") from None
    except (URLError, TimeoutError):
        raise ImportFailure("markers_unreachable", "Circuit annotation request failed") from None
    if len(raw) > 1024 * 1024:
        raise ImportFailure("markers_too_large", "Circuit annotation source exceeds the reviewed bound")
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ImportFailure("markers_invalid", "Circuit annotation source returned invalid JSON") from None
    if not isinstance(value, dict) or sorted({row.get("number") for row in value.get("corners", [])}) != list(range(1, turn_count + 1)):
        raise ImportFailure("markers_invalid", "Circuit annotation source does not contain the expected complete turn numbers")
    meta = {"source_url": url, "retrieved_at": utc_now(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "rows": len(value["corners"]), "role": "reference_annotations", "units": "source coordinates; no surveyed physical distance guarantee"}
    temporary = path.with_suffix(".json.tmp")
    try:
        temporary.write_bytes(raw)
        temporary.replace(path)
        atomic_json(meta_path, meta)
    finally:
        temporary.unlink(missing_ok=True)
    return value, meta


def import_session(cache_dir: Path, *, year: int = 2024, round_number: int = 16, session_key: int = 9586, expected_circuit: str = "Monza", refresh: bool = False, progress: Callable[[str], None] = print, spec: dict | None = None, bulk: bool = False) -> Path:
    if spec is not None:
        year, round_number, session_key, expected_circuit = spec["year"], spec["round"], spec["session_key"], spec["circuit_short_name"]
    elif (year, round_number, session_key, expected_circuit) != (2024, 16, 9586, "Monza"):
        raise ImportFailure("unreviewed_session", "This reviewed pilot imports only 2024 round 16 Monza qualifying, source session 9586")
    client = OpenF1Client(cache_dir / "source", refresh=refresh)
    metadata = {endpoint: client.fetch(endpoint, session_key) for endpoint in METADATA_ENDPOINTS}
    if len(metadata["sessions"]) != 1:
        raise ImportFailure("session_ambiguous", "Source did not resolve exactly one session")
    session = metadata["sessions"][0]
    if session.get("year") != year or session.get("circuit_short_name") != expected_circuit or session.get("session_name") not in ("Qualifying", "Sprint Qualifying", "Sprint Shootout") or session.get("is_cancelled") is not False:
        raise ImportFailure("session_mismatch", "Resolved session does not match the reviewed event specification")
    if spec and (session.get("meeting_key") != spec["meeting_key"] or session.get("circuit_key") != spec["circuit_key"] or session.get("date_start", "")[:10] != spec["qualifying_date"]):
        raise ImportFailure("session_mismatch", "Resolved meeting, layout or date disagrees with the pinned specification")
    phase_windows(metadata["race_control"])
    drivers = metadata["drivers"]
    if not drivers or len({driver["driver_number"] for driver in drivers}) != len(drivers):
        raise ImportFailure("roster_invalid", "Source roster is empty or duplicated")
    car_data, position_data = {}, {}
    if bulk:
        roster = {str(driver["driver_number"]) for driver in drivers}
        edges = [(timestamp(row.get("date_start")), milliseconds(row.get("lap_duration"))) for row in metadata["laps"]]
        starts = [start for start, _ in edges if start is not None]
        ends = [start + timedelta(milliseconds=duration) for start, duration in edges if start is not None and duration is not None]
        if not starts or not ends:
            raise ImportFailure("native_window_missing", "Source lap timing cannot bound a historical native-stream request")
        first, last = min(starts) - timedelta(seconds=5), max(ends) + timedelta(seconds=5)
        if not timedelta(0) < last - first <= timedelta(hours=5):
            raise ImportFailure("native_window_invalid", "Historical native-stream UTC window exceeds the reviewed bound")
        for endpoint, target in (("car_data", car_data), ("location", position_data)):
            # Whole-session OpenF1 requests can reject excessive row counts.
            # Half-open ten-minute windows retain every returned native row
            # without boundary duplication or signal resampling.
            cursor, count = first, 0
            while cursor < last:
                stop = min(last, cursor + timedelta(minutes=10))
                # Overlap queries to tolerate inclusive/exclusive provider
                # bounds, then partition locally into exact half-open bins.
                rows = client.fetch(endpoint, session_key, start=cursor - timedelta(seconds=1), end=stop + timedelta(seconds=1))
                records = [row for row in rows if cursor <= timestamp(row["date"]) < stop]
                for row in records:
                    number = str(row.get("driver_number"))
                    if number not in roster:
                        raise ImportFailure("foreign_driver", "Native stream contains a driver absent from the verified session roster")
                    target.setdefault(number, []).append(row)
                count += len(records)
                cursor = stop
                progress(f"Imported {endpoint} through {stop.isoformat()} ({count} native records)")
            for number in roster:
                target.setdefault(number, [])
            progress(f"Imported {count} native {endpoint} records for {len(roster)} source drivers")
    for driver in ([] if bulk else sorted(drivers, key=lambda row: row["driver_number"])):
        number = driver["driver_number"]
        car_data[str(number)] = client.fetch("car_data", session_key, number)
        position_data[str(number)] = client.fetch("location", session_key, number)
        progress(f"Imported {driver.get('name_acronym', number)}: {len(car_data[str(number)])} car / {len(position_data[str(number)])} position records")
        atomic_json(cache_dir / "acquisition-progress.json", {"session_key": session_key, "retrieved_at": utc_now(), "complete_drivers": list(car_data), "source_records": client.records})
    normalized_laps = normalize_laps(metadata["laps"], metadata["race_control"], metadata["stints"], metadata["weather"], session_key)
    markers, marker_meta = fetch_markers(cache_dir / "source", refresh=refresh, **({"circuit_key": spec["circuit_key"], "year": year, "turn_count": spec["turn_count"]} if spec else {}))
    client.records.append(marker_meta)
    manifest = {"schema_version": "1.0.0", "source": "openf1", "source_session": str(session_key), "year": year, "round": round_number, "circuit": expected_circuit, "retrieved_at": utc_now(),
        "eligibility_policy": POLICY_VERSION, "source_records": sorted(client.records, key=lambda record: record["source_url"]), "driver_count": len(drivers), "lap_count": len(normalized_laps), "timing_candidates": sum(lap["timing_candidate"] for lap in normalized_laps),
        "car_data": {number: channel_statistics(rows) for number, rows in car_data.items()}, "position_counts": {number: len(rows) for number, rows in position_data.items()},
        "native_channel_units": {"speed": "km/h", "throttle": "%", "n_gear": "integer", "brake": "0/100 binary; other raw values unavailable", "rpm": "rev/min", "drs": "raw code"},
        "position_units": "source coordinates; coordinate scale requires geometry verification", "phase_windows": phase_windows(metadata["race_control"]),
        "limitations": ["OpenF1 date_start is approximate; endpoint timestamps are imposed from recorded durations", "FastF1-specific flags are unavailable in OpenF1 and are never assumed false", "Native car/location records retain unknown/sentinel values for downstream masking", "Timing candidates are not proof that later spatial/timing quality gates passed"]}
    fingerprint = hashlib.sha256(json.dumps({"policy": POLICY_VERSION, "snapshot_schema": "1.0.0", "import_spec": spec, "inputs": [(record["source_url"], record["sha256"]) for record in manifest["source_records"]]}, separators=(",", ":")).encode()).hexdigest()
    manifest["source_digest"] = fingerprint
    snapshot = {"schema_version": "1.0.0", "source": "openf1", "session": {**session, "round": round_number, "event_name": "Italian Grand Prix" if expected_circuit == "Monza" else expected_circuit}, "drivers": drivers, "laps": normalized_laps,
        "car_data": car_data, "position_data": position_data, "race_control": metadata["race_control"], "weather": metadata["weather"], "stints": metadata["stints"], "pit": metadata["pit"], "session_results": metadata["session_result"], "markers": markers, "provenance": manifest}
    if spec:
        snapshot["import_spec"] = spec
        snapshot["session"]["event_name"] = spec["event_name"]
    revision_dir = cache_dir / "snapshots" / fingerprint[:24]
    snapshot_path = revision_dir / "snapshot.json"
    if not snapshot_path.exists():
        atomic_json(snapshot_path, snapshot)
        atomic_json(revision_dir / "manifest.json", manifest)
    atomic_json(cache_dir / "openf1-snapshot-pointer.json", {"source_digest": fingerprint, "snapshot_path": str(snapshot_path.resolve())})
    progress(f"Snapshot: {snapshot_path} ({client.requests} requests; {client.cache_hits} cache hits)")
    return snapshot_path
