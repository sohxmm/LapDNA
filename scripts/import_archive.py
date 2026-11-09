"""Resume the qualifying archive without resetting shared provider limits."""

import argparse
from datetime import date
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.analysis.publication import write_publication
from lapdna.ingestion.budget import RequestBudget
from lapdna.ingestion.fastf1_native import import_fastf1_session
from lapdna.ingestion.openf1 import ImportFailure, atomic_json, utc_now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=[2024, 2018, 2019, 2020, 2021, 2022, 2023, 2025, 2026])
    parser.add_argument("--output", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    parser.add_argument("--report", type=Path, default=Path("work/fastf1/archive-report.json"))
    args = parser.parse_args()
    if any(not 2018 <= year <= 2026 for year in args.years):
        parser.error("Only the reviewed 2018–2026 archive is supported")
    base = Path("work/fastf1")
    history = json.loads(args.report.read_text(encoding="utf-8")) if args.report.exists() else {"scope":"Actual primary-native archive attempts; future/unresolved sessions are not claimed as coverage", "results":{}}
    budget = RequestBudget(base / "request-budget")
    for year in args.years:
        calendar = json.loads(Path(f"services/api/src/lapdna/calendar_snapshots/{year}.json").read_text(encoding="utf-8"))
        results = json.loads(Path(f"services/api/src/lapdna/classification_snapshots/{year}.json").read_text(encoding="utf-8"))
        sprints = {event["round"] for event in results["events"] if any(s["session_type"] == "sprint_qualifying" for s in event["sessions"])}
        for race in calendar["races"]:
            if not race.get("qualifying_date") or race["qualifying_date"] > date.today().isoformat():
                continue
            for kind in (["Q", "SQ"] if year >= 2023 and race["round"] in sprints else ["Q"]):
                key = f"{year}-{race['round']}-{kind}"
                previous = history["results"].get(key)
                if previous and previous["status"] == "published":
                    root = json.loads((args.output / "publication.json").read_text(encoding="utf-8"))
                    entry = root["sessions"].get(previous["session_id"])
                    if entry:
                        manifest = json.loads((args.output / entry["manifest"]).read_text(encoding="utf-8"))
                        if manifest["source_snapshot_sha256"] == previous["source_snapshot_sha256"] and manifest["schema_version"] == "1.4.0":
                            continue
                while True:
                    row = {"year":year, "round":race["round"], "session_type":kind, "event_name":race["name"], "checked_at":utc_now()}
                    print(f"Importing {key} {race['name']}", flush=True)
                    try:
                        snapshot = import_fastf1_session(base / key, year, race["round"], session_type=kind)
                        report, _, compressed = write_publication(snapshot, args.output)
                        identity = json.loads(snapshot.read_text(encoding="utf-8"))["import_spec"]
                        row.update(status="published", session_id=f"{year}-{race['round']}-{identity['circuit_id']}-{kind}",
                                   source_snapshot_sha256=report["source_snapshot_sha256"], telemetry_laps=report["telemetry_laps"],
                                   sector_only_laps=report["sector_only_laps"], unavailable_laps=report["unavailable_laps"], compressed_bytes=compressed)
                        print(f"Published {key}: {row['telemetry_laps']} telemetry / {row['sector_only_laps']} timing-only", flush=True)
                    except ImportFailure as exc:
                        row.update(status="unavailable", code=exc.code, reason=str(exc))
                    except (ValueError, OSError) as exc:
                        row.update(status="unavailable", code="publication_failed", reason=str(exc)[:600])
                    history["results"][key] = row
                    history["updated_at"] = utc_now()
                    atomic_json(args.report, history)
                    if row.get("code") == "access_required":
                        print("Local sign-in needs renewal. Completed work is retained.", flush=True)
                        return 2
                    if row.get("code") != "rate_limited":
                        if row["status"] != "published":
                            print(f"Unavailable {key}: {row.get('code')}: {row.get('reason')}", flush=True)
                        break
                    # A stricter project window and the original library limiter
                    # both stay enabled in this one process. Never rotate clients
                    # or accounts to bypass the source's allowance.
                    _, wait = budget.status()
                    pause = max(60., wait + 2.)
                    print(f"Waiting {pause:.0f} seconds for the source window; cached work retained", flush=True)
                    deadline = time.monotonic() + pause
                    while time.monotonic() < deadline:
                        time.sleep(min(30., deadline - time.monotonic()))
    failures = [row for row in history["results"].values() if row["status"] != "published"]
    print(f"Archive pass complete: {len(history['results']) - len(failures)} published; {len(failures)} unresolved", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
