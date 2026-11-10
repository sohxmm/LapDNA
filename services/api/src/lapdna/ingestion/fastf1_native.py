"""Operator-only FastF1 adapter with raw, presence-preserving car/position rows.

FastF1's parsed telemetry can insert zero/False rows. Never normalize those
filled DataFrames: decode the actual compressed source messages instead.
No account credentials or authorization headers are written to the snapshot.
"""

import base64
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from urllib.parse import quote
import zlib

from .openf1 import ImportFailure, atomic_json, timestamp, utc_now

VERSION = "3.9.2"
MAX_RAW_BYTES = 128 * 1024 * 1024
MAX_FRAME_BYTES = 2 * 1024 * 1024
CHANNELS = {"0": "rpm", "2": "speed", "3": "n_gear", "4": "throttle", "5": "brake", "45": "drs"}


def native_resource_urls(path, name, primary, mirror):
    # Requests encodes non-ASCII event names before sending. Pin the same
    # encoded resource identity before verifying a returned response URL.
    encoded = quote(path, safe="/%")
    return (primary + encoded + name, mirror + encoded + name)


def provider_session_identifier(year, session_type):
    # FastF1 distinguishes 2023's Sprint Shootout (SS) from the later Sprint
    # Qualifying (SQ). LapDNA's external SQ format keeps actual SQ1/2/3 phases.
    return "SS" if year == 2023 and session_type == "SQ" else session_type


def resource_available(name, status, *, optional=False):
    """Missing context never creates measurements or hides required failures."""
    if status == 200:
        return True
    if status == 401:
        raise ImportFailure("access_required", "The timing source rejected the local sign-in; renew it in your terminal")
    if status == 429:
        raise ImportFailure("rate_limited", "The timing source requested a rate-limit pause; cached progress is retained")
    if optional and name == "WeatherData.jsonStream" and status in (403,404,410,500,502,503,504):
        return False
    raise ImportFailure("fastf1_source_unavailable", f"Required native resource {name} returned HTTP {status if status is not None else 'no response'}")


def stream_records(raw: bytes, *, compressed: bool):
    """Decode JSON messages only; never accept executable or pickle archives."""
    for line in raw.decode("utf-8-sig").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"(\d{2}:\d{2}:\d{2}\.\d{3})(.+)", line)
        if match is None:
            raise ImportFailure("native_frame_invalid", "Native source message lacks its session-clock prefix")
        payload = match[2]
        try:
            if compressed:
                encoded = json.loads(payload)
                if not isinstance(encoded, str):
                    raise ValueError
                decoder = zlib.decompressobj(-zlib.MAX_WBITS)
                body = decoder.decompress(base64.b64decode(encoded, validate=True), MAX_FRAME_BYTES + 1)
                if len(body) > MAX_FRAME_BYTES or not decoder.eof or decoder.unused_data:
                    raise ImportFailure("native_frame_too_large", "Native compressed message exceeds the decoding bound")
                value = json.loads(body.decode("utf-8-sig"))
            else:
                if len(payload) > MAX_FRAME_BYTES:
                    raise ImportFailure("native_frame_too_large", "Native metadata message exceeds the decoding bound")
                value = json.loads(payload)
            if not isinstance(value, dict):
                raise ValueError
        except (ValueError, TypeError, zlib.error, UnicodeDecodeError) as exc:
            raise ImportFailure("native_frame_invalid", "Native source message is not valid bounded JSON") from exc
        yield match[1], value


def native_rows(raw: bytes, kind: str):
    output = {}
    if kind not in ("car", "position"):
        raise ValueError("unknown native stream")
    for _, value in stream_records(raw, compressed=True):
        entries = value.get("Entries" if kind == "car" else "Position")
        if not isinstance(entries, list):
            raise ImportFailure("native_shape_invalid", "Native stream has no sample array")
        for entry in entries:
            when = timestamp(entry.get("Utc" if kind == "car" else "Timestamp"))
            drivers = entry.get("Cars" if kind == "car" else "Entries")
            if when is None or not isinstance(drivers, dict):
                raise ImportFailure("native_shape_invalid", "Native sample has no UTC or driver mapping")
            for number, sample in drivers.items():
                if not re.fullmatch(r"[0-9]{1,3}", number) or not isinstance(sample, dict):
                    raise ImportFailure("native_driver_invalid", "Native stream has an invalid driver identity")
                row = {"date": when.isoformat()}
                if kind == "car":
                    channels = sample.get("Channels")
                    if not isinstance(channels, dict):
                        raise ImportFailure("native_channels_invalid", "Native car sample has no channel mapping")
                    row.update({name: channels[key] for key, name in CHANNELS.items() if key in channels})
                else:
                    row.update({key.lower(): sample[key] for key in ("X", "Y", "Z", "Status") if key in sample})
                output.setdefault(number, []).append(row)
    for rows in output.values():
        rows.sort(key=lambda row: row["date"])
    return output


