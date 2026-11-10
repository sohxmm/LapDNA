"""Offline v5 gate attribution. Never activates data or changes serving behaviour.

Diagnostic continuation uses the existing v5 integration equations on unchanged
native observations after recording a failed gap gate. It is not an accepted lap,
a v6 estimator, a generated measurement, or independent validation.
"""
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from itertools import combinations
import argparse
import ast
import gzip
import json
from math import ceil, isfinite
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from lapdna.alignment.native import (AlignmentError, finite_number, native_car,
    utc_seconds, integrated_distance, integral_at, linear)
from lapdna.analysis.engine import canonical_hash, grade
from lapdna.analysis.publication import roster_and_laps
from lapdna.ingestion.openf1 import atomic_json

AUDIT_VERSION = "v5-gate-attribution-1"
PROTECTED = ["services/api/src/lapdna/" + name for name in (
    "alignment/native.py", "alignment/reference.py", "analysis/engine.py",
    "analysis/publication.py", "ingestion/fastf1_native.py", "inventory.py", "models.py")]
GATES = {
    "timing_eligibility": "Source validity/phase/compound/timing eligibility",
    "sector_sum": "Source import flags >5 ms inconsistency; later publication limit is >20.0001 ms (stages retained per lap)",
    "sliced_duration": "Source import flags >5 ms clock inconsistency; later publication limit is >20.0001 ms (stages retained per lap)",
    "native_edges": "Valid native speed does not bracket both lap edges",
    "native_gap": "Maximum native speed interval >750.0001 ms",
    "native_conflict": "Conflicting native records at one timestamp",
    "native_samples": "Insufficient native speed observations",
    "progress": "Nonpositive/nonmonotone integrated lap progress",
    "session_reference": "No accepted frozen session reference/geometry/markers",
    "interior_residual": "Unadjusted individual sector-crossing residual >150.0001 ms",
    "scale": "Absolute integrated-distance scale error >3.00001%",
    "missing_channel.speed": "No valid native Speed observations (required input)",
    "other_alignment": "Other original v5 alignment rejection",
}
SPACING_BINS_MS = (100, 250, 500, 750, 1000, 1500, 2000, 5000)


def digest_file(path):
    return sha256(path.read_bytes()).hexdigest()


def distribution(values):
    """Weighted nearest-rank quantiles; counter keys are integer microseconds."""
    count = sum(values.values())
    if not count:
        return {"count": 0, "p50_ms": None, "p90_ms": None, "p95_ms": None,
                "p99_ms": None, "maximum_ms": None, "bins": {}}
    ordered = sorted(values.items())
    result = {"count": count}
    for label, quantile in (("p50", .5), ("p90", .9), ("p95", .95), ("p99", .99)):
        rank, seen = ceil(count * quantile), 0
        for value, frequency in ordered:
            seen += frequency
            if seen >= rank:
                result[label + "_ms"] = value / 1000
                break
    result["maximum_ms"] = ordered[-1][0] / 1000
    bins = Counter()
    for value, frequency in ordered:
        upper = next((bound for bound in SPACING_BINS_MS if value <= bound * 1000), None)
        lower = SPACING_BINS_MS[SPACING_BINS_MS.index(upper) - 1] if upper is not None and SPACING_BINS_MS.index(upper) else 0
        label = f"({lower}, {upper}] ms" if upper is not None else "> 5000 ms"
        bins[label] += frequency
    result["bins"] = dict(bins)
    return result


def gate_for_error(message):
    for prefix, gate in (("native speed gap", "native_gap"),
            ("native speed does not bracket", "native_edges"),
            ("conflicting native", "native_conflict"),
            ("insufficient native speed", "native_samples"),
            ("integrated lap length", "progress"), ("stationary or", "progress")):
        if message.startswith(prefix):
            return gate
    return "other_alignment"


def measured_rows(rows, start, end):
    """Audit the same source range and scalar masks as native_car, without filling."""
    unique, conflicts, invalid_dates = {}, 0, 0
    for row in rows:
        try:
            when = utc_seconds(row["date"])
        except (KeyError, TypeError, ValueError):
            invalid_dates += 1
            continue
        if not start - 1 <= when <= end + 1:
            continue
        gear, brake = row.get("n_gear"), row.get("brake")
        values = (finite_number(row.get("speed"), 0, 400),
                  finite_number(row.get("throttle"), 0, 100),
                  gear if type(gear) is int and 0 <= gear <= 8 else None,
                  brake == 100 if type(brake) in (int, float) and brake in (0, 100) else None,
                  finite_number(row.get("rpm"), 0))
        if when in unique and unique[when][:4] != values[:4]:
            conflicts += 1
        unique.setdefault(when, values)
    ordered = sorted(unique.items())
    speeds = [(when, values[0]) for when, values in ordered if values[0] is not None]
    times = [when for when, _ in speeds]
    first, last = bisect_right(times, start) - 1, bisect_left(times, end)
    speed_brackets = first >= 0 and last < len(speeds)
    selected = speeds[first:last + 1] if speed_brackets else speeds
    car_times = [when for when, _ in ordered]
    in_lap = [(when, values) for when, values in ordered if start <= when <= end]
    counts = {name: sum(values[i] is not None for _, values in in_lap)
              for i, name in enumerate(("speed", "throttle", "gear", "brake", "rpm"))}
    return {"speed_times": [when for when, _ in selected],
            "speeds": [speed for _, speed in selected], "speed_brackets": speed_brackets,
            "car_brackets": bool(car_times and car_times[0] <= start and car_times[-1] >= end),
            "car_times": [when for when, _ in in_lap], "counts": counts,
            "native_car_samples": len(in_lap), "conflicts": conflicts, "invalid_dates": invalid_dates}


