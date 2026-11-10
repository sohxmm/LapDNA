"""Acquire, audit and release the remaining archive with resumable checkpoints.

Run from the Desktop repository. No source limits are bypassed. Any local
code change or sign-in failure stops publication for explicit follow-up.
"""

from datetime import datetime, timezone, date
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "work/archive-release-state.json"


def state(status, **details):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps({"status":status,"updated_at":datetime.now(timezone.utc).isoformat(),**details},indent=2),encoding="utf-8")
    temporary.replace(STATE)
    print(status, flush=True)


def run(command, *, cwd=ROOT):
    return subprocess.run(command,cwd=cwd,check=True)


def head():
    return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()


def require_unchanged(commit):
    if head() != commit or subprocess.check_output(["git","status","--porcelain"],cwd=ROOT,text=True).strip():
        raise ValueError("Source changed during acquisition; audit/release requires a reviewed clean checkpoint")


def expected_candidates(root, today=None):
    cutoff = today or date.today().isoformat()
    result = {}
    for year in range(2018,2027):
        calendar=json.loads((root / f"services/api/src/lapdna/calendar_snapshots/{year}.json").read_text(encoding="utf-8"))
        classifications=json.loads((root / f"services/api/src/lapdna/classification_snapshots/{year}.json").read_text(encoding="utf-8"))
        sprints={event["round"] for event in classifications["events"] if any(s["session_type"]=="sprint_qualifying" for s in event["sessions"])}
        for race in calendar["races"]:
            if not race.get("qualifying_date") or race["qualifying_date"]>cutoff:
                continue
            for kind in (["Q","SQ"] if year>=2023 and race["round"] in sprints else ["Q"]):
                result[(year,race["round"],kind)]={"year":year,"round":race["round"],"session_type":kind,"event_name":race["name"]}
    return result


