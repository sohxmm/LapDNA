"""Refresh a provenance-stamped calendar metadata fallback, never telemetry."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))

from lapdna.calendar import client_year, fetch_calendar, normalize, utc_now


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int)
    args = parser.parse_args()
    if not 1950 <= args.year <= client_year(utc_now()):
        parser.error("year is outside the supported calendar range")
    result = normalize(fetch_calendar(args.year), args.year, utc_now())
    destination = ROOT / "services/api/src/lapdna/calendar_snapshots" / f"{args.year}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(destination)
    print(f"Saved {result.year}: {len(result.races)} source calendar events, retrieved {result.retrieved_at.isoformat()}")