def diagnostic_progress(measured, start, end, length=None):
    """Existing prepare_lap equations; no gap acceptance, new interpolation or samples."""
    if not measured["speed_brackets"] or measured["conflicts"]:
        return None
    times, speeds = measured["speed_times"], measured["speeds"]
    integrated = integrated_distance(times, speeds)
    offset = integral_at(start, times, speeds, integrated)
    actual = integral_at(end, times, speeds, integrated) - offset
    if actual <= 0:
        raise AlignmentError("integrated lap length is nonpositive")
    canonical = actual if length is None else length
    scale = canonical / actual
    internal = [i for i, when in enumerate(times) if start < when < end]
    distance = [0., *[(integrated[i] - offset) * scale for i in internal], canonical]
    elapsed = [0., *[(times[i] - start) * 1000 for i in internal], (end - start) * 1000]
    if any(b <= a for a, b in zip(distance, distance[1:])):
        raise AlignmentError("stationary or non-increasing lap progress")
    return {"distance": distance, "elapsed": elapsed, "scale_factor": scale,
            "integrated_length_m": actual}


def probe_lap(raw, option, rows, publication):
    """Record actual first rejection and conditional downstream measurements separately."""
    eligible = option["capability"] != "unavailable"
    result = {"lap_id": option["lap_id"], "driver_number": option["driver_number"],
        "phase": option["phase"], "capability_v5": option["capability"],
        "timing_eligible_v5": eligible, "first_failed_gate": None,
        "all_failed_lap_gates": [], "not_evaluated": {}, "source_eligibility_reasons": [],
        "actual_alignment_error": None, "diagnostic_continuation": False,
        "measurements": {}, "pair_context": {}}
    failures, metrics = result["all_failed_lap_gates"], result["measurements"]
    duration, sectors = raw.get("lap_time_ms"), raw.get("sector_times_ms", [])
    if isinstance(duration, (int, float)) and duration > 0 and len(sectors) == 3 and all(isinstance(v, (int, float)) for v in sectors):
        metrics["sector_sum_residual_ms"] = sum(sectors) - duration
        if abs(metrics["sector_sum_residual_ms"]) > 20.0001:
            failures.append("sector_sum")
    else:
        result["not_evaluated"]["sector_sum"] = "incomplete recorded timings"
    if not eligible:
        result["source_eligibility_reasons"] = option["reasons"]
        # Preserve the real timing-selection order; numeric-only eligibility
        # failures are not falsely attributed to deletion/flag policy.
        reasons = option["reasons"]
        first = ("sector_sum" if reasons and reasons[0].startswith("Recorded sector sum differs") else
                 "sliced_duration" if reasons and reasons[0].startswith("Source lap clock differs") else
                 ("sector_sum" if abs(metrics.get("sector_sum_residual_ms", 0)) > 5 else "sliced_duration")
                 if reasons and reasons[0] == "native_timing_inconsistent" else "timing_eligibility")
        result["first_failed_gate"] = first
        if first not in failures:
            failures.insert(0, first)
    try:
        if not isinstance(raw.get("lap_start_utc"), str) or not isinstance(raw.get("lap_end_utc"), str):
            raise ValueError
        start, end = utc_seconds(raw["lap_start_utc"]), utc_seconds(raw["lap_end_utc"])
        if end <= start:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        result["not_evaluated"].update({key: "missing/invalid lap-clock edges" for key in (
            "native_gap", "native_edges", "sliced_duration", "interior_residual", "scale", "missing_channel")})
        return result, {}
    metrics["sliced_duration_residual_ms"] = (end - start) * 1000 - duration if isinstance(duration, (int, float)) else None
    if "native_timing_inconsistent" in raw.get("exclusion_reasons", []):
        # The importer uses exact datetime differences at its earlier 5 ms
        # gate, while prepare_lap uses UTC float seconds. Preserve both.
        exact = (datetime.fromisoformat(raw["lap_end_utc"].replace("Z", "+00:00"))
                 - datetime.fromisoformat(raw["lap_start_utc"].replace("Z", "+00:00"))).total_seconds() * 1000 - duration
        metrics["source_import_clock_residual_ms"] = exact
        metrics["source_import_consistency_limit_ms"] = 5.
        if abs(exact) > 5:
            failures.append("sliced_duration")
        if abs(metrics.get("sector_sum_residual_ms", 0)) > 5:
            failures.append("sector_sum")
    if metrics["sliced_duration_residual_ms"] is None:
        result["not_evaluated"]["sliced_duration"] = "missing recorded lap duration"
    if metrics["sliced_duration_residual_ms"] is not None and abs(metrics["sliced_duration_residual_ms"]) > 20.0001:
        failures.append("sliced_duration")
    measured = measured_rows(rows, start, end)
    metrics.update({key: measured[key] for key in ("speed_brackets", "car_brackets", "native_car_samples", "counts", "conflicts")})
    intervals = [b - a for a, b in zip(measured["speed_times"], measured["speed_times"][1:]) if b > start and a < end]
    metrics["max_speed_gap_ms"] = max(intervals) * 1000 if intervals else None
    metrics["missing_channels"] = [name for name, count in measured["counts"].items() if not count]
    if not measured["speed_times"]:
        failures.append("missing_channel.speed")
    if not measured["speed_brackets"]:
        failures.append("native_edges")
    if measured["conflicts"]:
        failures.append("native_conflict")
    if len(measured["speed_times"]) < 2:
        failures.append("native_samples")
    if intervals and max(intervals) > .7500001:
        failures.append("native_gap")
    try:
        native_car(rows, start, end)  # authoritative unchanged original first gate
    except AlignmentError as error:
        result["actual_alignment_error"] = str(error)
        if eligible:
            result["first_failed_gate"] = gate_for_error(str(error))
    has_reference = bool(publication.get("reference_lap_id"))
    length = publication["distance_m"][-1] if has_reference else None
    try:
        progress = diagnostic_progress(measured, start, end, length)
    except AlignmentError as error:
        progress = None
        failures.append("progress")
        if eligible and result["first_failed_gate"] is None:
            result["first_failed_gate"] = "progress"
    if progress is not None:
        metrics["integrated_length_m"] = progress["integrated_length_m"]
    result["diagnostic_continuation"] = bool(result["first_failed_gate"] or not eligible)
    if not has_reference:
        failures.append("session_reference")
        result["not_evaluated"].update({key: "no frozen v5 session reference" for key in ("scale", "interior_residual", "pair_gap")})
        if eligible and result["first_failed_gate"] is None:
            result["first_failed_gate"] = "session_reference"
    elif progress is None:
        result["not_evaluated"].update({key: "native speed edges/conflicts/progress prevent evaluation" for key in ("scale", "interior_residual", "pair_gap")})
    else:
        grid, boundaries = publication["distance_m"], publication["sector_boundaries_m"]
        times = [linear(progress["distance"], progress["elapsed"], value) for value in grid]
        metrics.update(scale_factor=progress["scale_factor"], integrated_length_m=progress["integrated_length_m"])
        if len(sectors) == 3 and all(isinstance(v, (int, float)) for v in sectors):
            residuals = [linear(grid, times, boundary) - sum(sectors[:i + 1]) for i, boundary in enumerate(boundaries[:2])]
            metrics["interior_residual_ms"] = residuals
            if max(abs(value) for value in residuals) > 150.0001:
                failures.append("interior_residual")
        else:
            result["not_evaluated"]["interior_residual"] = "incomplete recorded sectors"
        if abs(progress["scale_factor"] - 1) > .0300001:
            failures.append("scale")
        # Exact actual prepared channels are retained for accepted laps. This
        # also proves diagnostic equations did not silently alter v5 timing.
        published = publication["laps"].get(option["lap_id"], {})
        if "channels" in published:
            assert times == published["channels"]["time_raw_ms"], "Diagnostic continuation diverged from v5"
        if eligible and result["first_failed_gate"] is None:
            result["first_failed_gate"] = next((g for g in ("interior_residual", "scale", "sector_sum", "sliced_duration") if g in failures), None)
    failures[:] = list(dict.fromkeys(failures))
    if eligible:
        assert (result["first_failed_gate"] is None) == (option["capability"] == "telemetry"), (option["lap_id"], result)
    speed_distribution = Counter(round(value * 1_000_000) for value in intervals)
    car_distribution = Counter(round((b - a) * 1_000_000) for a, b in zip(measured["car_times"], measured["car_times"][1:]))
    return result, {"native_car_spacing": car_distribution, "native_speed_spacing": speed_distribution,
        "speed_gaps_over_750ms": Counter({k: v for k, v in speed_distribution.items() if k > 750000}),
        "lap_max_speed_gap": Counter({round(metrics["max_speed_gap_ms"] * 1000): 1}) if measured["speed_brackets"] and intervals else Counter()}


