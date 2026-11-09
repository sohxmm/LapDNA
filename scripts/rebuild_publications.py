"""Rebuild retained source snapshots with the current reviewed publication method."""

import argparse
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.analysis.publication import write_publication
from lapdna.ingestion.openf1 import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=Path("work"))
    parser.add_argument("--output", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    parser.add_argument("--years", type=int, nargs="+")
    args = parser.parse_args()
    # Primary snapshots are attempted last. A failed candidate never removes
    # the last usable publication from another explicitly declared source.
    pointers = sorted(args.work.glob("*/snapshot-pointer.json")) + sorted((args.work / "fastf1").glob("*/snapshot-pointer.json"))
    results = []
    for pointer in pointers:
        record = json.loads(pointer.read_text(encoding="utf-8"))
        declared = Path(record["snapshot_path"])
        local = pointer.parent / "snapshots" / declared.parent.name / "snapshot.json"
        path = local if local.is_file() else declared
        if not path.resolve().is_relative_to(args.work.resolve()):
            raise ValueError("Source snapshot must remain inside the project's private work directory")
        # Small session metadata is read from the source snapshot itself;
        # there are no upstream requests or inferred session identities.
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        identity = snapshot.get("import_spec") or snapshot["session"]
        if args.years and identity["year"] not in args.years:
            continue
        item = {"snapshot": str(path), "year": identity["year"], "round": identity["round"], "source": snapshot["source"]}
        del snapshot
        try:
            report, _, compressed = write_publication(path, args.output)
            item.update(status="published", telemetry_laps=report["telemetry_laps"], sector_only_laps=report["sector_only_laps"], compressed_bytes=compressed)
            print(f"{identity['year']} R{identity['round']} {item['source']}: {report['telemetry_laps']} telemetry / {report['sector_only_laps']} sectors", flush=True)
        except (ValueError, OSError) as exc:
            item.update(status="unavailable", reason=str(exc)[:600])
            print(f"Unavailable {identity['year']} R{identity['round']}: {item['reason']}", flush=True)
        results.append(item)
        atomic_json(args.work / "rebuild-report.json", {"scope": "Retained complete snapshots only; no network acquisition", "results": results})


if __name__ == "__main__":
    main()
