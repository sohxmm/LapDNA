"""Prepare a compact verified session publication offline; no upstream requests."""

import argparse
from pathlib import Path

from lapdna.analysis.publication import write_publication


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    args = parser.parse_args()
    report, raw_bytes, compressed_bytes = write_publication(args.snapshot, args.output)
    print(f"Published {report['roster_count']} drivers; {report['telemetry_laps']} telemetry, {report['sector_only_laps']} sector-only, {report['unavailable_laps']} unavailable laps")
    if report['reference_lap_id']:
        print(f"Reference {report['reference_lap_id']}; integrated length {report['reference_length_m']:.1f} m")
    else:
        print("No verified spatial reference; recorded timing only")
    print(f"Normalized bytes {raw_bytes}; compressed {compressed_bytes}")
    print(f"Reports: {args.output / 'reports'}")


if __name__ == "__main__":
    main()
