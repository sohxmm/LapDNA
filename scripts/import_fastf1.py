"""Import 2018–2026 qualifying through locally authenticated, pinned FastF1."""

import argparse
from pathlib import Path
import sys
import json
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.ingestion.fastf1_native import import_fastf1_session
from lapdna.ingestion.openf1 import ImportFailure, atomic_json, utc_now
from lapdna.analysis.publication import write_publication


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--session", choices=("Q", "SQ"), default="Q")
    parser.add_argument("--round", type=int, dest="round_number")
    parser.add_argument("--all", action="store_true", help="Import completed calendar qualifying candidates in this year; source failures remain unavailable")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    args = parser.parse_args(argv)
    if not 2018 <= args.year <= 2026 or args.session == "SQ" and args.year < 2023 or (args.round_number is None and not args.all) or (args.round_number is not None and args.all):
        parser.error("Choose 2018–2026 and either --round or --all")
    calendar = json.loads(Path(f"services/api/src/lapdna/calendar_snapshots/{args.year}.json").read_text(encoding="utf-8"))
    rounds = [race["round"] for race in calendar["races"] if args.all and race.get("qualifying_date") and race["qualifying_date"] <= date.today().isoformat()]
    if args.all and args.session == "SQ":
        classifications = json.loads(Path(f"services/api/src/lapdna/classification_snapshots/{args.year}.json").read_text(encoding="utf-8"))
        sprint_rounds = {event["round"] for event in classifications["events"] if any(session["session_type"] == "sprint_qualifying" for session in event["sessions"])}
        rounds = [round_number for round_number in rounds if round_number in sprint_rounds]
    if not args.all:
        rounds = [args.round_number]
    base = args.cache_dir or Path("work/fastf1")
    results = []
    for round_number in rounds:
        cache = base / f"{args.year}-{round_number}-{args.session}" if args.all or args.cache_dir is None else base
        result = {"year": args.year, "round": round_number, "session_type": args.session, "checked_at": utc_now()}
        try:
            print(f"Importing FastF1 {args.year} round {round_number}", flush=True)
            path = import_fastf1_session(cache, args.year, round_number, refresh=args.refresh, session_type=args.session)
            result.update(status="imported", snapshot_path=str(path.resolve()))
            if args.publish:
                report, _, compressed = write_publication(path, args.output)
                result.update(status="published", telemetry_laps=report["telemetry_laps"], sector_only_laps=report["sector_only_laps"], unavailable_laps=report["unavailable_laps"], compressed_bytes=compressed)
                print(f"Published {report['roster_count']} drivers, {report['telemetry_laps']} telemetry and {report['sector_only_laps']} sector-only laps; {compressed} compressed bytes", flush=True)
        except ImportFailure as exc:
            result.update(status="unavailable", code=exc.code, reason=str(exc))
            print(f"Import unavailable ({exc.code}): {exc}", file=sys.stderr, flush=True)
        except ValueError as exc:
            result.update(status="unavailable", code="publication_failed", reason=str(exc)[:600])
            print(result["reason"], file=sys.stderr, flush=True)
        except OSError:
            result.update(status="unavailable", code="filesystem_failed", reason="Local source/publication storage failed; previous publication retained")
            print(result["reason"], file=sys.stderr, flush=True)
        results.append(result)
        atomic_json(base / f"import-report-{args.year}{'-SQ' if args.session=='SQ' else ''}.json", {"scope": "Actual attempted primary-native imports; no calendar-only coverage claims", "results": results})
        if result.get("code") in ("rate_limited", "access_required"):
            break
    return 1 if any(result["status"] == "unavailable" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