def lap_window_rows(stream, roster, start, end):
    """Keep native samples around actual lap clocks, rejecting in-window aliens.

    Some archives begin with a stale previous-series message. Five seconds
    of padding preserve interpolation support outside the first/last lap.
    Source bytes remain in the private cache; clipping never edits samples.
    """
    lower, upper = timestamp(start) - timedelta(seconds=5), timestamp(end) + timedelta(seconds=5)
    retained = {number: [row for row in rows if lower <= timestamp(row["date"]) <= upper]
                for number, rows in stream.items()}
    retained = {number: rows for number, rows in retained.items() if rows}
    if set(retained) - roster:
        raise ImportFailure("foreign_driver", "Native stream contains an unknown driver inside the actual lap-clock window")
    return retained, sum(map(len, stream.values())) - sum(map(len, retained.values()))


def quarantine_unrostered(stream, roster, lap_drivers):
    """Exclude unassigned streams, never create drivers from car-number keys.

    The source DriverList and every parsed timing-lap identity must agree.
    Extra streams without any timing identity are retained only in the raw
    cache and provenance counts (e.g. the withdrawn car in Australia 2024).
    """
    if not lap_drivers <= roster:
        raise ImportFailure("foreign_driver", "Actual lap timing includes a driver outside the source roster")
    extra = {number:len(rows) for number, rows in stream.items() if number not in roster}
    return {number:rows for number, rows in stream.items() if number in roster}, extra


