"""Prepare isolated opt-in views from retained identity-checked native snapshots."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from lapdna.analysis.engine import canonical_hash
from lapdna.analysis.store import PilotStore
from lapdna.analysis.views import prepare_views
from lapdna.ingestion.openf1 import atomic_json


def snapshots_by_digest():
    result = {}
    for pointer in (ROOT / "work/fastf1").glob("*/snapshot-pointer.json"):
        row = json.loads(pointer.read_bytes())
        path = Path(row["snapshot_path"])
        if path.is_file():
            result[row["source_digest"]] = path
    return result


def write_publication(directory, publication):
    directory.mkdir(parents=True, exist_ok=True)
    sid = publication["session"]["session_id"]
    name = "normalized/" + sid + "-" + publication["publication_sha256"] + ".json.gz"
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(publication, allow_nan=False, separators=(",", ":")).encode()
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("View publication exceeds serving size bound")
    compressed = gzip.compress(raw, mtime=0)
    if not path.exists():
        path.write_bytes(compressed)
    root_path = directory / "publication.json"
    root = json.loads(root_path.read_bytes()) if root_path.exists() else {"schema_version": "2.0.0", "sessions": {}}
    root["sessions"][sid] = {"path": name, "sha256": sha256(compressed).hexdigest()}
    atomic_json(root_path, root)
    return root["sessions"][sid]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", nargs="+")
    parser.add_argument("--reference-mode", choices=("legacy_v5", "speed_only"), default="speed_only")
    parser.add_argument("--output", type=Path, default=ROOT / "services/api/src/lapdna/view_data")
    args = parser.parse_args()
    ledger = json.loads((ROOT / "config/telemetry-coverage.json").read_bytes())
    store = PilotStore(ROOT / "services/api/src/lapdna/pilot_data")
    snapshots = snapshots_by_digest()
    entries = [row for row in ledger["sessions"] if not args.sessions or row["session_id"] in args.sessions]
    if not entries or args.sessions and len(entries) != len(set(args.sessions)):
        raise ValueError("Unknown session selection")
    for entry in entries:
        snapshot = json.loads(snapshots[entry["source_snapshot_sha256"]].read_bytes())
        if canonical_hash(snapshot) != entry["source_snapshot_sha256"]:
            raise ValueError("Source snapshot digest changed")
        legacy = store.load(entry["session_id"])
        publication = prepare_views(snapshot, legacy)
        if args.reference_mode == "speed_only":
            from lapdna.alignment.view_reference import select_speed_reference
            publication = select_speed_reference(publication, legacy)
        write_publication(args.output, publication)
        print(f"{entry['session_id']}: {len(publication['laps'])} native views, {len(publication['failures'])} unavailable", flush=True)


if __name__ == "__main__":
    main()
