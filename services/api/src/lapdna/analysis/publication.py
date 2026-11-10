"""Offline normalization of one identity-checked session; serving never calls this."""

from datetime import datetime, timezone
from contextlib import contextmanager
import gzip
from hashlib import sha256
import json
import re
from pathlib import Path
import os
import time

from lapdna.alignment.native import (
    AlignmentError, aligned_channels, distance_at, linear, prepare_lap, support, utc_seconds,
)
from lapdna.alignment.reference import canonical_grid, geometry_at, monza_regions, marker_regions, project_markers
from lapdna.analysis.engine import METHOD, PIPELINE, SCHEMA, canonical_hash, grade, quality
from lapdna.inventory import SessionLapIndex
from lapdna.analysis.limits import MAX_NORMALIZED_LAPS, MAX_DISTANCE_POINTS


SESSION = {"session_id": "2024-16-monza-Q", "year": 2024, "round": 16,
           "session_type": "Q", "circuit_id": "monza", "event_name": "Italian Grand Prix"}
KNOWN_COMPOUNDS = {"SOFT", "MEDIUM", "HARD", "SUPERSOFT", "ULTRASOFT", "HYPERSOFT", "INTERMEDIATE", "WET"}


def weather_context(snapshot, lap):
    """Source rain observations near the lap, never an inferred dry track."""
    if not lap.get("lap_start_utc") or not lap.get("lap_end_utc"):
        return "unknown"
    start, end = utc_seconds(lap["lap_start_utc"]), utc_seconds(lap["lap_end_utc"])
    observations = []
    for row in snapshot.get("weather", []):
        value = row.get("rainfall")
        if type(value) not in (int, float, bool) or value not in (0, 1):
            continue
        try:
            when = utc_seconds(row["date"])
        except (KeyError, TypeError, ValueError):
            continue
        if start - 90 <= when <= end + 90:
            observations.append(bool(value))
    return "unknown" if not observations else "rain_reported" if any(observations) else "no_rain_reported"