def pair_attribution(records):
    """Count scalar gate relationships; never build Cartesian comparison artifacts."""
    aggregate = {}
    eligible = [r for r in records if r["timing_eligible_v5"]]
    for a, b in combinations(eligible, 2):
        cohort = ("same_driver_selection_blocked" if a["driver_number"] == b["driver_number"] else
                  "same_phase" if a["phase"] == b["phase"] else "cross_phase_opt_in")
        summary = aggregate.setdefault(cohort, {"pairs": 0, "actual_first_failed_gate": Counter(),
            "actual_pair_gap_failures": Counter(), "diagnostic_pair_gap_failures": Counter(),
            "actual_evaluated": 0, "diagnostic_evaluated": 0, "not_evaluated": 0})
        summary["pairs"] += 1
        contexts = [r["pair_context"].setdefault(cohort, {"peers": 0, "actual_evaluated": 0,
            "diagnostic_evaluated": 0, "not_evaluated": 0, "actual_pair_gap_failures": Counter(),
            "diagnostic_pair_gap_failures": Counter(), "example_failed_peer": None}) for r in (a, b)]
        for context in contexts:
            context["peers"] += 1
        ma, mb = a["measurements"], b["measurements"]
        actual = cohort != "same_driver_selection_blocked" and a["capability_v5"] == b["capability_v5"] == "telemetry"
        evaluable = all("interior_residual_ms" in m and m.get("sliced_duration_residual_ms") is not None for m in (ma, mb))
        if cohort == "same_driver_selection_blocked":
            first = "selection_same_driver"
        elif not actual:
            first = "missing_alignment"
        else:
            first = None
            # Same order as the quality() check list, followed by scale/gaps.
            for slot, m in (("A", ma), ("B", mb)):
                for key, metric, threshold in (("sector_sum_residual_ms", "sector_sum", 20.),
                        ("sliced_duration_residual_ms", "sliced_duration", 20.),
                        ("interior_residual_ms", "interior_residual", 150.)):
                    values = m[key] if isinstance(m[key], list) else [m[key]]
                    if any(grade(value, 0., threshold) == "block" for value in values):
                        first = first or slot + "." + metric
        failed = []
        if evaluable:
            differences = [right - left for left, right in zip(ma["interior_residual_ms"], mb["interior_residual_ms"])]
            differences.append(mb["sliced_duration_residual_ms"] - ma["sliced_duration_residual_ms"])
            failed = [name for name, value, threshold in zip(("pair_sector_1", "pair_sector_2", "pair_lap_gap"), differences, (150., 150., 20.))
                      if grade(value, 0., threshold) == "block"]
            kind = "actual" if actual else "diagnostic"
            summary[kind + "_evaluated"] += 1
            summary[kind + "_pair_gap_failures"].update(failed)
            for record, other, context in ((a, b, contexts[0]), (b, a, contexts[1])):
                context[kind + "_evaluated"] += 1
                context[kind + "_pair_gap_failures"].update(failed)
                if failed and context["example_failed_peer"] is None:
                    context["example_failed_peer"] = {"lap_id": other["lap_id"], "scope": kind, "gates": failed}
            if actual:
                first = first or next(iter(failed), None)
                if first is None:
                    if any(grade(abs(m["scale_factor"] - 1), 0., .03) == "block" for m in (ma, mb)):
                        first = "scale"
                    elif any(grade(m["max_speed_gap_ms"], 0., 750.) == "block" for m in (ma, mb)):
                        first = "native_gap"
        else:
            summary["not_evaluated"] += 1
            for context in contexts:
                context["not_evaluated"] += 1
        summary["actual_first_failed_gate"][first or "none"] += 1
    return aggregate


