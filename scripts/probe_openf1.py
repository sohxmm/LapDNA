"""Check historical source availability without importing/publishing a comparison."""
import argparse
import json
import math
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.openf1.org/v1/"
LIMIT = 4 * 1024 * 1024


def fetch(resource, params):
    url = BASE + resource + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "LapDNA-availability-probe/1"})
    with urlopen(request, timeout=20) as response:
        payload = response.read(LIMIT + 1)
    if len(payload) > LIMIT:
        raise ValueError("Probe response exceeded its size limit")
    rows = json.loads(payload)
    if not isinstance(rows, list):
        raise ValueError(f"Unexpected {resource} response")
    return rows


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def probe(year, circuit, driver):
    sessions = fetch("sessions", {"year": year, "circuit_short_name": circuit, "session_name": "Qualifying"})
    if len(sessions) != 1:
        raise ValueError("Expected one matching qualifying session")
    key = sessions[0]["session_key"]
    laps = fetch("laps", {"session_key": key, "driver_number": driver})
    sector_fields = [f"duration_sector_{i}" for i in range(1, 4)]
    complete = [lap for lap in laps if lap.get("date_start") and
                all(positive(lap.get(k)) for k in ["lap_duration", *sector_fields])]
    if not complete:
        raise ValueError("No returned lap has three positive sectors and a lap duration")
    lap = min(complete, key=lambda row: (row["lap_duration"], row["lap_number"]))
    start = datetime.fromisoformat(lap["date_start"])
    end = start + timedelta(seconds=lap["lap_duration"])
    car = fetch("car_data", {"session_key": key, "driver_number": driver,
                            "date>": start.isoformat(), "date<": end.isoformat()})
    # Verify filter behavior locally before reporting support.
    car = [row for row in car if row.get("date") and start <= datetime.fromisoformat(row["date"]) <= end]
    channels = [k for k in ("speed", "throttle", "n_gear", "brake", "rpm", "drs")
                if any(row.get(k) is not None for row in car)]
    return {
        "probe_only": True, "source": "openf1", "session_key": key,
        "circuit": circuit, "year": year, "driver_number": driver,
        "returned_laps": len(laps), "laps_with_three_sectors": len(complete),
        "sample_lap_number": lap["lap_number"], "reported_lap_seconds": lap["lap_duration"],
        "reported_sector_seconds": [lap[k] for k in sector_fields],
        "sector_sum_residual_ms": round(1000 * (sum(lap[k] for k in sector_fields) - lap["lap_duration"]), 3),
        "segment_status_arrays_present": all(isinstance(lap.get(f"segments_sector_{i}"), list) for i in range(1, 4)),
        "car_samples_in_window": len(car), "available_car_channels": channels,
        "scope": "Availability only. No phase/eligibility, alignment, official-document or comparison validation.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--circuit", choices=("Monza", "Silverstone", "Suzuka"), default="Monza")
    parser.add_argument("--driver", type=int, default=4)
    args = parser.parse_args()
    try:
        print(json.dumps(probe(args.year, args.circuit, args.driver), indent=2))
    except (ValueError, KeyError, HTTPError, URLError, TimeoutError, OSError) as exc:
        parser.exit(1, f"Availability probe failed: {exc}\n")