@contextmanager
def activation_lock(output):
    """Short cross-process lock; the OS releases it if an operator job exits."""
    output.mkdir(parents=True, exist_ok=True)
    with (output / ".activation.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            for attempt in range(100):
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if attempt == 99:
                        raise ValueError("Another publication is being activated; retry with the retained snapshot") from None
                    time.sleep(.05)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def roster_and_laps(snapshot):
    drivers = {str(row["driver_number"]): row for row in snapshot["drivers"]}
    def colour(row):
        value = row.get("team_colour")
        return "#" + value.upper() if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{6}", value) else None
    roster = [{"driver_number": number, "driver_code": row["name_acronym"],
               "driver_name": row.get("full_name") or f"{row['first_name']} {row['last_name']}",
               "team_name": row.get("team_name"), "team_colour": colour(row)} for number, row in drivers.items()]
    positions = {str(row["driver_number"]): row.get("position") for row in snapshot.get("session_results", [])}
    roster.sort(key=lambda row: (positions.get(row["driver_number"]) or 999, int(row["driver_number"])))
    metadata = {}
    options = []
    for row in snapshot["laps"]:
        phase = row.get("phase")
        if phase not in ("Q1", "Q2", "Q3", "SQ1", "SQ2", "SQ3"):
            continue
        number = str(row["driver_number"])
        driver = drivers[number]
        value = {"lap_id": row["lap_id"], "phase": phase, "driver_number": number,
                 "team_name": driver.get("team_name"), "team_colour": colour(driver),
                 "driver_code": driver["name_acronym"], "driver_name": driver["full_name"],
                 "lap_number": row["lap_number"], "lap_time_ms": row.get("lap_time_ms"),
                 "sector_times_ms": row["sector_times_ms"], "compound": row.get("compound"),
                 "tyre_life_laps": row.get("tyre_life_laps"), "lap_start_utc": row.get("lap_start_utc")}
        original_reasons = list(row.get("exclusion_reasons", []))
        # v5 changes conditions eligibility only. Never relax deletion,
        # generated/accuracy, pit, phase, flag or raw timing requirements.
        removed = {"dry_weather_unverified"}
        if row.get("compound") in KNOWN_COMPOUNDS:
            removed.add("dry_compound_unverified")
        reasons = [reason for reason in original_reasons if reason not in removed]
        candidate = not reasons and (row.get("timing_candidate") is True or bool(original_reasons))
        if candidate:
            duration, sectors = value["lap_time_ms"], value["sector_times_ms"]
            if duration is None or duration <= 0 or any(sector is None or sector <= 0 for sector in sectors):
                candidate = False
                reasons.append("Recorded lap/sector timings are incomplete.")
            elif abs(sum(sectors) - duration) > 20.0001:
                candidate = False
                reasons.append("Recorded sector sum differs from lap duration by more than 20 ms.")
            elif abs((utc_seconds(row["lap_end_utc"]) - utc_seconds(row["lap_start_utc"])) * 1000 - duration) > 20.0001:
                candidate = False
                reasons.append("Source lap clock differs from recorded duration by more than 20 ms.")
        if not candidate and not reasons:
            reasons.append("Source timing/eligibility checks did not establish a clean complete lap.")
        options.append({**value, "capability": "sector_only" if candidate else "unavailable",
                        "reasons": reasons or ["Telemetry alignment has not yet passed its quality gates."]})
        if candidate:
            metadata[row["lap_id"]] = {**value, "track_status": "1"}
    return roster, options, metadata


def lap_metrics(prepared, regions, markers):
    native = prepared["native"]
    distances, elapsed = native["distance_m"], native["elapsed_ms"]
    output = {}
    for region in regions:
        start, end = region["start_m"], region["end_m"]
        fields = {"speed": support(prepared, start, end), "brake": support(prepared, start, end, "brake"),
                  "throttle": support(prepared, start, end, "throttle_pct")}
        local_markers = [marker for marker in markers if marker["segment_id"] == region["segment_id"]]
        approach_end = local_markers[0]["distance_m"] if local_markers else start
        onsets = []
        for i in range(1, len(distances) - 1):
            if not start <= distances[i] <= approach_end:
                continue
            if native["brake"][i - 1] is False and native["brake"][i] is True and native["brake"][i + 1] is True:
                if 200 <= elapsed[i + 1] - elapsed[i] <= 500.0001 and elapsed[i] - elapsed[i - 1] <= 500.0001:
                    onsets.append([distances[i - 1], distances[i]])
        fields["brake"]["onset"] = onsets[0] if len(onsets) == 1 else None
        local = [i for i, distance in enumerate(distances) if start <= distance <= end]
        min_index = min(local, key=lambda i: native["speed_kph"][i]) if local else None
        pickup = None
        if min_index is not None:
            for i in range(max(1, min_index + 1), len(distances) - 2):
                if distances[i] > end:
                    break
                values = native["throttle_pct"][i - 1:i + 3]
                if (all(value is not None for value in values) and values[0] < 95
                        and all(value >= 95 for value in values[1:])
                        and 400 <= elapsed[i + 2] - elapsed[i] <= 1000.0001
                        and max(elapsed[j + 1] - elapsed[j] for j in range(i - 1, i + 2)) <= 500.0001):
                    pickup = [distances[i - 1], distances[i]]
                    break
        fields["throttle"]["pickup"] = pickup
        # Positive native counts and spans are retained, never inferred from
        # the much denser display grid.
        output[region["segment_id"]] = fields
    return output


def _components(snapshot):
    provenance = snapshot.get("provenance", {})
    components = provenance.get("components", [])
    if not components:
        records = provenance.get("source_records", []) + provenance.get("archive_records", [])
        for record in records:
            url = record.get("source_url", "")
            source = "openf1" if "api.openf1.org/" in url else "tracinginsights" if "TracingInsights/" in url else "multiviewer" if "api.multiviewer.app/" in url else None
            if source is None:
                continue
            match = re.search(r"TracingInsights/(\d{4})/([a-f0-9]{40})/", url)
            archive_license = f"https://github.com/TracingInsights/{match[1]}/blob/{match[2]}/LICENSE" if match else None
            components.append({"source": source, "version": record.get("archive_commit") or ("v1" if source == "openf1" else str(snapshot["session"]["year"])),
                               "url": url, "sha256": record["sha256"], "retrieved_at": record["retrieved_at"],
                               "license_name": "CC BY-NC-SA 4.0" if source == "openf1" else "Archive licence and underlying data rights remain distinct; review the pinned licence" if source == "tracinginsights" else "Public endpoint; redistribution terms not verified",
                               "license_url": "https://github.com/br-g/openf1/blob/main/LICENSE" if source == "openf1" else
                               archive_license if source == "tracinginsights" else None})
    required = {"fastf1"} if snapshot.get("source") == "fastf1" else {"openf1", "tracinginsights"}
    if not required.issubset({item["source"] for item in components}):
        raise ValueError("composite snapshot requires explicit provider component hashes")
    return components


def timing_publication(snapshot, session, roster, options, metadata, report, components, source_hash):
    """Keep real lap selection without inventing a distance/reference axis."""
    if len({row["driver_number"] for row in metadata.values()}) < 2:
        raise ValueError("Fewer than two drivers have source-eligible recorded lap timing")
    primary, source = snapshot["source"] == "fastf1", snapshot["provenance"]
    retrieved = source.get("retrieved_at") or source.get("source_retrieved_at")
    if not retrieved:
        raise ValueError("Source retrieval timestamp is missing")
    reasons = sorted({reason for row in report["laps"].values() for reason in row.get("reasons", [])}
                     | {row["reason"] for row in report["reference_attempts"] if row.get("reason")})
    reason = ("No eligible lap supplies a verified distance/position reference. " + "; ".join(reasons[:2]))[:600]
    rows = {row["lap_id"]: row for row in snapshot["laps"]}
    publication = {"schema_version": SCHEMA, "session": session, "capability": "sector_only",
        "method": "distance-v5-fastf1-native" if primary else METHOD, "telemetry_unavailable_reason": reason,
        "laps": {identifier: {"metadata": value, "weather_context": weather_context(snapshot, rows[identifier])} for identifier, value in metadata.items()},
        "provenance": {"source": snapshot["source"], "fastf1_version": source.get("fastf1_version") if primary else None,
            "provider_version": f"FastF1 {source.get('fastf1_version')} raw primary" if primary else f"OpenF1 v1 + TracingInsights {session['year']} pinned archive",
            "source_retrieved_at": retrieved, "generated_at": retrieved, "source_snapshot_sha256": source_hash,
            "source_urls": source.get("source_urls", [item["url"] for item in components]), "components": components,
            "verification_scope": "Recorded lap/sector clocks and original validity checks only. Native/reference quality gates failed; no continuous distance, turn-local or corner-class claims are published.",
            "source_session": f"{session['year']} {session['event_name']} {session['session_type']} / source session {snapshot['session']['session_key']}"}}
    publication["publication_sha256"] = canonical_hash(publication)
    for option in options:
        if option["lap_id"] in metadata:
            option.update(capability="sector_only", reasons=report["laps"].get(option["lap_id"], {}).get("reasons") or [reason])
    mirror = primary and any("livetiming-mirror.fastf1.dev" in item.get("url","") for item in components)
    if mirror:
        publication["provenance"]["provider_version"] = f"FastF1 {source.get('fastf1_version')} native archive; mirror resources included"
        publication["provenance"]["verification_scope"] += " Per-resource origin URLs and hashes include the pinned FastF1 mirror; no filled car/position rows are used."
        publication["publication_sha256"] = canonical_hash({key:value for key,value in publication.items() if key != "publication_sha256"})
    index = {"schema_version": SCHEMA, "session": session, "source_snapshot_sha256": source_hash, "drivers": roster, "laps": options,
        "source_name": "FastF1 / primary timing" if primary else "OpenF1 + TracingInsights",
        "source_url": "https://docs.fastf1.dev/" if primary else "https://openf1.org/",
        "data_points": ["Recorded lap and sector timing", "Actual qualifying phases and source validity", "Event-specific drivers, teams and colours", "Source compound and tyre-life context"],
        "warnings": [reason, "Sector crossings are discrete timing observations; no intermediate curve or corner attribution is inferred."]}
    report.update(reference_lap_id=None, reference_length_m=None, telemetry_laps=0,
                  sector_only_laps=len(metadata), unavailable_laps=len(options)-len(metadata), telemetry_unavailable_reason=reason)
    if mirror:
        index["source_name"] = "FastF1 / native archive (mirror resources)"
    return publication, SessionLapIndex.model_validate_json(json.dumps(index)), report


def prepare_publication(snapshot: dict) -> tuple[dict, SessionLapIndex, dict]:
    if snapshot.get("source") not in ("openf1_tracinginsights", "fastf1"):
        raise ValueError("Publication requires identity-checked composite timing and native telemetry")
    components = _components(snapshot)
    primary = snapshot["source"] == "fastf1"
    spec = snapshot.get("import_spec")
    session = ({"session_id": f"{spec['year']}-{spec['round']}-{spec['circuit_id']}-{spec['session_type']}",
                **{key: spec[key] for key in ("year", "round", "session_type", "circuit_id", "event_name")}} if spec else SESSION)
    profile = spec.get("profile", "marker-windows-v1") if spec else "monza-v1"
    session_label = "Sprint Qualifying" if session["session_type"] == "SQ" else "Qualifying"
    source_hash = canonical_hash(snapshot)
    roster, options, metadata = roster_and_laps(snapshot)
    source_laps = {row["lap_id"]: row for row in snapshot["laps"]}
    report = {"method": METHOD, "source_snapshot_sha256": source_hash, "lap_count": len(snapshot["laps"]),
              "roster_count": len(roster), "reference_attempts": [], "laps": {}}
    prepared = {}
    candidates = sorted(metadata.values(), key=lambda row: (row["lap_time_ms"], int(row["driver_number"]), row["lap_number"]))
    for lap in candidates:
        raw = source_laps[lap["lap_id"]]
        try:
            prepared[lap["lap_id"]] = prepare_lap(snapshot["car_data"].get(lap["driver_number"], []),
                utc_seconds(raw["lap_start_utc"]), utc_seconds(raw["lap_end_utc"]))
        except AlignmentError as exc:
            report["laps"][lap["lap_id"]] = {"capability": "sector_only", "reasons": [str(exc)]}
    reference_id = None
    for candidate in candidates:
        identifier = candidate["lap_id"]
        if identifier not in prepared:
            continue
        native = prepared[identifier]
        trial_grid = canonical_grid(native["length"], [], [], [])
        try:
            trial_geometry = geometry_at(native, snapshot["position_data"].get(candidate["driver_number"], []), trial_grid)
            markers = project_markers(snapshot["markers"], trial_grid, trial_geometry, native)
            regions = monza_regions(markers, native["length"]) if profile == "monza-v1" else marker_regions(markers, native["length"])
            crossings = source_laps[identifier].get("sector_crossing_utc")
            if not crossings or len(crossings) < 2:
                raise AlignmentError("reference lacks actual source sector crossing timestamps")
            sectors = [distance_at(native, (utc_seconds(value) - native["start"]) * 1000) for value in crossings[:2]]
            if any(value is None for value in sectors):
                raise AlignmentError("reference sector crossings are outside native coverage")
            grid = canonical_grid(native["length"], markers, regions, sectors)
            geometry = geometry_at(native, snapshot["position_data"].get(candidate["driver_number"], []), grid)
            reference_id = identifier
            report["reference_attempts"].append({"lap_id": identifier, "status": "accepted"})
            break
        except AlignmentError as exc:
            report["reference_attempts"].append({"lap_id": identifier, "status": "rejected", "reason": str(exc)})
    if reference_id is None:
        return timing_publication(snapshot, session, roster, options, metadata, report, components, source_hash)
    source_provenance = snapshot["provenance"]
    retrieved = source_provenance.get("retrieved_at") or source_provenance.get("source_retrieved_at")
    if not retrieved:
        raise ValueError("snapshot must retain actual retrieval timestamp")
    publication = {"schema_version": SCHEMA, "session": session, "reference_lap_id": reference_id, "method": METHOD,
                   "circuit_revision": f"{session['circuit_id']}-{session['year']}-{profile}",
                   "profile": profile,
                   "distance_m": grid, "geometry": geometry, "regions": regions,
                   "corners": [{key: value for key, value in marker.items() if key != "projection_error_source_units"} for marker in markers],
                   "sector_boundaries_m": sectors, "laps": {},
                   "provenance": {"source": "openf1_tracinginsights", "fastf1_version": None,
                                  "provider_version": f"OpenF1 v1 + TracingInsights {session['year']} pinned archive",
                                  "source_retrieved_at": retrieved, "generated_at": retrieved,
                                  "source_urls": source_provenance.get("source_urls", [item["url"] for item in components]),
                                  "components": components, "source_snapshot_sha256": source_hash,
                                  "verification_scope": "Complete source driver/lap identities and available timings matched, native support and raw sector reconciliation checked. Local estimates are approximate; source agreement is not independent physical validation. Source licences do not independently grant all underlying F1 redistribution rights.",
                                  "source_session": f"{session['year']} {session['event_name']} Qualifying / OpenF1 session {snapshot['session']['session_key']} / TracingInsights {session['year']}"}}
    if primary:
        version = source_provenance["fastf1_version"]
        geometry["coordinate_note"] = "Primary native position coordinates retained in their year-specific source frame. The map is approximate; the distance axis is integrated speed, not map coordinates."
        publication["method"] = "distance-v5-fastf1-native"
        publication["provenance"].update(source="fastf1", fastf1_version=version, provider_version=f"FastF1 {version}; raw-presence-v1 decoder",
            verification_scope="Native primary car/position rows decoded before library filling. Lap clocks, phases and validity use the pinned FastF1 parser. Native support and unadjusted timing consistency must pass; no independent physical validation is claimed.",
            source_session=f"{session['year']} {session['event_name']} {session_label} / primary timing session {snapshot['session']['session_key']}")
        if any("livetiming-mirror.fastf1.dev" in item.get("url","") for item in components):
            geometry["coordinate_note"] = "Native archive position coordinates retained in their source frame; resource URLs and hashes identify primary/mirror delivery. The map is approximate and timing distance is integrated speed."
            publication["provenance"]["verification_scope"] = "Native car/position rows decoded before library filling. The pinned FastF1 primary/mirror fallback is declared per resource URL and hash. Lap clocks, phases and validity use the pinned parser; native support and unadjusted timing consistency must pass. No independent physical validation is claimed."
            publication["provenance"]["provider_version"] += "; mirror resources included"
    publication["reference_sha256"] = canonical_hash({"reference_lap_id": reference_id, "geometry": geometry,
                                                      "regions": regions, "corners": publication["corners"], "grid": grid,
                                                      "method": publication.get("method", METHOD)})
    length = grid[-1]
    option_map = {option["lap_id"]: option for option in options}
    for candidate in candidates:
        identifier, raw = candidate["lap_id"], source_laps[candidate["lap_id"]]
        record = {"metadata": candidate, "weather_context": weather_context(snapshot, raw)}
        publication["laps"][identifier] = record
        if identifier not in prepared:
            option_map[identifier]["reasons"] = report["laps"][identifier]["reasons"]
            continue
        try:
            native = prepare_lap(snapshot["car_data"][candidate["driver_number"]],
                                 utc_seconds(raw["lap_start_utc"]), utc_seconds(raw["lap_end_utc"]), length)
            record.update(channels=aligned_channels(native, grid), metrics=lap_metrics(native, regions, markers),
                          integrated_length_m=native["integrated_length_m"], scale_factor=native["scale_factor"],
                          native_count=native["native"]["native_count"], max_native_gap_ms=native["native"]["max_gap_ms"])
            # Individual residuals must pass before a pair can hide errors by
            # cancellation. Compare against the frozen reference locations.
            residuals = [linear(grid, record["channels"]["time_raw_ms"], sectors[i]) - sum(candidate["sector_times_ms"][:i + 1]) for i in range(2)]
            sector_error = sum(candidate["sector_times_ms"]) - candidate["lap_time_ms"]
            sliced_error = record["channels"]["time_raw_ms"][-1] - candidate["lap_time_ms"]
            blocked = (max(abs(value) for value in residuals) > 150.0001 or abs(record["scale_factor"] - 1) > .0300001
                       or abs(sector_error) > 20.0001 or abs(sliced_error) > 20.0001)
            report["laps"][identifier] = {"capability": "sector_only" if blocked else "telemetry",
                "interior_residual_ms": residuals, "sector_sum_residual_ms": sector_error,
                "sliced_residual_ms": sliced_error, "scale_factor": record["scale_factor"],
                "integrated_length_m": record["integrated_length_m"], "native_count": record["native_count"],
                "max_native_gap_ms": record["max_native_gap_ms"]}
            if blocked:
                record.pop("channels")
                record.pop("metrics")
                option_map[identifier]["reasons"] = ["Telemetry blocked by unadjusted interior residual, distance scale or timing consistency; inspect source diagnostics."]
            else:
                option_map[identifier].update(capability="telemetry", reasons=[])
        except AlignmentError as exc:
            report["laps"][identifier] = {"capability": "sector_only", "reasons": [str(exc)]}
            option_map[identifier]["reasons"] = [str(exc)]
    publication["publication_sha256"] = canonical_hash(publication)
    data_points = ["Recorded lap and sector timing", ("SQ1/SQ2/SQ3" if session["session_type"] == "SQ" else "Q1/Q2/Q3") + " and source validity", "Native speed (km/h)",
                   "Native throttle (%)", "Native gear", "Native binary brake", f"Approximate location and {len(markers)} source turn markers",
                   "Event-specific drivers/teams", "Compound and tyre age", "Source lap clocks and weather/race control context",
                   "Derived distance, delta, local gains and evidence-backed observations"]
    index = {"schema_version": SCHEMA, "session": session, "source_snapshot_sha256": source_hash,
             "drivers": roster, "laps": options, "source_name": "OpenF1 + TracingInsights",
             "source_url": "https://openf1.org/docs/", "data_points": data_points,
             "warnings": ["Public telemetry supports approximate local analysis; brake is binary, not pressure.",
                          "Map coordinates remain in their source frame. Timing distance is integrated speed.",
                          "Known wet tyres are supported. Source rainfall is context, not measured track grip; unknown weather never becomes assumed dry.",
                          "Eligible laps can still fall back to sectors when pair reconciliation fails."]}
    if primary:
        index.update(source_name="FastF1 / primary native records", source_url="https://docs.fastf1.dev/")
        if any("livetiming-mirror.fastf1.dev" in item.get("url","") for item in components):
            index["source_name"] = "FastF1 / native archive (mirror resources)"
    if profile == "marker-windows-v1":
        note = "Turn vicinities use fixed ±120 m source-marker windows; overlapping windows form a complex. They are approximate analysis zones, not measured corner boundaries."
        index["warnings"].append(note)
        publication["provenance"]["verification_scope"] += " " + note
        # Final identity includes the profile disclosure as well as its arrays.
        publication["publication_sha256"] = canonical_hash({key: value for key, value in publication.items() if key != "publication_sha256"})
    report["reference_lap_id"] = reference_id
    report["reference_length_m"] = length
    report["markers"] = markers
    report["regions"] = regions
    report["telemetry_laps"] = sum(option["capability"] == "telemetry" for option in options)
    report["sector_only_laps"] = sum(option["capability"] == "sector_only" for option in options)
    report["unavailable_laps"] = sum(option["capability"] == "unavailable" for option in options)
    return publication, SessionLapIndex.model_validate_json(json.dumps(index)), report


def write_publication(snapshot_path: Path, output: Path):
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    publication, index, report = prepare_publication(snapshot)
    session_id = index.session.session_id
    normalized = json.dumps(publication, separators=(",", ":"), allow_nan=False).encode()
    revision = publication["publication_sha256"]
    normalized_name = f"{session_id}-{revision}.json.gz"
    if len(normalized) > 20 * 1024 * 1024:
        raise ValueError("normalized pilot publication exceeds bounded reader size")
    if len(publication["laps"]) > MAX_NORMALIZED_LAPS or len(publication.get("distance_m", [])) > MAX_DISTANCE_POINTS:
        raise ValueError("normalized publication exceeds bounded lap/grid count")
    outputs = {
        output / "sessions" / f"{session_id}.json": index.model_dump_json().encode(),
        output / "normalized" / normalized_name: gzip.compress(normalized, mtime=0),
        output / "reports" / f"{session_id}.json": json.dumps(report, indent=2, allow_nan=False).encode(),
    }
    manifest = {"session_id": session_id, "schema_version": SCHEMA, "method": publication.get("method", METHOD),
                "normalized": f"normalized/{normalized_name}",
                "source_snapshot_sha256": index.source_snapshot_sha256,
                "publication_sha256": publication["publication_sha256"],
                "files": {str(path.relative_to(output)).replace("\\", "/"): sha256(data).hexdigest() for path, data in outputs.items()}}
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(path)
    # Each session has its own activation manifest; adding a session cannot
    # overwrite the identity of another. The root is a small lookup catalogue.
    manifest_path = output / "manifests" / f"{session_id}-{revision}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary.replace(manifest_path)
    with activation_lock(output):
        root = output / "publication.json"
        prior = json.loads(root.read_text(encoding="utf-8")) if root.exists() else {}
        catalogue = prior if prior.get("catalogue_version") == 2 else {"catalogue_version": 2, "sessions": {}}
        catalogue["sessions"][session_id] = {"manifest": str(manifest_path.relative_to(output)).replace("\\", "/"), "sha256": sha256(manifest_path.read_bytes()).hexdigest()}
        temporary = root.with_suffix(".tmp")
        temporary.write_text(json.dumps(catalogue, indent=2), encoding="utf-8")
        temporary.replace(root)
    return report, len(normalized), len(outputs[output / "normalized" / normalized_name])