def summarize(records):
    output = {}
    for name, selected in (("all_indexed", records), ("timing_eligible", [r for r in records if r["timing_eligible_v5"]])):
        failed = [r for r in selected if r["capability_v5"] != "telemetry"]
        output[name] = {"laps": len(selected), "telemetry_laps": len(selected) - len(failed),
            "failed_telemetry_laps": len(failed),
            "first_failed_gate": dict(Counter(r["first_failed_gate"] for r in failed)),
            "all_failed_lap_gates": dict(Counter(g for r in failed for g in r["all_failed_lap_gates"])),
            "not_evaluated": dict(Counter(g for r in selected for g in r["not_evaluated"])),
            "source_eligibility_reasons": dict(Counter(g for r in selected for g in r["source_eligibility_reasons"])),
            "car_brackets_both_edges": sum(r["measurements"].get("car_brackets", False) for r in selected),
            "speed_brackets_both_edges": sum(r["measurements"].get("speed_brackets", False) for r in selected),
            "entirely_missing_native_car_in_lap": sum(r["measurements"].get("native_car_samples", 0) == 0 for r in selected),
            "entirely_missing_channel_in_lap": dict(Counter(name for r in selected for name in r["measurements"].get("missing_channels", []))),
            "diagnostic_continuation_laps": sum(r["diagnostic_continuation"] for r in selected)}
    return output


