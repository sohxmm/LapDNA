"""Step 4: retain Step 3b receipt, select speed-only references, remeasure views."""
import gzip
from hashlib import sha256
import json
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from lapdna.alignment.view_reference import select_speed_reference
from lapdna.analysis.view_store import ViewStore
from lapdna.analysis.store import PilotStore
from lapdna.ingestion.openf1 import atomic_json
from attribute_view_gates import session_measurement, summarize, render_report
from attribute_telemetry_gates import protected_functions
from prepare_view_publications import write_publication


def main():
    before = json.loads((ROOT / "config/view-coverage-legacy-reference.json").read_bytes())
    baseline = json.loads((ROOT / "config/telemetry-coverage.json").read_bytes())
    assert len(before["sessions"]) == len(baseline["sessions"]) == 217
    assert before["tier2_function_sha256"] == protected_functions()
    directory = ROOT / "services/api/src/lapdna/view_data"
    legacy_store = PilotStore(ROOT / "services/api/src/lapdna/pilot_data")
    entries = {r["session_id"]: r for r in baseline["sessions"]}
    sessions, recovery = [], []
    # Read frozen Step 3b blob paths, not a partially replaced root on resumption.
    receipt = ROOT / "work/view-attribution/legacy-catalogue.json"
    if not receipt.exists():
        receipt.write_bytes((directory / "publication.json").read_bytes())
    frozen_catalogue = json.loads(receipt.read_bytes())
    legacy_root = ROOT / "work/view-attribution/legacy-views"
    legacy_root.mkdir(parents=True, exist_ok=True)
    # Store path references remain confined to one root: copy only compressed
    # derived views to ignored checkpoint storage, never raw samples into Git.
    if not (legacy_root / "publication.json").exists():
        for item in frozen_catalogue["sessions"].values():
            target = legacy_root / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((directory / item["path"]).read_bytes())
        atomic_json(legacy_root / "publication.json", frozen_catalogue)
    old_store = ViewStore(legacy_root)
    for old in before["sessions"]:
        sid = old["session_id"]
        original = old_store.load(sid)
        assert original["publication_sha256"] == old["view_publication_sha256"]
        publication = select_speed_reference(original, legacy_store.load(sid))
        write_publication(directory, publication)
        session = session_measurement(publication, entries[sid])
        sessions.append(session)
        if old["reference"] is None:
            summary = summarize([session])
            recovery.append({"session_id": sid, "year": old["year"],
                "recovered_reference": publication["reference"] is not None,
                "eligible_laps": summary["eligible_laps"], "tier0": summary["tier0"], "tier1": summary["tier1"],
                "old_attempt_rejections": entries[sid]["gate_attribution"]["reference"]["attempt_rejections"]})
        print(f"{sid}: speed-only Tier 1 {sum(r['tier1'] for r in session['laps'])}/{len(session['laps'])}", flush=True)
    lap_path = ROOT / "config/view-laps-speed-reference.jsonl.gz"
    with lap_path.open("wb") as file:
        with gzip.GzipFile(fileobj=file, mode="wb", mtime=0, filename="") as stream:
            for session in sessions:
                for lap in session["laps"]:
                    stream.write((json.dumps({"session_id": session["session_id"], **lap}, allow_nan=False, separators=(",", ":")) + "\n").encode())
    report = {**before, "reference_mode": "speed_only", "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "step4_file_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "services/api/src/lapdna/alignment/view_reference.py", "services/api/src/lapdna/analysis/views.py",
            "scripts/prepare_view_publications.py", "scripts/recover_view_references.py")},
        "step3b_ledger_sha256": sha256((ROOT / "config/view-coverage-legacy-reference.json").read_bytes()).hexdigest(),
        "reference_implementation_sha256": sha256((ROOT / "services/api/src/lapdna/alignment/view_reference.py").read_bytes()).hexdigest(),
        "by_year": {str(year): summarize([s for s in sessions if s["year"] == year]) for year in sorted({s["year"] for s in sessions})},
        "totals": summarize(sessions), "reference_recovery": recovery,
        "per_lap_ledger": {"path": lap_path.relative_to(ROOT).as_posix(), "sha256": sha256(lap_path.read_bytes()).hexdigest()},
        "sessions": [{**{k: v for k, v in s.items() if k != "laps"}, "summary": summarize([s])} for s in sessions]}
    recent = summarize([s for s in sessions if 2022 <= s["year"] <= 2025])["bound_distribution"]
    report["quality_proposal"] = {"status": "proposal_only_not_enabled",
        "recent_2022_2025_distribution": recent,
        "A": "No speed bridges, interior residuals <=50 ms, distance scale deviation <=3%; native support still does not prove cause.",
        "B_bound_ceiling_m": ceil(recent["p90_m"] / 5) * 5,
        "B": "Bridged laps within the rounded-up 2022-2025 P90 bound ceiling, interior residuals <=150 ms and scale deviation <=3%.",
        "C": "Any larger model bound, interior residual >150 ms, or scale deviation >3%; annotate, do not block Tier 1.",
        "qualification": "Distance-bound thresholds are descriptive of this archive, not calibrated accuracy or probabilities. Equal endpoint speeds can hide dynamics; bridge flags always remain. Current runtime only applies the already authorized interior-residual C annotation; others stay ungraded."}
    atomic_json(ROOT / "config/view-coverage-speed-reference.json", report)
    lines = [render_report(report), "## Step 3b versus Step 4", "",
        "| Year | Tier 1 existing reference | Tier 1 speed-only reference | Newly available laps | Reference-less sessions recovered |", "| --- | ---: | ---: | ---: | ---: |"]
    for year, row in report["by_year"].items():
        old = before["by_year"][year]
        recovered = sum(r["recovered_reference"] for r in recovery if str(r["year"]) == year)
        lines.append(f"| {year} | {old['tier1']} | {row['tier1']} | {row['tier1'] - old['tier1']} | {recovered} |")
    lines += ["", "## Previously reference-less sessions", "", "| Session | Recovered | Eligible | Tier 1 | Original reference rejections |", "| --- | --- | ---: | ---: | --- |"]
    for row in recovery:
        lines.append(f"| {row['session_id']} | {row['recovered_reference']} | {row['eligible_laps']} | {row['tier1']} | {json.dumps(row['old_attempt_rejections'], sort_keys=True)} |")
    q = report["quality_proposal"]
    lines += ["", "## Proposed quality thresholds (not activated)", "", q["A"], "",
        f"B: cumulative model bound <= **{q['B_bound_ceiling_m']} m**, rounded up in 5 m steps from the pooled 2022-2025 P90 ({recent['p90_m']:.3f} m), with interior residuals <=150 ms and scale deviation <=3%.", "",
        "C: above that model bound, an interior residual above 150 ms, or scale deviation above 3%. These are visible quality annotations, never new Tier 1 rejection gates.", "",
        q["qualification"], "", "## Checkpoint boundary", "",
        "Steps 1-4 backend/contracts and coverage receipts are complete. Stop here. Same-driver/flagged-lap selection and ECharts rendering remain Steps 5-6. No position estimator or live deployment is included.", ""]
    (ROOT / "docs/25-v6-reference-recovery.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    assert before["tier2_function_sha256"] == protected_functions()
    for name, expected in before["runtime_sha256"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected
    print("Wrote combined Step 3b/4 checkpoint", flush=True)


if __name__ == "__main__":
    main()
