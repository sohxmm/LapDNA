"""Integrate native speed exactly at timing edges; never fit elapsed time to sectors."""

from bisect import bisect_left, bisect_right
from datetime import datetime
from math import isfinite


class AlignmentError(ValueError):
    pass


def utc_seconds(value: str) -> float:
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise AlignmentError("source timestamp lacks timezone")
    return stamp.timestamp()


def finite_number(value, minimum=0.0, maximum=float("inf")):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if isfinite(value) and minimum <= value <= maximum else None


def native_car(rows: list[dict], start: float, end: float) -> dict:
    """Retain one native speed observation outside each edge and explicit channel nulls."""
    ordered = []
    for row in rows:
        try:
            time = utc_seconds(row["date"])
        except (KeyError, TypeError, ValueError):
            continue
        if not start - 1 <= time <= end + 1:
            continue
        speed = finite_number(row.get("speed"), 0, 400)
        throttle = finite_number(row.get("throttle"), 0, 100)
        gear = row.get("n_gear")
        gear = gear if type(gear) is int and 0 <= gear <= 8 else None
        raw_brake = row.get("brake")
        brake = raw_brake == 100 if type(raw_brake) in (int, float) and raw_brake in (0, 100) else None
        ordered.append((time, speed, throttle, gear, brake))
    ordered.sort(key=lambda item: item[0])
    unique = []
    for row in ordered:
        if unique and row[0] == unique[-1][0]:
            if row != unique[-1]:
                raise AlignmentError("conflicting native car records at one timestamp")
            continue
        unique.append(row)
    # Invalid speed is absent evidence, never clamped. Its missing span remains
    # represented by the gap between the remaining source observations.
    usable = [row for row in unique if row[1] is not None]
    times = [row[0] for row in usable]
    first = bisect_right(times, start) - 1
    last = bisect_left(times, end)
    if first < 0 or last >= len(usable) or end <= start:
        raise AlignmentError("native speed does not bracket both lap timing edges")
    selected = usable[first:last + 1]
    if len(selected) < 2:
        raise AlignmentError("insufficient native speed samples")
    gap = max(b[0] - a[0] for a, b in zip(selected, selected[1:]))
    if gap > .7500001:
        raise AlignmentError(f"native speed gap {gap:.3f} s exceeds 0.75 s")
    return {"time": [row[0] for row in selected], "speed_kph": [row[1] for row in selected],
            "throttle_pct": [row[2] for row in selected], "gear": [row[3] for row in selected],
            "brake": [row[4] for row in selected], "max_gap_ms": gap * 1000,
            "native_count": sum(start <= row[0] <= end for row in selected)}


def integrated_distance(times: list[float], speeds: list[float]) -> list[float]:
    if len(times) != len(speeds) or len(times) < 2:
        raise AlignmentError("native time/speed lengths disagree")
    result = [0.0]
    for i in range(1, len(times)):
        span = times[i] - times[i - 1]
        if span <= 0 or not isfinite(span):
            raise AlignmentError("native clock must strictly increase")
        result.append(result[-1] + (speeds[i - 1] + speeds[i]) / 7.2 * span)
    return result


def integral_at(time: float, times: list[float], speeds: list[float], distance: list[float]) -> float:
    i = bisect_right(times, time) - 1
    if i < 0 or time > times[-1]:
        raise AlignmentError("distance integration would extrapolate")
    if i == len(times) - 1:
        return distance[i]
    elapsed = time - times[i]
    acceleration = (speeds[i + 1] - speeds[i]) / (times[i + 1] - times[i])
    return distance[i] + (speeds[i] * elapsed + acceleration * elapsed * elapsed / 2) / 3.6


def linear(xs: list[float], ys: list, x: float, *, step=False, max_gap=None):
    i = bisect_right(xs, x) - 1
    if i < 0 or x > xs[-1]:
        return None
    if xs[i] == x or i == len(xs) - 1:
        return ys[i]
    if max_gap is not None and xs[i + 1] - xs[i] > max_gap:
        return None
    if ys[i] is None or (not step and ys[i + 1] is None):
        return None
    if step:
        return ys[i]
    return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])


def prepare_lap(rows: list[dict], start: float, end: float, length: float | None = None) -> dict:
    native = native_car(rows, start, end)
    times, speeds = native["time"], native["speed_kph"]
    integrated = integrated_distance(times, speeds)
    offset = integral_at(start, times, speeds, integrated)
    actual_length = integral_at(end, times, speeds, integrated) - offset
    if actual_length <= 0:
        raise AlignmentError("integrated lap length is nonpositive")
    canonical_length = actual_length if length is None else length
    scale = canonical_length / actual_length
    internal = [i for i, time in enumerate(times) if start < time < end]
    sample_times = [start, *[times[i] for i in internal], end]
    sample_distance = [0.0, *[(integrated[i] - offset) * scale for i in internal], canonical_length]
    if any(b <= a for a, b in zip(sample_distance, sample_distance[1:])):
        raise AlignmentError("stationary or non-increasing lap progress")
    native["distance_m"] = [(value - offset) * scale for value in integrated]
    native["elapsed_ms"] = [(time - start) * 1000 for time in times]
    return {"native": native, "sample_distance": sample_distance,
            "sample_elapsed_ms": [(time - start) * 1000 for time in sample_times],
            "integrated_length_m": actual_length, "scale_factor": scale,
            "start": start, "end": end, "length": canonical_length}


def elapsed_at(prepared: dict, distance: float) -> float | None:
    return linear(prepared["sample_distance"], prepared["sample_elapsed_ms"], distance)


def distance_at(prepared: dict, elapsed_ms: float) -> float | None:
    return linear(prepared["sample_elapsed_ms"], prepared["sample_distance"], elapsed_ms)


def aligned_channels(prepared: dict, grid: list[float]) -> dict:
    native = prepared["native"]
    times = native["time"]
    elapsed = [elapsed_at(prepared, distance) for distance in grid]
    result = {"time_raw_ms": elapsed}
    for field in ("speed_kph", "throttle_pct", "gear", "brake"):
        result[field] = [linear(times, native[field], prepared["start"] + time / 1000,
                               step=field in ("gear", "brake"),
                               max_gap=.75 if field == "speed_kph" else .50)
                         if time is not None else None for time in elapsed]
    return result


def support(prepared: dict, start_m: float, end_m: float, field="speed_kph") -> dict:
    native = prepared["native"]
    distances, times, values = native["distance_m"], native["elapsed_ms"], native[field]
    first, after = bisect_left(distances, start_m), bisect_right(distances, end_m)
    indices = [i for i in range(first, after) if values[i] is not None]
    lo, hi = max(0, first - 1), min(len(times) - 1, after)
    span = max((times[i + 1] - times[i] for i in range(lo, hi)), default=float("inf"))
    return {"count": len(indices), "span_ms": span,
            "minimum": min((values[i] for i in indices), default=None),
            "maximum": max((values[i] for i in indices), default=None)}
