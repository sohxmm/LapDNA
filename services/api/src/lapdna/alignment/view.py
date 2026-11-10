"""V6 native views. No position, marker, reference or legacy gate dependencies."""
from bisect import bisect_left, bisect_right
import json

from lapdna.alignment.native import finite_number, utc_seconds
from lapdna.models import LapMetadata
from lapdna.view_models import CHANNELS, NativeLapView


class ViewUnavailable(ValueError):
    def __init__(self, gate, message):
        super().__init__(message)
        self.gate = gate


class CarStream:
    """Index the entire driver stream once; keep real padding beyond the v5 crop."""
    def __init__(self, rows):
        unique = {}
        self.conflicts = 0
        for row in rows:
            try:
                when = utc_seconds(row["date"])
            except (KeyError, TypeError, ValueError):
                continue
            gear, brake = row.get("n_gear"), row.get("brake")
            values = [finite_number(row.get("speed"), 0, 400),
                      finite_number(row.get("throttle"), 0, 100),
                      finite_number(row.get("rpm"), 0),
                      gear if type(gear) is int and 0 <= gear <= 8 else None,
                      brake == 100 if type(brake) in (int, float) and brake in (0, 100) else None]
            if when not in unique:
                unique[when] = values
            else:
                # Conflicting duplicate measurements are unknown, never first-wins.
                for i, value in enumerate(values):
                    if unique[when][i] != value:
                        unique[when][i] = None
                        self.conflicts += 1
        ordered = sorted(unique.items())
        self.times = [t for t, _ in ordered]
        self.values = [v for _, v in ordered]

    def view(self, metadata, start, end):
        if isinstance(metadata, dict):
            metadata = LapMetadata.model_validate_json(json.dumps(metadata))
        if end <= start:
            raise ViewUnavailable("timing_edges", "Source timing edges are not increasing.")
        first, last = bisect_right(self.times, start) - 1, bisect_left(self.times, end)
        if first < 0 or last >= len(self.times):
            raise ViewUnavailable("car_edges", "Native car samples do not bracket both timing edges.")
        times = [(t - start) * 1000 for t in self.times[first:last + 1]]
        duration = (end - start) * 1000
        values = self.values[first:last + 1]
        channels = {name: [v[i] for v in values] for i, name in enumerate(CHANNELS)}
        spans = []
        for name in CHANNELS:
            continuous = name not in ("gear", "brake")
            threshold = 750.0001 if name == "speed_kph" else 500.0001
            good = [i for i, v in enumerate(channels[name]) if v is not None]
            intervals = []
            if not good:
                intervals = [(0., duration, False)]
            else:
                if times[good[0]] > 0:
                    intervals.append((0., times[good[0]], False))
                for left, right in zip(good, good[1:]):
                    dt = times[right] - times[left]
                    if dt > threshold or right != left + 1:
                        intervals.append((times[left], times[right], continuous and dt <= 2000.0001))
                if times[good[-1]] < duration:
                    intervals.append((times[good[-1]], duration, False))
            for a, b, bridged in intervals:
                a, b = max(0., a), min(duration, b)
                if b > a:
                    spans.append({"channel": name, "start_elapsed_ms": a, "end_elapsed_ms": b,
                        "state": "bridged" if bridged else "gap",
                        "render_hint": "dashed_connector" if bridged else "blank_gap" if continuous else "hatched_no_data",
                        "reason": "Derived linear connector between native observations; not a measurement." if bridged else
                                  "No supported native samples across this interval; do not hold discrete values."})
        return NativeLapView(metadata=metadata, source_duration_ms=duration, elapsed_ms=times,
            channels=channels, sample_masks={name: ["gap" if v is None else "measured" for v in channels[name]] for name in CHANNELS},
            interpolation={name: "none" if name in ("gear", "brake") else "linear_connector" for name in CHANNELS},
            spans=spans, warnings=["Conflicting duplicate values were replaced by null."] if self.conflicts else [])