def protected_functions():
    result = {}
    names = {"analysis/engine.py": ("summaries", "sensitivity", "regional_gain", "_evidence"),
             "analysis/publication.py": ("roster_and_laps", "lap_metrics"),
             "alignment/reference.py": ("project_markers", "speed_class", "monza_regions", "marker_regions")}
    for relative, wanted in names.items():
        path = ROOT / "services/api/src/lapdna" / relative
        source = path.read_bytes().splitlines(keepends=True)
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.FunctionDef) and node.name in wanted:
                result[relative + ":" + node.name] = sha256(b"".join(source[node.lineno - 1:node.end_lineno])).hexdigest()
    return result


def audit_session(entry, publication_root, snapshot_path):
    sid = entry["session_id"]
    snapshot_bytes = snapshot_path.read_bytes()
    snapshot_file_sha256 = sha256(snapshot_bytes).hexdigest()
    snapshot = json.loads(snapshot_bytes)
    del snapshot_bytes
    assert canonical_hash(snapshot) == entry["source_snapshot_sha256"], "Raw snapshot identity changed"
    catalogue = json.loads((publication_root / "publication.json").read_bytes())
    active = catalogue["sessions"][sid]
    manifest_path = publication_root / active["manifest"]
    assert digest_file(manifest_path) == active["sha256"]
    manifest = json.loads(manifest_path.read_bytes())
    for name, expected in manifest["files"].items():
        assert digest_file(publication_root / name) == expected, "Activated publication input changed"
    publication = json.loads(gzip.decompress((publication_root / manifest["normalized"]).read_bytes()))
    assert publication["publication_sha256"] == entry["publication_sha256"]
    index = json.loads((publication_root / "sessions" / f"{sid}.json").read_bytes())
    _, options, _ = roster_and_laps(snapshot)
    assert [(o["lap_id"], o["capability"] != "unavailable") for o in options] == [(o["lap_id"], o["capability"] != "unavailable") for o in index["laps"]]
    source_laps = {r["lap_id"]: r for r in snapshot["laps"]}
    streams = {}
    for driver, rows in snapshot["car_data"].items():
        ordered = sorted(((utc_seconds(r["date"]), r) for r in rows), key=lambda r: r[0])
        streams[driver] = ([t for t, _ in ordered], [r for _, r in ordered])
    records, distributions = [], {name: Counter() for name in ("native_car_spacing", "native_speed_spacing", "speed_gaps_over_750ms", "lap_max_speed_gap")}
    for option in index["laps"]:
        raw = source_laps[option["lap_id"]]
        times, rows = streams.get(option["driver_number"], ([], []))
        try:
            if not isinstance(raw.get("lap_start_utc"), str) or not isinstance(raw.get("lap_end_utc"), str):
                raise ValueError
            start, end = utc_seconds(raw["lap_start_utc"]), utc_seconds(raw["lap_end_utc"])
            window = rows[bisect_left(times, start - 1):bisect_right(times, end + 1)]
        except (TypeError, KeyError, ValueError):
            window = []
        record, values = probe_lap(raw, option, window, publication)
        records.append(record)
        if record["timing_eligible_v5"]:
            for name, values_for_metric in values.items():
                distributions[name].update(values_for_metric)
    pair_summary = pair_attribution(records)
    summary = summarize(records)
    assert summary["timing_eligible"]["laps"] == len(publication["laps"])
    assert summary["timing_eligible"]["telemetry_laps"] == entry["capabilities"].get("telemetry", 0)
    report = json.loads((publication_root / "reports" / f"{sid}.json").read_bytes())
    return {"session_id": sid, "year": entry["year"], "source_snapshot_sha256": entry["source_snapshot_sha256"],
        "source_file_sha256": snapshot_file_sha256,
        "publication_sha256": entry["publication_sha256"], "summary": summary,
        "reference": {"available": bool(publication.get("reference_lap_id")), "reference_lap_id": publication.get("reference_lap_id"),
                      "attempt_rejections": dict(Counter(r["reason"] for r in report.get("reference_attempts", []) if r.get("reason")))},
        "pair_gates": pair_summary, "distribution_counts_us": {name: dict(values) for name, values in distributions.items()},
        "laps": records}