def import_fastf1_session(cache: Path, year: int, round_number: int, *, progress=print, refresh: bool = False, session_type: str = "Q") -> Path:
    if not 2018 <= year <= 2026 or not 1 <= round_number <= 30:
        raise ImportFailure("unsupported_session", "Detailed native imports are limited to 2018–2026 qualifying")
    if session_type not in ("Q", "SQ") or session_type == "SQ" and year < 2023:
        raise ImportFailure("unsupported_session", "Native Sprint Qualifying uses actual 2023-onward sessions; earlier sprint race formats are not SQ")
    pointer = cache / "snapshot-pointer.json"
    if pointer.exists() and not refresh:
        previous = Path(json.loads(pointer.read_text(encoding="utf-8"))["snapshot_path"])
        if previous.is_file():
            snapshot = json.loads(previous.read_text(encoding="utf-8"))
            identity, source = snapshot.get("session", {}), snapshot.get("provenance", {})
            if (snapshot.get("source") == "fastf1" and identity.get("year") == year and identity.get("round") == round_number
                    and identity.get("session_type", "Q") == session_type
                    and source.get("fastf1_version") == VERSION and source.get("native_mask_policy") == "raw-presence-v1"):
                progress("Reusing the complete primary native snapshot; no sign-in or source request required")
                return previous
    try:
        import fastf1
        import pandas as pd
        from fastf1 import _api
        from fastf1.internals.f1account import token_manager
        from fastf1.req import Cache
    except ImportError as exc:
        raise ImportFailure("data_dependencies_missing", "Install the API data dependencies before using the FastF1 operator adapter") from exc
    if fastf1.__version__ != VERSION:
        raise ImportFailure("unreviewed_library", f"This native adapter requires FastF1 {VERSION}")
    fastf1.set_log_level("WARNING")
    from .budget import install_fastf1_budget
    budget = install_fastf1_budget()
    # Check status without printing token contents/claims or launching login.
    token = token_manager.get_stored()
    if token is None or not token.is_valid():
        raise ImportFailure("access_required", "Sign in locally first: python -m fastf1 auth f1tv --authenticate. Do not put credentials in chat or repository files.")
    # The pinned transport otherwise starts an interactive password prompt
    # when a token is revoked mid-batch. Operator jobs must stop instead.
    def require_local_sign_in():
        raise ImportFailure("access_required", "The Formula 1 sign-in needs renewal in your local terminal; completed imports are retained")
    token_manager._default_auth_func = require_local_sign_in
    (cache / "library").mkdir(parents=True, exist_ok=True)
    Cache.configure(cache_dir=str(cache / "library"), force_renew=refresh)
    records, unavailable = [], []

    def raw_resource(name, *, optional=False):
        # Follow the pinned library's own native-resource fallback. Its parser
        # may already have obtained timing from the mirror while the primary
        # returns AccessDenied; requesting only the primary discards real data.
        urls = native_resource_urls(session.api_path,name,_api.base_url,_api.base_url_mirror)
        path, metadata_path = cache / "source" / name, cache / "source" / (name + ".meta.json")
        if path.exists() and metadata_path.exists() and not refresh:
            raw, meta = path.read_bytes(), json.loads(metadata_path.read_text(encoding="utf-8"))
            if meta.get("source_url") in urls and meta.get("sha256") == sha256(raw).hexdigest():
                records.append(meta)
                return raw
        response = Cache.requests_get(urls, headers=_api.headers, timeout=60)
        status = None if response is None else response.status_code
        if not resource_available(name, status, optional=optional):
            unavailable.append({"source_urls":list(urls),"resource":name,"http_status":status,"retrieved_at":utc_now()})
            return None
        url = response.url
        if url not in urls:
            raise ImportFailure("unexpected_resource_origin", "Native response left the pinned library's declared resource origins")
        raw = response.content
        if len(raw) > MAX_RAW_BYTES:
            raise ImportFailure("source_too_large", "Native resource exceeds the reviewed import bound")
        meta = {"source_url": url, "retrieved_at": utc_now(), "sha256": sha256(raw).hexdigest(), "bytes": len(raw), "library_version": VERSION}
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(raw)
        temporary.replace(path)
        atomic_json(metadata_path, meta)
        records.append(meta)
        return raw

    try:
        session = fastf1.get_session(year, round_number, provider_session_identifier(year,session_type))
        expected_names = ("Sprint Qualifying", "Sprint Shootout") if session_type == "SQ" else ("Qualifying",)
        if session.name not in expected_names:
            raise ImportFailure("session_mismatch", "The selected source format does not match the requested qualifying session")
        if int(session.event["RoundNumber"]) != round_number or session.event.year != year or not session.api_path.startswith(f"/static/{year}/"):
            raise ImportFailure("session_mismatch", "FastF1 resolved a different event identity")
        # Library clocks/phases/accuracy checks are retained with their exact
        # version. Its filled car/position arrays are deliberately never used.
        session.load(laps=True, telemetry=True, weather=False, messages=True)
        info = session.session_info
        if not isinstance(info, dict) or not info:
            raise ImportFailure("session_metadata_unavailable", "The source did not load the actual qualifying session metadata")
        if session.t0_date is None or session.laps.empty:
            raise ImportFailure("timing_unavailable", "FastF1 did not establish lap timing and the session UTC origin")
        t0 = pd.Timestamp(session.t0_date)
        t0 = t0.tz_localize("UTC") if t0.tzinfo is None else t0.tz_convert("UTC")
        car = native_rows(raw_resource("CarData.z.jsonStream"), "car")
        positions = native_rows(raw_resource("Position.z.jsonStream"), "position")
        raw_weather = raw_resource("WeatherData.jsonStream", optional=True)
        weather = []
        for clock, value in (stream_records(raw_weather, compressed=False) if raw_weather is not None else ()):
            if value.get("Rainfall") in ("0", "1", 0, 1) and value.get("Rainfall") is not None:
                weather.append({"date": (t0 + pd.Timedelta(clock)).isoformat(), "rainfall": int(value["Rainfall"])})
        # Capture exact primary timing inputs underlying the parsed lap flags.
        for name in ("TimingData.jsonStream", "TimingAppData.jsonStream", "SessionInfo.jsonStream", "SessionStatus.jsonStream", "TrackStatus.jsonStream", "RaceControlMessages.jsonStream", "DriverList.jsonStream"):
            raw_resource(name)
        source_drivers = _api.driver_info(session.api_path)
        if not isinstance(source_drivers, dict) or not source_drivers:
            raise ImportFailure("roster_unavailable", "The source did not establish the actual qualifying driver roster")
    except ImportFailure:
        if budget.status()[1] > 0:
            raise ImportFailure("rate_limited", "The shared historical import window is full; cached progress is retained until the source window resets") from None
        raise
    except Exception as exc:
        from fastf1.exceptions import RateLimitExceededError
        stored = token_manager.get_stored()
        if stored is None or not stored.is_valid():
            raise ImportFailure("access_required", "The Formula 1 sign-in needs renewal in your local terminal; completed imports are retained") from None
        if isinstance(exc, RateLimitExceededError) or budget.status()[1] > 0:
            raise ImportFailure("rate_limited", "FastF1's source rate window is exhausted; keep cached progress and resume after the provider window resets") from None
        # Authentication/network exceptions may contain sensitive request
        # details. Keep operator-facing output deliberately sanitized.
        raise ImportFailure("fastf1_load_failed", "FastF1 could not load the requested session; check local sign-in, upstream availability and the library cache") from None

    calendar = json.loads((Path(__file__).resolve().parents[1] / "calendar_snapshots" / f"{year}.json").read_text(encoding="utf-8"))
    race = next((race for race in calendar["races"] if race["round"] == round_number), None)
    if race is None or race["name"] != str(session.event["EventName"]):
        raise ImportFailure("calendar_identity_mismatch", "Source event name/round does not match the local calendar; review the identity mapping")
    circuit_key = info.get("Meeting", {}).get("Circuit", {}).get("Key")
    marker_url = f"https://api.multiviewer.app/api/v1/circuits/{circuit_key}/{year}" if isinstance(circuit_key,int) else None
    try:
        if marker_url is None:
            raise ValueError("missing circuit annotation identity")
        with urlopen(Request(marker_url, headers={"User-Agent": "LapDNA verified circuit annotations"}), timeout=30) as response:
            marker_bytes = response.read(1024 * 1024 + 1)
        if len(marker_bytes) > 1024 * 1024:
            raise ValueError
        markers = json.loads(marker_bytes)
        numbers = sorted({item["number"] for item in markers["corners"]})
        if not numbers or numbers != list(range(1, max(numbers) + 1)):
            raise ValueError
    except Exception:
        # An absent annotation source must not erase real recorded lap times.
        # Reference construction will withhold spatial output on an empty set.
        markers = {"corners":[]}
        unavailable.append({"source_url":marker_url,"resource":"year/layout turn annotations","retrieved_at":utc_now()})
    else:
        records.append({"source_url": marker_url, "retrieved_at": utc_now(), "sha256": sha256(marker_bytes).hexdigest(), "bytes": len(marker_bytes)})
    drivers = []
    for number, row in source_drivers.items():
        name = row.get("FullName") or " ".join(filter(None, [row.get("FirstName"), row.get("LastName")]))
        if not name or not row.get("Tla"):
            raise ImportFailure("roster_identity_missing", "Source roster lacks a driver's actual name or code")
        drivers.append({"driver_number": int(number), "name_acronym": row["Tla"], "full_name": name,
                        "team_name": row.get("TeamName"), "team_colour": row.get("TeamColour")})
    roster = {str(row["driver_number"]) for row in drivers}

    def scalar(value):
        if value is None or pd.isna(value):
            return None
        return value.item() if hasattr(value, "item") else value

    def ms(value):
        return None if value is None or pd.isna(value) else round(value.total_seconds() * 1000)

    def clock(value):
        return None if value is None or pd.isna(value) else (t0 + value).isoformat()

    phases = {}
    phase_names = ("SQ1", "SQ2", "SQ3") if session_type == "SQ" else ("Q1", "Q2", "Q3")
    try:
        phase_frames = session.laps.split_qualifying_sessions()
    except Exception:
        raise ImportFailure("phase_unavailable", "The source did not establish actual qualifying phase boundaries") from None
    for phase, frame in zip(phase_names, phase_frames):
        if frame is not None:
            for _, row in frame.iterrows():
                phases[(str(row["DriverNumber"]), int(row["LapNumber"]))] = phase
    laps, seen = [], set()
    for _, row in session.laps.iterrows():
        number, lap_number = str(row["DriverNumber"]), int(row["LapNumber"])
        key = (number, lap_number)
        if key in seen or number not in roster:
            raise ImportFailure("lap_identity_invalid", "Source lap identities are duplicated or absent from the roster")
        seen.add(key)
        phase = phases.get(key)
        flags = {name: scalar(row.get(name)) for name in ("Deleted", "IsAccurate", "FastF1Generated", "TrackStatus")}
        duration, sectors = ms(row.get("LapTime")), [ms(row.get(f"Sector{i}Time")) for i in (1, 2, 3)]
        start, end = clock(row.get("LapStartTime")), clock(row.get("Time"))
        reasons = []
        if duration is None or any(value is None for value in sectors) or start is None or end is None:
            reasons.append("native_timing_incomplete")
        elif abs(sum(sectors) - duration) > 5 or abs((timestamp(end) - timestamp(start)).total_seconds() * 1000 - duration) > 5:
            reasons.append("native_timing_inconsistent")
        for name, expected in (("Deleted", False), ("FastF1Generated", False), ("IsAccurate", True)):
            if flags[name] is not expected:
                reasons.append(name + "_failed_or_unknown")
        if flags["TrackStatus"] != "1": reasons.append("track_status_not_green_or_unknown")
        if scalar(row.get("PitInTime")) is not None or scalar(row.get("PitOutTime")) is not None: reasons.append("pit_lap")
        if phase is None: reasons.append("phase_unknown")
        compound = scalar(row.get("Compound"))
        if compound not in ("SOFT", "MEDIUM", "HARD", "SUPERSOFT", "ULTRASOFT", "HYPERSOFT"):
            reasons.append("dry_compound_unverified")
        rain = [sample for sample in weather if start and end and timestamp(start) - timedelta(seconds=90) <= timestamp(sample["date"]) <= timestamp(end) + timedelta(seconds=90)]
        if not rain or any(sample["rainfall"] != 0 for sample in rain): reasons.append("dry_weather_unverified")
        laps.append({"lap_id": f"fastf1_{year}_{round_number}_{session_type}_{number}_{lap_number}", "driver_number": number,
                     "lap_number": lap_number, "phase": phase, "lap_time_ms": duration, "sector_times_ms": sectors,
                     "lap_start_utc": start, "lap_end_utc": end,
                     "sector_crossing_utc": [clock(row.get(f"Sector{i}SessionTime")) for i in (1, 2, 3)],
                     "compound": compound, "tyre_life_laps": scalar(row.get("TyreLife")), "source_flags": flags,
                     "timing_candidate": not reasons, "exclusion_reasons": reasons})
    starts = [row["lap_start_utc"] for row in laps if row["lap_start_utc"]]
    ends = [row["lap_end_utc"] for row in laps if row["lap_end_utc"]]
    if not starts or not ends:
        raise ImportFailure("timing_unavailable", "Source has no actual lap-clock envelope")
    lap_drivers = {row["driver_number"] for row in laps}
    car, quarantined_car = quarantine_unrostered(car, roster, lap_drivers)
    positions, quarantined_position = quarantine_unrostered(positions, roster, lap_drivers)
    car, excluded_car = lap_window_rows(car, roster, min(starts), max(ends))
    positions, excluded_position = lap_window_rows(positions, roster, min(starts), max(ends))
    spec = {"year": year, "round": round_number, "session_type": session_type, "circuit_id": race["circuit_id"],
            "event_name": race["name"], "session_key": info.get("Key"), "profile": "monza-v1" if race["circuit_id"] == "monza" else "marker-windows-v1"}
    components = [{"source": "multiviewer" if "multiviewer" in item["source_url"] else "fastf1",
                   "version": str(year) if "multiviewer" in item["source_url"] else VERSION,
                   "url": item["source_url"], "sha256": item["sha256"], "retrieved_at": item["retrieved_at"],
                   "license_name": "Underlying data rights remain separate from the FastF1 software licence",
                   "license_url": "https://github.com/theOehrly/Fast-F1/blob/v3.9.2/LICENSE" if "multiviewer" not in item["source_url"] else None} for item in records]
    provenance = {"source": "fastf1", "fastf1_version": VERSION, "retrieved_at": utc_now(), "source_records": records, "components": components,
                  "unavailable_optional_resources": unavailable,
                  "native_resource_origins": sorted({item["source_url"].split('/')[2] for item in records}),
                  "clock_origin_utc": t0.isoformat(), "native_mask_policy": "raw-presence-v1",
                  "native_window_policy": "actual-lap-envelope-v1", "outside_lap_window_samples": {"car": excluded_car, "position": excluded_position},
                  "unassigned_native_streams": {"car":quarantined_car, "position":quarantined_position},
                  "limitations": ["Car and position rows decoded before library filling; absent channels remain absent", "Raw brake is binary 0/100 only", "Coordinate frame and circuit projection must pass year-specific publication checks"]}
    snapshot = {"source": "fastf1", "schema_version": "1.0.0", "import_spec": spec,
                "session": {**spec, "session_key": info.get("Key")}, "drivers": drivers, "laps": laps,
                "car_data": car, "position_data": positions, "weather": weather, "markers": markers, "provenance": provenance}
    digest = sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    path = cache / "snapshots" / digest[:24] / "snapshot.json"
    atomic_json(path, snapshot)
    atomic_json(cache / "snapshot-pointer.json", {"source_digest": digest, "snapshot_path": str(path.resolve())})
    progress(f"Imported FastF1 {year} {race['name']}: {len(drivers)} drivers, {len(laps)} actual laps; publication checks remain required")
    return path
