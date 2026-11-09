"""Import explicit historical session identities, resumably, outside web requests."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.ingestion.openf1 import ImportFailure, import_session, atomic_json, utc_now
from lapdna.ingestion.tracing import enrich_snapshot, archive_json
from lapdna.ingestion.specs import load_specs
from lapdna.analysis.publication import write_publication


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, help="Single-session cache, or parent directory when --all is used")
    parser.add_argument("--specs", type=Path, default=Path("config/telemetry-sessions.json"))
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--round", type=int, dest="round_number", default=16)
    parser.add_argument("--all", action="store_true", help="Process every configured session in the selected year; failures remain unavailable")
    parser.add_argument("--publish", action="store_true", help="Normalize and activate only sessions passing publication checks")
    parser.add_argument("--bulk", action="store_true", help="Fetch bounded whole-session native streams instead of per-driver requests")
    parser.add_argument("--output", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    parser.add_argument("--refresh", action="store_true", help="Refetch source records; existing immutable revisions are retained")
    args = parser.parse_args()
    specs = [spec for spec in load_specs(args.specs) if spec["year"] == args.year and (args.all or spec["round"] == args.round_number)]
    if not specs:
        parser.error("No pinned native-source specification exists for this selection; recorded classification timing remains available")
    results = []
    base = args.cache_dir or Path("work" if args.all else f"work/{specs[0]['circuit_id']}{args.year}")
    for spec in specs:
        cache = base / f"{spec['circuit_id']}{spec['year']}" if args.all else base
        result = {"year": spec["year"], "round": spec["round"], "event_name": spec["event_name"], "checked_at": utc_now()}
        try:
            print(f"Importing {spec['year']} {spec['event_name']}", flush=True)
            # Verify pinned timing archive identity before downloading large streams.
            info, _ = archive_json(cache / "source", "session_info.json", spec=spec)
            identity = info.get("session_info", {})
            if (identity.get("Key"), identity.get("Meeting", {}).get("Key"), identity.get("Path")) != (spec["session_key"], spec["meeting_key"], spec["archive_session_path"]):
                raise ImportFailure("archive_session_mismatch", "Pinned source identity disagrees with import specification")
            path = None
            pointer = cache / "snapshot-pointer.json"
            if pointer.exists() and not args.refresh:
                previous = Path(json.loads(pointer.read_text(encoding="utf-8"))["snapshot_path"])
                if previous.is_file():
                    snapshot = json.loads(previous.read_text(encoding="utf-8"))
                    legacy_monza = (not snapshot.get("import_spec") and spec["session_key"] == 9586 and spec["year"] == 2024 and spec["round"] == 16)
                    if snapshot.get("source") == "openf1_tracinginsights" and (snapshot.get("import_spec") == spec or legacy_monza):
                        path = previous
                        print("Reusing the complete identity-checked source snapshot", flush=True)
            if path is None:
                path = enrich_snapshot(import_session(cache, refresh=args.refresh, spec=spec, bulk=args.bulk), cache)
            result.update(status="imported", snapshot_path=str(path.resolve()))
            if args.publish:
                report, raw_size, compressed = write_publication(path, args.output)
                result.update(status="published", telemetry_laps=report["telemetry_laps"], sector_only_laps=report["sector_only_laps"], unavailable_laps=report["unavailable_laps"], compressed_bytes=compressed)
                print(f"Published {report['roster_count']} drivers / {report['telemetry_laps']} telemetry / {report['sector_only_laps']} sector-only laps", flush=True)
        except ImportFailure as exc:
            result.update(status="unavailable", code=exc.code, reason=str(exc))
            print(f"Unavailable ({exc.code}): {exc}", file=sys.stderr, flush=True)
        except (OSError, ValueError) as exc:
            result.update(status="unavailable", code="publication_or_filesystem_failed", reason=str(exc)[:600])
            print(f"Unavailable: {exc}", file=sys.stderr, flush=True)
        results.append(result)
        atomic_json(base / "import-report.json", {"scope": "Actual attempted imports only; catalogue entries alone do not establish availability", "results": results})
    return 1 if any(result["status"] == "unavailable" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
