"""Import the reviewed Monza 2024 qualifying pilot outside the request path."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.ingestion.openf1 import ImportFailure, import_session
from lapdna.ingestion.tracing import enrich_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("work/monza2024"))
    parser.add_argument("--refresh", action="store_true", help="Refetch source records; existing immutable revisions are retained")
    args = parser.parse_args()
    try:
        snapshot_path = import_session(args.cache_dir, refresh=args.refresh)
        enrich_snapshot(snapshot_path, args.cache_dir)
    except ImportFailure as exc:
        print(f"Import failed ({exc.code}): {exc}", file=sys.stderr)
        return 1
    except OSError:
        print("Import failed (filesystem_error): could not read or atomically write the local source cache; prior complete snapshots are retained", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
