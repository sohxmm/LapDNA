"""Linear native-speed progress, explicit bridges and endpoint-model bounds.

Uses the v5 integration/elapsed interpolation primitives. The prescribed bound
is a diagnostic of the endpoint-speed model, not a physical/probability bound.
No sector fitting or position estimator is performed here.
"""
from bisect import bisect_left, bisect_right

from lapdna.alignment.native import integrated_distance, integral_at, linear
from lapdna.alignment.view import ViewUnavailable
from lapdna.view_models import AlignedLap, AlignedDelta, SectorAnnotation


def prepare_progress(view, length=None):
    selected = [(t / 1000, v) for t, v in zip(view.elapsed_ms, view.channels.speed_kph) if v is not None]
    times = [t for t, _ in selected]
    speeds = [v for _, v in selected]
    end = view.source_duration_ms / 1000
    first, last = bisect_right(times, 0.) - 1, bisect_left(times, end)
    if first < 0 or last >= len(times):
        raise ViewUnavailable("speed_edges", "Valid native speed does not bracket both timing edges.")
    times, speeds = times[first:last + 1], speeds[first:last + 1]
    intervals = [b - a for a, b in zip(times, times[1:])]
    if any(dt > 2.0000001 for dt in intervals):
        raise ViewUnavailable("speed_gap_over_2s", "A native speed interval exceeds 2.0 s; measured channels remain viewable.")
    integrated = integrated_distance(times, speeds)
    offset = integral_at(0., times, speeds, integrated)
    actual = integral_at(end, times, speeds, integrated) - offset
    if actual <= 0:
        raise ViewUnavailable("progress", "Integrated lap length is nonpositive.")
    canonical = actual if length is None else length
    scale = canonical / actual
    internal = [i for i, t in enumerate(times) if 0 < t < end]
    distance = [0., *[(integrated[i] - offset) * scale for i in internal], canonical]
    elapsed = [0., *[times[i] * 1000 for i in internal], view.source_duration_ms]
    if any(b <= a for a, b in zip(distance, distance[1:])):
        raise ViewUnavailable("progress", "Stationary or non-increasing integrated progress.")
    bridges = []
    for i, dt in enumerate(intervals):
        if dt <= .7500001:
            continue
        start_gap, end_gap = max(0., times[i]), min(end, times[i + 1])
        if end_gap <= start_gap:
            continue
        full = dt * abs(speeds[i + 1] - speeds[i]) / 7.2
        bridges.append({"start_elapsed_ms": start_gap * 1000, "end_elapsed_ms": end_gap * 1000,
            "native_interval_ms": dt * 1000, "speed_before_kph": speeds[i], "speed_after_kph": speeds[i + 1],
            "full_interval_bound_m": full, "in_lap_bound_m": full * (end_gap - start_gap) / dt,
            "excluded_from_analysis": True})
    # Allocate each native interval bound linearly over its overlap with the lap.
    cumulative = [sum(g["in_lap_bound_m"] * max(0., min(1., (t - g["start_elapsed_ms"]) /
                    (g["end_elapsed_ms"] - g["start_elapsed_ms"]))) for g in bridges) for t in elapsed]
    total = cumulative[-1]
    if total >= actual:
        raise ViewUnavailable("uncertainty_denominator", "The accumulated endpoint-model bound reaches the integrated length.")
    lower, upper = envelopes(distance, cumulative, actual, canonical)
    # The common lap edges are exact constraints. Cumulative raw bound is NOT reset.
    lower[0] = upper[0] = 0.
    lower[-1] = upper[-1] = canonical
    return AlignedLap(elapsed_ms=elapsed, distance_m=distance, cumulative_bound_m=cumulative,
        distance_lower_m=lower, distance_upper_m=upper, integrated_length_m=actual, scale_factor=scale,
        source_duration_ms=view.source_duration_ms, endpoint_residual_ms=view.source_duration_ms - view.metadata.lap_time_ms,
        bridges=bridges, sector_annotations=[])


