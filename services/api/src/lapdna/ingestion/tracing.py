"""Pinned archive timing/eligibility joined to the matching OpenF1 session.

This is an explicit composite source, not independent validation: both providers
ultimately use the Formula 1 timing feed. The archive's merged *_tel files are
deliberately never imported as native measurements.
"""
from __future__ import annotations

from datetime import timedelta
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .openf1 import ImportFailure, atomic_json, milliseconds, timestamp, utc_now

ARCHIVE_COMMIT = "d1543a71370d9b617b627319f8ad80b2f85dfd5e"
ARCHIVE_ROOT = f"https://raw.githubusercontent.com/TracingInsights/2024/{ARCHIVE_COMMIT}/Italian%20Grand%20Prix/Qualifying/"
POLICY_VERSION = "openf1-tracing-lap-v1"


def archive_json(cache_dir: Path, name: str, *, opener: Callable = urlopen, sleep: Callable = time.sleep) -> tuple[Any, dict[str, Any]]:
    if name not in ("session_info.json", "drivers.json", "session_laptimes.json", "rcm.json", "corners.json", "weather.json") and not re.fullmatch(r"[A-Z]{3}/laptimes\.json", name):
        raise ImportFailure("archive_path_invalid", "Only reviewed archive metadata and lap timing files may be imported")
    url = ARCHIVE_ROOT + quote(name, safe="/")
    stem = "tracing-" + name.replace("/", "-")
    raw_path, meta_path = cache_dir / stem, cache_dir / (stem + ".meta.json")
    if raw_path.exists() and meta_path.exists():
        raw, meta = raw_path.read_bytes(), json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("source_url") == url and meta.get("sha256") == hashlib.sha256(raw).hexdigest():
            return json.loads(raw), meta
    for attempt in range(3):
        try:
            sleep(.36)
            with opener(Request(url, headers={"User-Agent": "LapDNA/0.1 pinned historical metadata import"}), timeout=45) as response:
                raw = response.read(5 * 1024 * 1024 + 1)
            if len(raw) > 5 * 1024 * 1024:
                raise ImportFailure("archive_too_large", "Pinned metadata resource exceeds the reviewed bound")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ImportFailure("archive_shape_invalid", "Expected a columnar archive metadata object")
            meta = {"source_url": url, "retrieved_at": utc_now(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "archive_commit": ARCHIVE_COMMIT}
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = raw_path.with_suffix(raw_path.suffix + ".tmp")
            try:
                temporary.write_bytes(raw)
                temporary.replace(raw_path)
                atomic_json(meta_path, meta)
            finally:
                temporary.unlink(missing_ok=True)
            return value, meta
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise ImportFailure("archive_http_error", f"Pinned metadata source returned HTTP {exc.code}") from None
            sleep(2 ** (attempt + 1))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise ImportFailure("archive_unreachable", "Pinned metadata request failed after bounded retries") from None
            sleep(2 ** (attempt + 1))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ImportFailure("archive_invalid_json", "Pinned metadata source returned invalid JSON") from None
    raise AssertionError("unreachable")


def nullable(value: Any) -> Any:
    return None if value is None or value == "None" or value == "NaT" else value


def column_rows(columns: dict[str, Any]) -> list[dict[str, Any]]:
    required = {"lap", "dNum", "drv", "time", "s1", "s2", "s3", "lST", "sesT", "qs", "del", "ff1G", "iacc", "pin", "pout", "status", "compound", "life"}
    if not required.issubset(columns) or not isinstance(columns.get("lap"), list):
        raise ImportFailure("archive_laps_invalid", "Pinned lap archive has no lap-number array")
    count = len(columns["lap"])
    for name, values in columns.items():
        if not isinstance(values, list) or len(values) != count:
            raise ImportFailure("archive_columns_invalid", f"Pinned lap archive has inconsistent {name} column length")
    return [{name: nullable(values[index]) for name, values in columns.items()} for index in range(count)]


def combine_laps(open_laps: list[dict[str, Any]], drivers: list[dict[str, Any]], archive_laps: dict[str, dict[str, Any]], session_info: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    info = session_info.get("session_info", {})
    if info.get("Key") != 9586 or info.get("Meeting", {}).get("Key") != 1244 or info.get("Path") != "2024/2024-09-01_Italian_Grand_Prix/2024-08-31_Qualifying/":
        raise ImportFailure("archive_session_mismatch", "Pinned metadata does not match Monza 2024 qualifying")
    t0 = timestamp(session_info.get("t0_date"))
    if t0 is None:
        raise ImportFailure("archive_clock_missing", "Pinned metadata has no valid session clock origin")
    lookup = {(str(lap["driver_number"]), lap["lap_number"]): lap for lap in open_laps}
    if len(lookup) != len(open_laps):
        raise ImportFailure("duplicate_lap_identity", "OpenF1 contains duplicate driver/lap identities")
    result, offsets, identity_records = [], [], []
    archive_keys = set()
    for driver in drivers:
        number, code = str(driver["driver_number"]), driver["name_acronym"]
        if code not in archive_laps:
            raise ImportFailure("archive_driver_missing", f"Pinned timing archive has no {code} lap record")
        for row in column_rows(archive_laps[code]):
            key = (number, row["lap"])
            if key in archive_keys or str(row.get("dNum")) != number or row.get("drv") != code or key not in lookup:
                raise ImportFailure("archive_lap_mismatch", "Source driver/lap identity sets do not agree")
            archive_keys.add(key)
            original = lookup[key]
            duration = milliseconds(row.get("time"))
            sectors = [milliseconds(row.get("s" + str(index))) for index in (1, 2, 3)]
            equal_duration = duration is None or duration == original["lap_time_ms"]
            equal_sectors = all(value is None or value == original["sector_times_ms"][index] for index, value in enumerate(sectors))
            if not equal_duration or not equal_sectors:
                raise ImportFailure("source_timing_mismatch", f"Source timing disagrees for driver {number} lap {row['lap']}")
            start_clock, end_clock = row.get("lST"), row.get("sesT")
            start = t0 + timedelta(seconds=start_clock) if isinstance(start_clock, (int, float)) else None
            end = t0 + timedelta(seconds=end_clock) if isinstance(end_clock, (int, float)) else None
            approximate = timestamp(original.get("date_start"))
            offset = round((approximate - start).total_seconds() * 1000, 3) if approximate and start else None
            if offset is not None and duration is not None and original.get("is_pit_out_lap") is False:
                offsets.append(offset)
            reasons = []
            if duration is None or any(value is None for value in sectors): reasons.append("recorded_timing_incomplete")
            if start is None or end is None: reasons.append("timing_clock_missing")
            if duration is not None and start and end and abs((end - start).total_seconds() * 1000 - duration) > 5: reasons.append("native_timing_duration_mismatch")
            if duration and all(value is not None for value in sectors) and abs(sum(sectors) - duration) > 5: reasons.append("sector_sum_mismatch")
            if row.get("del") is not False: reasons.append("lap_deleted_or_unknown")
            deletion = original["source_flags"].get("deletion_evidence")
            if isinstance(deletion, dict) and deletion.get("deleted") is True: reasons.append("lap_deleted")
            if row.get("ff1G") is not False: reasons.append("generated_lap_or_unknown")
            if row.get("iacc") is not True: reasons.append("timing_accuracy_flag_failed_or_unknown")
            if row.get("pout") is not None: reasons.append("pit_out_lap")
            if row.get("pin") is not None: reasons.append("pit_in_lap")
            if row.get("qs") not in ("Q1", "Q2", "Q3"): reasons.append("phase_unknown")
            if row.get("status") != "1": reasons.append("track_status_not_green_or_unknown")
            if row.get("compound") not in ("SOFT", "MEDIUM", "HARD"): reasons.append("dry_compound_unverified")
            if "dry_weather_unverified" in original["exclusion_reasons"]: reasons.append("dry_weather_unverified")
            crossings = [t0 + timedelta(seconds=value) if isinstance((value := row.get(f"s{index}T")), (int, float)) else None for index in (1, 2, 3)]
            result.append({**original, "phase": row.get("qs"), "lap_time_ms": duration, "sector_times_ms": sectors, "lap_start_utc": start.isoformat() if start else None, "lap_end_utc": end.isoformat() if end else None,
                "sector_crossing_utc": [value.isoformat() if value else None for value in crossings],
                "session_start_ms": round(start_clock * 1000) if isinstance(start_clock, (int, float)) else None,
                "session_end_ms": round(end_clock * 1000) if isinstance(end_clock, (int, float)) else None,
                "source_start_utc_approximate": original.get("date_start"), "source_start_offset_ms": offset,
                "timing_edge_basis": "Pinned TracingInsights/FastF1 session clock (t0_date + LapStartTime/Time); source-native OpenF1 car/location UTC",
                "compound": row.get("compound"), "tyre_life_laps": row.get("life"), "stint_number": row.get("stint"),
                "source_flags": {"FastF1Generated": row.get("ff1G"), "IsAccurate": row.get("iacc"), "Deleted": row.get("del"), "DeletedReason": row.get("delR"), "TrackStatus": row.get("status"), "PitInTime": row.get("pin"), "PitOutTime": row.get("pout"), "deletion_evidence": original["source_flags"].get("deletion_evidence")},
                "archive_lap_fields": row, "eligibility_policy": POLICY_VERSION, "timing_candidate": not reasons, "exclusion_reasons": sorted(set(reasons))})
            identity_records.append({"driver_number": number, "lap_number": row["lap"], "duration_verified": duration is not None, "sectors_verified": all(value is not None for value in sectors)})
    if archive_keys != set(lookup):
        raise ImportFailure("archive_inventory_mismatch", "Sources do not contain the same complete driver/lap inventory")
    report = {"session_identity_verified": True, "driver_lap_identity_count": len(archive_keys), "all_available_archive_durations_and_sectors_match_openf1": True,
        "timed_laps_verified": sum(record["duration_verified"] and record["sectors_verified"] for record in identity_records),
        "clock_origin_utc": t0.isoformat(), "openf1_approximate_start_minus_archive_clock_ms": {"count": len(offsets), "min": min(offsets) if offsets else None, "max": max(offsets) if offsets else None, "mean": round(sum(offsets) / len(offsets), 3) if offsets else None},
        "independent_validation": False, "reason": "Both providers derive from the Formula 1 timing feed; timing/clock identity checks do not establish independent physical telemetry accuracy"}
    return sorted(result, key=lambda lap: (int(lap["driver_number"]), lap["lap_number"])), report


def enrich_snapshot(snapshot_path: Path, cache_dir: Path, *, progress: Callable[[str], None] = print) -> Path:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    records = []
    info, meta = archive_json(cache_dir / "source", "session_info.json")
    records.append(meta)
    archive_laps = {}
    for driver in snapshot["drivers"]:
        code = driver["name_acronym"]
        archive_laps[code], meta = archive_json(cache_dir / "source", f"{code}/laptimes.json")
        records.append(meta)
        progress(f"Matched pinned timing metadata for {code}")
    laps, reconciliation = combine_laps(snapshot["laps"], snapshot["drivers"], archive_laps, info)
    snapshot["source"] = "openf1_tracinginsights"
    snapshot["laps"] = laps
    provenance = snapshot["provenance"]
    provenance.update({"source": "openf1_tracinginsights", "eligibility_policy": POLICY_VERSION, "archive_commit": ARCHIVE_COMMIT,
        "source_components": {"car_and_position": "OpenF1 unmodified API records with field presence and invalid-value masking", "timing_phase_and_eligibility": "TracingInsights archived FastF1 lap fields", "markers": "MultiViewer 2024 circuit annotations"},
        "source_records": sorted(provenance["source_records"] + records, key=lambda record: record["source_url"]),
        "timing_candidates": sum(lap["timing_candidate"] for lap in laps), "source_reconciliation": reconciliation,
        "limitations": ["Composite source: matching archived FastF1 lap clocks/flags and native OpenF1 car/location; both share an upstream timing family", "Archive FastF1 software version is not published with these records", "OpenF1 native source records contain invalid/sentinel fields; downstream masks remain mandatory", "Position coordinates support an approximate drawing; no surveyed physical car-line claim", "Publication still requires native support, geometry and timing quality gates"]})
    fingerprint = hashlib.sha256(json.dumps({"policy": POLICY_VERSION, "snapshot_schema": "1.0.0", "inputs": [(record["source_url"], record["sha256"]) for record in provenance["source_records"]]}, separators=(",", ":")).encode()).hexdigest()
    provenance["source_digest"] = fingerprint
    target = cache_dir / "snapshots" / fingerprint[:24] / "snapshot.json"
    if not target.exists():
        atomic_json(target, snapshot)
        atomic_json(target.parent / "manifest.json", provenance)
    atomic_json(cache_dir / "snapshot-pointer.json", {"source_digest": fingerprint, "snapshot_path": str(target.resolve())})
    metadata = {key: value for key, value in snapshot.items() if key not in ("car_data", "position_data")}
    metadata.update({"car_data": {}, "position_data": {}})
    atomic_json(cache_dir / "metadata-snapshot.json", metadata)
    progress(f"Verified composite snapshot: {target}; {len(laps)} actual laps / {provenance['timing_candidates']} timing candidates")
    return target