def merge_summaries(sessions):
    output = {}
    for cohort in ("all_indexed", "timing_eligible"):
        totals = Counter()
        counters = {}
        for session in sessions:
            for key, value in session["summary"][cohort].items():
                if isinstance(value, dict):
                    counters.setdefault(key, Counter()).update(value)
                else:
                    totals[key] += value
        output[cohort] = {**totals, **{key: dict(value) for key, value in counters.items()}}
    distributions = {}
    for session in sessions:
        for name, values in session["distribution_counts_us"].items():
            distributions.setdefault(name, Counter()).update({int(k): v for k, v in values.items()})
    output["distributions"] = {name: distribution(values) for name, values in distributions.items()}
    pair_totals = {}
    for session in sessions:
        for cohort, values in session["pair_gates"].items():
            target = pair_totals.setdefault(cohort, {})
            for key, value in values.items():
                if isinstance(value, dict):
                    target.setdefault(key, Counter()).update(value)
                else:
                    target[key] = target.get(key, 0) + value
    output["pair_gates"] = pair_totals
    return output


def render_report(audit):
    rows = ["# V5 telemetry gate attribution — Step 0", "", "Measurement only. No runtime, selection, alignment, contract or observation gate was changed.", "",
        f"Audit version `{AUDIT_VERSION}`. Baseline source `{audit['baseline_commit']}`; active catalogue `{audit['catalogue_sha256']}`.",
        f"Sessions: **{audit['sessions']}**. Full per-lap derived ledger: `{audit['per_lap_ledger']['path']}` (SHA-256 `{audit['per_lap_ledger']['sha256']}`).", "",
        "## Cohorts and interpretation", "",
        "Timing-eligible means the existing v5 source/timing selection, not a new denominator. All indexed known-phase laps are also audited, including excluded laps. Unknown-phase raw laps are outside the published lap index.",
        "First failure follows the existing eligibility → native preparation → frozen-reference → individual-publication gate order. The publication's final combined condition orders interior residual, scale, sector sum, then sliced duration. Pair gates are contextual and are reported separately; a failed peer comparison does not make a lap intrinsically bad.",
        "All-failure counts include diagnostic continuation using unchanged v5 equations on actual native gap endpoints where a frozen reference exists. This does not accept a gap, insert samples, implement v6 bridging, fit time to sectors, or establish independent validation. If prerequisites/reference are absent, downstream gates are explicitly not evaluated. Counts overlap; they must not be added as disjoint failures.",
        "Missing throttle/gear/brake/RPM is channel availability, not an existing whole-lap graph gate. Only the required speed stream can prevent alignment. No new missing-optional-channel rejection is invented for this audit.", "",
        "## Per-year baseline and native edge coverage", "",
        "| Year | Indexed laps | Timing eligible | V5 telemetry | Telemetry % | Car brackets both edges | Bracket % | No in-lap car samples |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for year, values in audit["by_year"].items():
        e = values["timing_eligible"]; n = e["laps"]
        rows.append(f"| {year} | {values['all_indexed']['laps']} | {n} | {e['telemetry_laps']} | {100 * e['telemetry_laps']/n:.2f} | {e['car_brackets_both_edges']} | {100*e['car_brackets_both_edges']/n:.2f} | {e['entirely_missing_native_car_in_lap']} |")
    rows += ["", "Car-edge coverage is an input feasibility measurement, not a Tier 0 coverage claim; no tier has been implemented.", "", "## First failing lap gate — timing-eligible laps", ""]
    requested = {"native_gap", "sector_sum", "sliced_duration", "interior_residual", "scale", "missing_channel.speed"}
    gates = sorted(requested | {g for v in audit["by_year"].values() for g in v["timing_eligible"]["first_failed_gate"]})
    rows += ["| Year | " + " | ".join(gates) + " |", "| --- | " + " | ".join("---:" for _ in gates) + " |"]
    for year, values in audit["by_year"].items():
        rows.append("| " + year + " | " + " | ".join(str(values['timing_eligible']['first_failed_gate'].get(g, 0)) for g in gates) + " |")
    rows += ["", "## All failed lap gates — timing-eligible laps", ""]
    gates = sorted(requested | {g for v in audit["by_year"].values() for g in v["timing_eligible"]["all_failed_lap_gates"]})
    rows += ["| Year | " + " | ".join(gates) + " |", "| --- | " + " | ".join("---:" for _ in gates) + " |"]
    for year, values in audit["by_year"].items():
        rows.append("| " + year + " | " + " | ".join(str(values['timing_eligible']['all_failed_lap_gates'].get(g, 0)) for g in gates) + " |")
    rows += ["", "Sector-sum and sliced-duration failures can be zero in this cohort because timing selection already enforces them. The all-indexed histograms below preserve those earlier exclusions.", "", "## First failures — all indexed laps", ""]
    rows += ["| Year | Gate | Laps |", "| --- | --- | ---: |"]
    for year, values in audit["by_year"].items():
        for gate, count in sorted(values["all_indexed"]["first_failed_gate"].items()):
            rows.append(f"| {year} | {gate} | {count} |")
    rows += ["", "### All failed gates — all indexed laps", "", "| Year | Gate | Laps |", "| --- | --- | ---: |"]
    for year, values in audit["by_year"].items():
        for gate, count in sorted(values["all_indexed"]["all_failed_lap_gates"].items()):
            rows.append(f"| {year} | {gate} | {count} |")
    rows += ["", "The primary importer marks `native_timing_inconsistent` when sector sum OR exact source-clock duration differs by more than **5 ms**, before later 20 ms publication checks. The first offending source check is attributed to its numeric gate, with both source and preparation clock residuals retained. Source deletion/accuracy/pit/status exclusions remain explicit per lap and in each session/year ledger.", "",
        "### Entirely missing in-lap channel observations — timing eligible", "", "These are availability counts, not invented optional-channel gates.", "",
        "| Year | Speed | Throttle | Gear | Brake | RPM |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for year, values in audit["by_year"].items():
        missing = values["timing_eligible"]["entirely_missing_channel_in_lap"]
        rows.append(f"| {year} | " + " | ".join(str(missing.get(name, 0)) for name in ("speed", "throttle", "gear", "brake", "rpm")) + " |")
    rows += ["", "## Native interval distributions", "", "Timing-eligible laps only. Unique actual car timestamps inside each lap define car sample spacing. Valid-speed intervals overlapping the lap use the original ±1 s window and available native edge padding. Maximum-gap distributions include only speed-bracketed laps. No resampled/display-grid points enter these distributions. Intervals are rounded to 1 microsecond for exact weighted nearest-rank quantiles; values below are milliseconds.", ""]
    rows += ["| Year | Distribution | N | P50 ms | P90 ms | P95 ms | P99 ms | Max ms |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for year, values in audit["by_year"].items():
        for name, stats in values["distributions"].items():
            rows.append(f"| {year} | {name} | " + " | ".join(str(stats.get(key)) for key in ("count", "p50_ms", "p90_ms", "p95_ms", "p99_ms", "maximum_ms")) + " |")
    rows += ["", "### Speed-gap length bins (>750 ms)", "", "Disjoint bins, not cumulative counts.", "", "| Year | Gap bin | Intervals |", "| --- | --- | ---: |"]
    for year, values in audit["by_year"].items():
        for label, count in values["distributions"]["speed_gaps_over_750ms"]["bins"].items():
            rows.append(f"| {year} | {label} | {count} |")
    rows += ["", "## Downstream gates not evaluated — timing eligible", "", "| Year | Gate | Laps |", "| --- | --- | ---: |"]
    for year, values in audit["by_year"].items():
        for gate, count in sorted(values["timing_eligible"]["not_evaluated"].items()):
            rows.append(f"| {year} | {gate} | {count} |")
    rows += ["", "## Pair-gap attribution", "", "All distinct timing-eligible lap pairs are counted using scalar residual comparisons only; no Cartesian comparison artifacts or observations are generated. Same-phase and cross-phase-opt-in distinct-driver cohorts are separate. Same-driver pairs remain rejected by current selection and are recorded as such. Actual pair gates require both currently published telemetry laps; other calculable residual differences are diagnostic-only. A peer's failure remains pair context in each lap record.", "",
        "| Year | Cohort | Pairs | Actual evaluated | Diagnostic evaluated | Prerequisites absent | Actual pair-sector-1 failures | Actual pair-sector-2 failures | Actual pair-lap-gap failures |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for year, values in audit["by_year"].items():
        for cohort, stats in values["pair_gates"].items():
            g = stats["actual_pair_gap_failures"]
            rows.append(f"| {year} | {cohort} | {stats['pairs']} | {stats['actual_evaluated']} | {stats['diagnostic_evaluated']} | {stats['not_evaluated']} | {g.get('pair_sector_1',0)} | {g.get('pair_sector_2',0)} | {g.get('pair_lap_gap',0)} |")
    rows += ["", "## Reproduce and inspect", "", "```powershell", ".venv\\Scripts\\python scripts/attribute_telemetry_gates.py", "```", "", "The script reads retained source snapshots and activated publications offline. Source digests, active file hashes, eligibility parity and every currently published lap's reconstructed timing array are checked. Raw car/position rows, authentication and absolute cache paths are not committed. The ledger contains derived diagnostics only. `config/telemetry-coverage.json` retains the original coverage fields and adds the attribution receipt, per-year and per-session summaries; the compressed JSON-lines companion records every indexed lap.", "", "Gate definitions:", ""]
    rows.extend(f"- `{name}`: {description}." for name, description in GATES.items())
    rows += ["", "**Stop point:** Step 0 only. No contracts, v6 method, bridge masks, selection rules, graph rows or observation gates have changed. Review this report before proceeding to Step 1.", ""]
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication", type=Path, default=ROOT / "services/api/src/lapdna/pilot_data")
    parser.add_argument("--ledger", type=Path, default=ROOT / "config/telemetry-coverage.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/23-gate-attribution.md")
    parser.add_argument("--lap-ledger", type=Path, default=ROOT / "config/gate-attribution-laps.jsonl.gz")
    parser.add_argument("--work", type=Path, default=ROOT / "work/gate-attribution")
    parser.add_argument("--sessions", nargs="+")
    args = parser.parse_args()
    baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ledger = json.loads(args.ledger.read_bytes())
    selected = [r for r in ledger["sessions"] if not args.sessions or r["session_id"] in args.sessions]
    assert selected and (not args.sessions or len(selected) == len(set(args.sessions)))
    protected = {p: digest_file(ROOT / p) for p in PROTECTED}
    catalogue_hash = digest_file(args.publication / "publication.json")
    script_hash = digest_file(Path(__file__))
    pointers = list((ROOT / "work/fastf1").glob("*/snapshot-pointer.json"))
    snapshots = {}
    for pointer in pointers:
        record = json.loads(pointer.read_bytes())
        path = Path(record["snapshot_path"])
        if path.is_file():
            snapshots[record["source_digest"]] = path
    args.work.mkdir(parents=True, exist_ok=True)
    sessions = []
    for entry in selected:
        cache = args.work / (entry["session_id"] + ".json.gz")
        key = [script_hash, canonical_hash(protected), entry["source_snapshot_sha256"], entry["publication_sha256"]]
        saved = json.loads(gzip.decompress(cache.read_bytes())) if cache.is_file() else None
        if saved is not None and saved["key"] == key:
            session = saved["session"]
            assert digest_file(snapshots[entry["source_snapshot_sha256"]]) == session["source_file_sha256"], "Cached audit source bytes changed"
            active = json.loads((args.publication / "publication.json").read_bytes())["sessions"][entry["session_id"]]
            manifest_path = args.publication / active["manifest"]
            assert digest_file(manifest_path) == active["sha256"]
            for name, expected in json.loads(manifest_path.read_bytes())["files"].items():
                assert digest_file(args.publication / name) == expected, "Cached audit publication bytes changed"
        else:
            session = audit_session(entry, args.publication, snapshots[entry["source_snapshot_sha256"]])
            cache.write_bytes(gzip.compress(json.dumps({"key": key, "session": session}, allow_nan=False, separators=(",", ":")).encode(), mtime=0))
        sessions.append(session)
        e = session["summary"]["timing_eligible"]
        print(f"{entry['session_id']}: {e['telemetry_laps']}/{e['laps']} telemetry; first failures {e['first_failed_gate']}", flush=True)
    assert protected == {p: digest_file(ROOT / p) for p in PROTECTED}, "Runtime changed during audit"
    assert catalogue_hash == digest_file(args.publication / "publication.json"), "Active catalogue changed during audit"
    args.lap_ledger.parent.mkdir(parents=True, exist_ok=True)
    with args.lap_ledger.open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0, filename="") as compressed:
            for session in sessions:
                for record in session["laps"]:
                    compressed.write((json.dumps({"session_id": session["session_id"], **record}, allow_nan=False, separators=(",", ":")) + "\n").encode())
    audit = {"audit_version": AUDIT_VERSION, "baseline_commit": baseline, "catalogue_sha256": catalogue_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(), "sessions": len(sessions),
        "scope": "All indexed laps; timing-eligible denominators preserve v5. Conditional downstream diagnostics and pair context are not graph acceptance.",
        "gate_definitions": GATES, "runtime_sha256": protected, "tier2_function_sha256": protected_functions(),
        "per_lap_ledger": {"path": args.lap_ledger.resolve().relative_to(ROOT).as_posix(), "sha256": digest_file(args.lap_ledger),
            "records": sum(len(s["laps"]) for s in sessions), "format": "gzip JSON Lines; derived diagnostics, no native sample arrays"},
        "by_year": {str(year): merge_summaries([s for s in sessions if s["year"] == year]) for year in sorted({s["year"] for s in sessions})},
        "totals": merge_summaries(sessions)}
    by_id = {s["session_id"]: s for s in sessions}
    for row in ledger["sessions"]:
        if row["session_id"] in by_id:
            session = by_id[row["session_id"]]
            row["gate_attribution"] = {"summary": session["summary"], "reference": session["reference"],
                "pair_gates": session["pair_gates"], "distributions": {name: distribution({int(k): v for k, v in values.items()}) for name, values in session["distribution_counts_us"].items()}}
    ledger["gate_attribution"] = audit
    atomic_json(args.ledger, ledger)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(audit), encoding="utf-8", newline="\n")
    print(f"Wrote Step 0 report for {len(sessions)} sessions / {audit['per_lap_ledger']['records']} indexed laps", flush=True)


if __name__ == "__main__":
    main()