def remaining_candidates(expected, coverage, attempts):
    # The audited active publication is authoritative. A successful targeted
    # retry can supersede an old failed batch entry without rewriting history.
    published={(row["year"],row["round"],row["session_id"].rsplit('-',1)[1]) for row in coverage["sessions"]}
    remaining=[]
    for key,identity in expected.items():
        if key in published:
            continue
        attempted=attempts["results"].get(f"{key[0]}-{key[1]}-{key[2]}")
        remaining.append({**identity,"code":attempted.get("code","not_published") if attempted else "not_attempted",
            "reason":attempted.get("reason","No audited native publication is active for this session") if attempted else "Detailed native import has not completed for this past-session candidate"})
    return remaining


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-current",action="store_true",help="Audit and publish the ready catalogue without waiting for unfinished imports")
    args=parser.parse_args()
    python = sys.executable
    baseline = head()
    require_unchanged(baseline)
    state("importing", code_commit=baseline)
    # A second bounded pass retries actual source/publication failures while
    # skipping completed primary sessions. Rate-limited work waits in-place.
    for attempt in range(0 if args.publish_current else 2):
        imported = subprocess.run([python,"-u","scripts/import_archive.py"],cwd=ROOT)
        if imported.returncode == 2:
            state("needs_local_sign_in", code_commit=baseline, instruction="Renew FastF1 sign-in locally, then run this command again. Do not share credentials.")
            return 2
        if imported.returncode not in (0,1):
            raise ValueError("Archive acquisition stopped unexpectedly; retained progress requires inspection")
        if imported.returncode == 0:
            break
    require_unchanged(baseline)
    state("checking", code_commit=baseline)
    run([python,"-m","pytest","services/api/tests","-q"])
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    for check in ("contracts:check","typecheck","test:web","build"):
        run([npm,"run",check])
    run([python,"scripts/prepare_release.py"])
    candidates = sorted((ROOT / "work/releases").glob(baseline[:8]+"-*"))
    release = candidates[-1]
    receipt = json.loads((release / "release-receipt.json").read_text(encoding="utf-8"))
    state("auditing", code_commit=baseline, release_path=str(release), sessions=receipt["sessions"])
    ledger = release / "audited-coverage.json"
    run([python,"-u","scripts/audit_publications.py","--publication",str(release / "services/api/src/lapdna/pilot_data"),
         "--output",str(ledger),"--reports",str(release / "audit")])
    require_unchanged(baseline)
    coverage = json.loads(ledger.read_text(encoding="utf-8"))
    attempts = json.loads((ROOT / "work/fastf1/archive-report.json").read_text(encoding="utf-8"))
    unresolved = remaining_candidates(expected_candidates(ROOT),coverage,attempts)
    # Only an audited frozen ledger is committed. No raw cache or credentials.
    shutil.copy2(ledger, ROOT / "config/telemetry-coverage.json")
    notes = ["# Audited native archive coverage", "", "This is the latest audited batch; deployment is complete only when the receipt below is confirmed.", "",
             f"Source commit: `{baseline}`. Frozen catalogue: `{receipt['catalogue_sha256']}`.",
             f"Audited sessions: **{coverage['session_count']}**. Remaining source/publication failures: **{len(unresolved)}**.", "",
             "A session with telemetry-capable laps still applies pairwise checks. Timing-only and excluded laps remain explicit. Future calendar sessions are not downloaded before they exist.", "",
             "| Year | Native Q | Native SQ |", "| --- | ---: | ---: |"]
    for year in range(2018,2027):
        rows = [row for row in coverage["sessions"] if row["year"] == year]
        notes.append(f"| {year} | {sum(row['session_id'].endswith('-Q') for row in rows)} | {sum(row['session_id'].endswith('-SQ') for row in rows)} |")
    notes.extend(["", "| Session | Telemetry-capable laps | Timing-only laps |", "| --- | ---: | ---: |"])
    for row in coverage["sessions"]:
        notes.append(f"| {row['session_id']} · {row['event_name']} | {row['capabilities'].get('telemetry',0)} | {row['capabilities'].get('sector_only',0)} |")
    notes.extend(["", "## Unresolved source/publication failures", ""])
    notes.extend([f"- {row['year']} R{row['round']} {row['session_type']} · {row['event_name']}: {row.get('reason','No verified native publication')}" for row in unresolved] or ["None among the actual attempted past-session candidates."])
    notes.extend(["", "The detailed ledger records exact source hashes, methods and phase-best pair checks. Source agreement is not physical corner ground truth. Brake is on/off, not pressure; no missing control input is inferred from speed.", ""])
    document = ROOT / "docs/21-archive-coverage.md"
    document.write_text("\n".join(notes),encoding="utf-8")
    run(["git","add","config/telemetry-coverage.json","docs/21-archive-coverage.md"])
    if subprocess.run(["git","diff","--cached","--quiet"],cwd=ROOT).returncode:
        run(["git","commit","-m","Update audited native qualifying archive coverage"])
        run(["git","push","origin","main"])
    release_head = head()
    state("uploading_verified_artifacts", code_commit=baseline, release_path=str(release), sessions=coverage["session_count"], unresolved=len(unresolved))
    run([python,"-u","scripts/publish_release_blobs.py","--release",str(release)])
    require_unchanged(release_head)
    state("deploying", code_commit=baseline, release_path=str(release), sessions=coverage["session_count"])
    npx = shutil.which("npx.cmd" if sys.platform == "win32" else "npx")
    run([npx,"--yes","vercel@65.12.1","deploy","--prod","--yes","--scope","sohxm44s-projects"],cwd=release)
    run([python,"-u","scripts/verify_deployment.py","--expected-publication",str(release / "services/api/src/lapdna/pilot_data/publication.json"),
         "--output",str(release / "hosted-checks.json")])
    document.write_text(document.read_text(encoding="utf-8")+"\n## Confirmed deployment\n\nThe frozen batch above was deployed to https://lapdna.vercel.app and passed hosted session-inventory, comparison, reversal, exact-link and roster checks. The private operator release directory retains the deployment output and hosted-check receipt. Earlier 63-session figures in historical release notes describe the earlier batch.\n",encoding="utf-8")
    run(["git","add","docs/21-archive-coverage.md"])
    run(["git","commit","-m","Record verified archive deployment"])
    run(["git","push","origin","main"])
    state("complete" if not unresolved else "released_with_source_failures", code_commit=baseline, release_path=str(release),
          sessions=coverage["session_count"], unresolved=unresolved, url="https://lapdna.vercel.app")
    return 0 if not unresolved else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Commands above use only operator paths/identifiers, never secrets.
        state("needs_review", reason=str(exc)[:600])
        raise
