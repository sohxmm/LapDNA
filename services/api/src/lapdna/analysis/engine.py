"""Pure comparison calculations over a frozen, offline-normalized publication."""

from bisect import bisect_left
from hashlib import sha256
import json
from math import ceil, floor

from lapdna.alignment.native import linear
from lapdna.models import ComparisonArtifact, SectorComparisonArtifact

METHOD = "distance-v5-openf1-native-composite"
LEGACY_METHOD = "distance-v4-openf1-native-composite"
PIPELINE = "native-composite-3"
SEVERITY = {"pass": 0, "warn": 1, "block": 2}


class ComparisonUnavailable(ValueError):
    """A concise, safe reason for an intentionally withheld comparison tier."""


def canonical_hash(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def worst(*statuses):
    return max(statuses, key=SEVERITY.__getitem__)


def grade(value: float | None, passing: float, warning: float):
    return "block" if value is None or abs(value) > warning + 1e-7 else "warn" if abs(value) > passing + 1e-7 else "pass"


def check(driver, metric, basis, official, observed, passing=50., warning=150.):
    residual = observed - official if observed is not None else None
    return {"driver": driver, "metric": metric, "basis": basis, "official_ms": official,
            "observed_ms": observed, "residual_ms": residual,
            "status": grade(residual, passing, warning)}


def comparison_identity(publication: dict, a: str, b: str, tier: str) -> str:
    tag = canonical_hash(publication["session"]["session_id"])[:8]
    return "cmp_" + tag + "_" + canonical_hash({"laps": sorted((a, b)), "publication": publication["publication_sha256"],
                                    "method": publication.get("method", LEGACY_METHOD), "pipeline": PIPELINE, "schema": "1.3.0", "tier": tier})[:24]


def pairing(a, b, records=()):
    cross = a["phase"] != b["phase"]
    warnings = []
    if cross:
        warnings.append(f"Different qualifying phases: {a['phase']} and {b['phase']}; track evolution and conditions may differ.")
    if a["compound"] != b["compound"]:
        warnings.append(f"Different tyre compounds: {a['driver_code']} {a['compound']}, {b['driver_code']} {b['compound']}.")
    if any(lap["compound"] in ("INTERMEDIATE", "WET") for lap in (a, b)):
        warnings.append("Selected laps include wet-weather tyres; track grip and conditions are not controlled.")
    contexts = [record.get("weather_context", "unknown") for record in records]
    if "rain_reported" in contexts:
        warnings.append("The source reported rainfall within 90 seconds of the selected lap windows; this is context, not a measurement of track grip.")
    if "unknown" in contexts:
        warnings.append("Rainfall context for one or both selected laps is unavailable; no dry-track assumption is made.")
    if a.get("tyre_life_laps") != b.get("tyre_life_laps"):
        warnings.append("The selected laps have different reported tyre ages.")
    if a.get("lap_start_utc") and b.get("lap_start_utc"):
        from lapdna.alignment.native import utc_seconds
        separation = abs(utc_seconds(a["lap_start_utc"]) - utc_seconds(b["lap_start_utc"]))
        if separation > 120:
            warnings.append(f"Lap starts were {separation / 60:.1f} minutes apart; conditions are not controlled.")
    return {"mode": "cross_phase" if cross else "same_phase", "warnings": warnings}


def provenance(publication: dict, telemetry: bool):
    value = {key: publication["provenance"][key] for key in (
        "source", "fastf1_version", "provider_version", "source_retrieved_at", "source_urls",
        "verification_scope", "components", "source_session", "source_snapshot_sha256", "generated_at",
    )}
    value.update(pipeline_version=PIPELINE, methodology_version=publication.get("method", LEGACY_METHOD))
    if telemetry:
        value.update(reference_sha256=publication["reference_sha256"],
                     circuit_revision=publication.get("circuit_revision", "monza-2024-projected-v1"), reference_lap_id=publication["reference_lap_id"])
    return value


def sector_result(publication: dict, first: str, second: str, reason: str):
    a, b = publication["laps"][first]["metadata"], publication["laps"][second]["metadata"]
    checks = [check(slot, "sector_sum", "timing_record_consistency", lap["lap_time_ms"],
                    sum(lap["sector_times_ms"]), 3., 20.) for slot, lap in (("A", a), ("B", b))]
    if any(item["status"] == "block" for item in checks):
        raise ComparisonUnavailable("Recorded sector timing does not reconcile with the lap duration; this pair is unavailable.")
    delta = [right - left for left, right in zip(a["sector_times_ms"], b["sector_times_ms"])]
    result = {"schema_version": "1.3.0", "comparison_id": comparison_identity(publication, first, second, "sector_only"),
              "detail_level": "sector_only", "session": publication["session"], "lap_a": a, "lap_b": b,
              "pairing": pairing(a, b, [publication["laps"][first], publication["laps"][second]]), "provenance": provenance(publication, False),
              "quality": {"status": worst(*(item["status"] for item in checks)),
                          "warnings": ["Sector timing only; no continuous curve or corner attribution is supported for this pair."],
                          "checks": checks}, "fallback_reason": reason[:600], "sector_delta_ms": delta,
              "cumulative_delta_ms": [sum(delta[:i + 1]) for i in range(3)]}
    return SectorComparisonArtifact.model_validate_json(json.dumps(result, allow_nan=False))


def quality(publication, a, b):
    checks = []
    for slot, record in (("A", a), ("B", b)):
        lap = record["metadata"]
        checks.extend(check(slot, "sector_sum", "timing_record_consistency", lap["lap_time_ms"],
                            sum(lap["sector_times_ms"]), 3., 20.) for _ in range(1))
        checks.append(check(slot, "sliced_duration", "timing_record_consistency", lap["lap_time_ms"],
                            record["channels"]["time_raw_ms"][-1], 3., 20.))
        for i, metric in enumerate(("cumulative_sector_1", "cumulative_sector_2")):
            basis = "calibration" if lap["lap_id"] == publication["reference_lap_id"] else "cross_lap_consistency"
            observed = linear(publication["distance_m"], record["channels"]["time_raw_ms"], publication["sector_boundaries_m"][i])
            checks.append(check(slot, metric, basis, sum(lap["sector_times_ms"][:i + 1]), observed))
    for i, metric in enumerate(("cumulative_sector_1", "cumulative_sector_2", "lap_gap")):
        s = publication["sector_boundaries_m"][i] if i < 2 else publication["distance_m"][-1]
        observed = (linear(publication["distance_m"], b["channels"]["time_raw_ms"], s)
                    - linear(publication["distance_m"], a["channels"]["time_raw_ms"], s))
        official = (sum(b["metadata"]["sector_times_ms"][:i + 1]) - sum(a["metadata"]["sector_times_ms"][:i + 1])) if i < 2 else b["metadata"]["lap_time_ms"] - a["metadata"]["lap_time_ms"]
        checks.append(check("pair", metric, "timing_constraint" if i == 2 else "cross_lap_consistency", official, observed,
                            3. if i == 2 else 50., 20. if i == 2 else 150.))
    scale = [grade(abs(record["scale_factor"] - 1), .01, .03) for record in (a, b)]
    gaps = [grade(record["max_native_gap_ms"], 500., 750.) for record in (a, b)]
    status = worst(*(item["status"] for item in checks), *scale, *gaps)
    warnings = ["Approximate local timing from native public telemetry; this is not causal proof or surveyed track position.",
                "Timing clocks/eligibility are from the identity-matched TracingInsights archive; car and location streams are from OpenF1.",
                "Start/finish values are timing constraints; endpoint agreement does not independently validate the interior curve."]
    if publication["provenance"]["source"] == "fastf1":
        warnings[1] = "Timing clocks/eligibility use the pinned FastF1 parser; native car/location rows are decoded before library default filling."
    if any(item["status"] == "warn" for item in checks):
        warnings.append("Interior or timing residuals exceed a pass threshold; inspect the unadjusted checks in Data details.")
    if "warn" in gaps:
        warnings.append("Some native speed gaps exceed 0.50 s; affected regions cannot support written observations.")
    if "warn" in scale:
        warnings.append("A lap's integrated distance differs from the reference by more than 1%.")
    return {"status": worst(status, "warn"), "warnings": warnings, "checks": checks,
            "native_samples_a": a["native_count"], "native_samples_b": b["native_count"],
            "max_native_gap_ms_a": a["max_native_gap_ms"], "max_native_gap_ms_b": b["max_native_gap_ms"],
            "distance_a": {"integrated_length_m": a["integrated_length_m"], "scale_factor": a["scale_factor"]},
            "distance_b": {"integrated_length_m": b["integrated_length_m"], "scale_factor": b["scale_factor"]}}


def regional_gain(grid, delta, start, end):
    left, right = linear(grid, delta, start), linear(grid, delta, end)
    return right - left if left is not None and right is not None else None


def sensitivity(grid, delta, start, end):
    values = [regional_gain(grid, delta, max(0., start + left), min(grid[-1], end + right))
              for left in (-10, 0, 10) for right in (-10, 0, 10)
              if max(0., start + left) < min(grid[-1], end + right)]
    if any(value is None for value in values):
        return None
    return {"minimum_ms": min(values), "maximum_ms": max(values)}


def _evidence(identifier, metric, unit, region, a, b, field, value_a, value_b, interval_a=None, interval_b=None):
    sa, sb = a["metrics"][region["segment_id"]][field], b["metrics"][region["segment_id"]][field]
    return {"evidence_id": identifier, "metric": metric, "unit": unit,
            "start_m": region["start_m"], "end_m": region["end_m"], "value_a": value_a, "value_b": value_b,
            "difference_b_minus_a": value_b - value_a if value_a is not None and value_b is not None else None,
            "native_samples_a": sa["count"], "native_samples_b": sb["count"],
            "max_support_span_ms_a": sa["span_ms"], "max_support_span_ms_b": sb["span_ms"],
            "interval_a": interval_a, "interval_b": interval_b,
            "difference_interval_b_minus_a": [interval_b[0] - interval_a[1], interval_b[1] - interval_a[0]]
            if interval_a is not None and interval_b is not None else None}


def summaries(publication, a, b, delta):
    grid = publication["distance_m"]
    segments, evidence, supported = [], [], {}
    for region in publication["regions"]:
        identifier = region["segment_id"]
        gain = regional_gain(grid, delta, region["start_m"], region["end_m"])
        bounds = sensitivity(grid, delta, region["start_m"], region["end_m"])
        sa, sb = a["metrics"][identifier]["speed"], b["metrics"][identifier]["speed"]
        enough = min(sa["count"], sb["count"]) >= 5 and max(sa["span_ms"], sb["span_ms"]) <= 500.0001
        eid = "gain_" + identifier
        ids = [eid]
        duration_a = regional_gain(grid, a["channels"]["time_raw_ms"], region["start_m"], region["end_m"])
        duration_b = regional_gain(grid, b["channels"]["time_raw_ms"], region["start_m"], region["end_m"])
        evidence.append(_evidence(eid, "segment_gain", "ms", region, a, b, "speed", duration_a, duration_b))
        if enough:
            eid = "min_" + identifier
            evidence.append(_evidence(eid, "minimum_speed", "km/h", region, a, b, "speed", sa["minimum"], sb["minimum"]))
            ids.append(eid)
            for field, metric, unit, key in (("brake", "brake_onset", "m", "onset"),
                                             ("throttle", "throttle_pickup", "m", "pickup")):
                first, second = a["metrics"][identifier][field], b["metrics"][identifier][field]
                if first.get(key) is not None and second.get(key) is not None and min(first["count"], second["count"]) >= 3:
                    eid = f"{field}_{identifier}"
                    evidence.append(_evidence(eid, metric, unit, region, a, b, field, None, None,
                                              first[key], second[key]))
                    ids.append(eid)
        segments.append({**region, "gain_ms": gain, "gain_sensitivity_ms": bounds,
                         "quality_status": "warn" if enough else "block", "evidence_ids": ids})
        supported[identifier] = enough
    categories = []
    for band in ("low", "medium", "high"):
        expected = [item for item in segments if item["speed_class"] == band]
        included = [item for item in expected if supported[item["segment_id"]] and item["gain_sensitivity_ms"] is not None]
        totals = [sum(max(item["gain_ms"], 0) for item in included), sum(max(-item["gain_ms"], 0) for item in included)]
        lower = sum(item["gain_sensitivity_ms"]["minimum_ms"] for item in included)
        upper = sum(item["gain_sensitivity_ms"]["maximum_ms"] for item in included)
        a_wins = b_wins = 0
        for item in included:
            lo, hi = item["gain_sensitivity_ms"]["minimum_ms"], item["gain_sensitivity_ms"]["maximum_ms"]
            material = abs(item["gain_ms"]) >= max(30., 2 * (hi - lo))
            a_wins += int(material and lo > 0)
            b_wins += int(material and hi < 0)
        coverage = sum(item["end_m"] - item["start_m"] for item in included) / sum(item["end_m"] - item["start_m"] for item in expected) if expected else 0.
        net = totals[0] - totals[1]
        assessment = "insufficient"
        if included and coverage >= .8:
            assessment = "balanced" if not a_wins and not b_wins else "mixed"
            sign_wins = a_wins if net > 0 else b_wins
            if (len(included) >= 2 and lower * upper > 0 and abs(net) >= max(30., 2 * (upper - lower))
                    and sign_wins >= 2 and sign_wins * 3 >= (a_wins + b_wins) * 2):
                assessment = "a_advantage" if net > 0 else "b_advantage"
        categories.append({"speed_class": band, "included_segment_ids": [item["segment_id"] for item in included],
                           "excluded_segment_ids": [item["segment_id"] for item in expected if item not in included],
                           "independent_units": len(included), "distance_coverage": coverage,
                           "gains_a_ms": totals[0] if included else None, "gains_b_ms": totals[1] if included else None,
                           "net_gain_ms": net if included else None, "a_wins": a_wins, "b_wins": b_wins,
                           "neutral_units": len(included) - a_wins - b_wins,
                           "sensitivity": {"minimum_ms": lower, "maximum_ms": upper} if included else None,
                           "assessment": assessment, "evidence_ids": ["gain_" + item["segment_id"] for item in included]})
    observations = []
    candidates = []
    for item in segments:
        bounds = item["gain_sensitivity_ms"]
        if not supported[item["segment_id"]] or bounds is None:
            continue
        lo, hi = bounds["minimum_ms"], bounds["maximum_ms"]
        if lo * hi <= 0 or abs(item["gain_ms"]) < max(30., 2 * (hi - lo)):
            continue
        candidates.append(item)
    candidates.sort(key=lambda item: (-abs(item["gain_ms"]), item["start_m"]))
    chosen = []
    for kind in ("corner", "straight"):
        match = next((item for item in candidates if (item["kind"] == "straight") == (kind == "straight")), None)
        if match is not None:
            chosen.append(match)
    chosen.extend(item for item in candidates if item not in chosen)
    evidence_map = {item["evidence_id"]: item for item in evidence}
    for region in chosen[:3]:
        winner = a if region["gain_ms"] > 0 else b
        loser = b if region["gain_ms"] > 0 else a
        text = f"{winner['metadata']['driver_code']} gained an estimated {abs(region['gain_ms']) / 1000:.2f} s over {loser['metadata']['driver_code']} through {region['label']}."
        speed = evidence_map.get("min_" + region["segment_id"])
        if speed is not None:
            text += f" Minimum recorded speeds in this window were {a['metadata']['driver_code']} {speed['value_a']:.0f} and {b['metadata']['driver_code']} {speed['value_b']:.0f} km/h."
        brake = evidence_map.get("brake_" + region["segment_id"])
        if brake is not None:
            lo, hi = brake["difference_interval_b_minus_a"]
            if lo > 0 or hi < 0:
                later = b if lo > 0 else a
                first, last = sorted((abs(lo), abs(hi)))
                text += f" {later['metadata']['driver_code']}'s observed brake-on bracket was about {floor(first / 5) * 5:.0f}–{ceil(last / 5) * 5:.0f} m later."
        observations.append({"observation_id": "obs_" + region["segment_id"], "template_id": "speed_pattern",
                             "segment_id": region["segment_id"], "text": text, "evidence_ids": region["evidence_ids"]})
    bits = []
    for row in categories:
        if row["net_gain_ms"] is not None:
            winner = a if row["net_gain_ms"] >= 0 else b
            count = row["independent_units"]
            if abs(row["net_gain_ms"]) < 5:
                bits.append(f"{row['speed_class']}: negligible estimated net ({count} supported regions)")
            elif row["assessment"].endswith("_advantage"):
                bits.append(f"{row['speed_class']}: {winner['metadata']['driver_code']} advantage ≈{abs(row['net_gain_ms']) / 1000:.2f} s ({count} regions)")
            else:
                assessment = "insufficient pattern evidence" if row["assessment"] == "insufficient" else row["assessment"]
                bits.append(f"{row['speed_class']}: {assessment}, net ≈{abs(row['net_gain_ms']) / 1000:.2f} s toward {winner['metadata']['driver_code']} ({count} regions)")
    mixed = sum(item["speed_class"] in ("mixed", "unknown") for item in segments)
    text = "; ".join(bits) + "." if bits else "No corner-speed category has enough supported regions for a comparison."
    if mixed:
        text += f" {mixed} mixed/unknown complexes remain outside the class totals."
    pattern = "mixed" if any(row["assessment"] in ("mixed", "a_advantage", "b_advantage") for row in categories) else "insufficient"
    analysis = {"categories": categories, "classification_rule": "reference_apex_minimum_v1",
                "medium_from_kph": 150., "high_from_kph": 250., "pattern": pattern,
                "pattern_driver": None, "text": text[:600], "evidence_ids": [eid for row in categories for eid in row["evidence_ids"]],
                "limitations": ["Class totals describe only these selected laps and the supported reference windows.",
                                "Corner classes use the frozen reference lap and its conditions; track grip is not measured or controlled.",
                                "Public brake is an on/off signal; steering angle and brake pressure are unavailable.",
                                "One high-speed region cannot establish a consistent class-wide advantage."]}
    if publication.get("profile") == "marker-windows-v1":
        analysis["limitations"].insert(0, "Turn vicinities are fixed ±120 m marker windows, merged where overlapping; they are approximate analysis zones, not measured corner entry/exit boundaries.")
    return segments, evidence, observations, analysis


def build_comparison(publication: dict, lap_a: str, lap_b: str, detail_level="auto"):
    first, second = sorted((lap_a, lap_b))
    a, b = publication["laps"][first], publication["laps"][second]
    if detail_level not in ("auto", "telemetry", "sector_only"):
        raise ComparisonUnavailable("Unsupported comparison detail level.")
    if first == second or a["metadata"]["driver_number"] == b["metadata"]["driver_number"]:
        raise ComparisonUnavailable("Choose two different drivers.")
    missing = "channels" not in a or "channels" not in b
    if missing and detail_level == "telemetry":
        raise ComparisonUnavailable("One or both selected laps lack a verified distance alignment; use recorded sectors or another actual lap.")
    if detail_level == "sector_only" or missing:
        return sector_result(publication, first, second,
                             "Sector timing selected; this view contains recorded split differences only." if detail_level == "sector_only" else
                             "One or both selected laps lack a verified distance alignment; recorded sectors remain available.")
    report = quality(publication, a, b)
    if report["status"] == "block":
        if detail_level == "telemetry":
            raise ComparisonUnavailable("The raw interior timing, distance scale or native gaps block telemetry for this pair.")
        reasons = [f"{item['driver']} {item['metric']}: {item['residual_ms']:.1f} ms" for item in report["checks"] if item["status"] == "block"]
        return sector_result(publication, first, second, "Telemetry quality blocked: " + "; ".join(reasons or ["distance scale/native gap exceeded threshold"]))
    grid = publication["distance_m"]
    delta = [right - left if left is not None and right is not None else None
             for left, right in zip(a["channels"]["time_raw_ms"], b["channels"]["time_raw_ms"])]
    segments, evidence, observations, analysis = summaries(publication, a, b, delta)
    bins = []
    start = 0.
    while start < grid[-1]:
        end = min(start + 100., grid[-1])
        bins.append({"source": "derived_telemetry", "start_m": start, "end_m": end,
                     "gain_ms": regional_gain(grid, delta, start, end)})
        start = end
    def channels(record):
        raw_fields = {"speed_kph": "speed", "throttle_pct": "throttle", "gear": "n_gear", "brake": "brake"}
        if publication["provenance"]["source"] == "fastf1":
            raw_fields = {"speed_kph": "Speed", "throttle_pct": "Throttle", "gear": "nGear", "brake": "Brake"}
        return {name: {"status": "measured", "source_channel": raw, "reason": None}
                if any(value is not None for value in record["channels"][name]) else
                {"status": "missing", "source_channel": None, "reason": "No valid native source observations for this channel."}
                for name, raw in raw_fields.items()}
    result = {"schema_version": "1.3.0", "comparison_id": comparison_identity(publication, first, second, "telemetry"),
              "detail_level": "telemetry", "session": publication["session"], "lap_a": a["metadata"], "lap_b": b["metadata"],
              "pairing": pairing(a["metadata"], b["metadata"], [a, b]), "provenance": provenance(publication, True),
              "distance_m": grid, "channels_a": a["channels"], "channels_b": b["channels"],
              "channel_provenance_a": channels(a), "channel_provenance_b": channels(b),
              "geometry": publication["geometry"], "delta_ms": delta, "valid": [value is not None for value in delta],
              "sector_boundaries_m": publication["sector_boundaries_m"], "quality": report,
              "segments": segments, "corners": publication["corners"], "estimated_minisectors": bins,
              "analysis": analysis, "evidence": evidence, "observations": observations,
              "insufficient_evidence_reason": None if len(observations) == 3 else
              f"{len(observations)} distinct regions passed native support, gain materiality and boundary-sensitivity checks; no additional observations are inferred."}
    return ComparisonArtifact.model_validate_json(json.dumps(result, allow_nan=False))