def envelopes(distance, cumulative, actual, length):
    """Propagate raw distance error through distance normalization, not time fitting."""
    total = cumulative[-1]
    lower, upper = [], []
    for d, b in zip(distance, cumulative):
        raw = d * actual / length
        lo = max(0., raw - b) / (actual + total) * length
        hi = min(1., (raw + b) / (actual - total)) * length
        lower.append(max(lower[-1] if lower else 0., min(d, lo)))
        upper.append(max(d, hi))
    return lower, upper


def crossing_range(lap, target, length):
    if target == 0:
        return 0., 0.
    if target == length:
        return lap.source_duration_ms, lap.source_duration_ms
    # Invert UNPINNED envelopes: forcing the finish node before inversion would
    # invent confidence by interpolating the exact edge constraint backwards.
    lower, upper = envelopes(lap.distance_m, lap.cumulative_bound_m, lap.integrated_length_m, length)
    def crossing(curve):
        if target > curve[-1]:
            return lap.source_duration_ms
        right = bisect_left(curve, target)
        if right == 0:
            return lap.elapsed_ms[0]
        left = right - 1
        return lap.elapsed_ms[left] + (target - curve[left]) / (curve[right] - curve[left]) * (lap.elapsed_ms[right] - lap.elapsed_ms[left])
    return crossing(upper), crossing(lower)


def annotate_sectors(lap, metadata, boundaries, is_reference=False):
    official = 0.
    for sector, distance in enumerate(boundaries, 1):
        official += metadata.sector_times_ms[sector - 1]
        estimate = linear(lap.distance_m, lap.elapsed_ms, distance)
        residual = estimate - official
        lap.sector_annotations.append(SectorAnnotation(sector=sector, official_elapsed_ms=official,
            estimated_elapsed_ms=estimate, residual_ms=residual,
            grade="C" if abs(residual) > 150.0001 else "ungraded",
            basis="reference_timing_constraint" if is_reference else "shared_progress_estimate"))


def align_pair(view_a, view_b, reference, boundaries):
    length = reference["length_m"]
    a, b = prepare_progress(view_a, length), prepare_progress(view_b, length)
    annotate_sectors(a, view_a.metadata, boundaries, view_a.metadata.lap_id == reference["lap_id"])
    annotate_sectors(b, view_b.metadata, boundaries, view_b.metadata.lap_id == reference["lap_id"])
    grid = [float(x) for x in range(0, int(length), 5)] + [length]
    ta = [linear(a.distance_m, a.elapsed_ms, x) for x in grid]
    tb = [linear(b.distance_m, b.elapsed_ms, x) for x in grid]
    delta = [b - a for a, b in zip(ta, tb)]
    ranges_a = [crossing_range(a, x, length) for x in grid]
    ranges_b = [crossing_range(b, x, length) for x in grid]
    lo = [min(d, rb[0] - ra[1]) for d, ra, rb in zip(delta, ranges_a, ranges_b)]
    hi = [max(d, rb[1] - ra[0]) for d, ra, rb in zip(delta, ranges_a, ranges_b)]
    grade_c = any(s.grade == "C" for lap in (a, b) for s in lap.sector_annotations)
    warnings = ["Endpoint-speed model band; not a calibrated probability interval or independent validation."]
    if a.bridges or b.bridges:
        warnings.append("Flagged speed bridges are derived and excluded from corner observations.")
    if any(abs(lap.scale_factor - 1) > .0300001 for lap in (a, b)):
        warnings.append("Integrated distance normalization differs from the reference by over 3%; time was not rescaled.")
    return AlignedDelta(reference=reference, distance_m=grid, elapsed_a_ms=ta, elapsed_b_ms=tb,
        delta_ms=delta, delta_lower_ms=lo, delta_upper_ms=hi, lap_a=a, lap_b=b,
        recorded_lap_gap_ms=view_b.metadata.lap_time_ms - view_a.metadata.lap_time_ms,
        quality_grade="C" if grade_c else "ungraded", warnings=warnings)
