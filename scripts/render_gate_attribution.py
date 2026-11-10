"""Render the committed Step 0 ledger, or inspect one derived lap record."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

from attribute_telemetry_gates import ROOT, render_report


def render(ledger):
    audit = ledger["gate_attribution"]
    total = audit["totals"]["timing_eligible"]
    first = total["first_failed_gate"]
    rows = ["", "## Findings for owner review", "",
        f"- All **{audit['per_lap_ledger']['records']:,} indexed laps** are recorded, including **{total['laps']:,} timing-eligible laps**. **{total['failed_telemetry_laps']:,}** eligible laps currently lack graphs.",
        f"- The native-gap gate is first for **{first.get('native_gap',0):,}** of those failures (**{100*first.get('native_gap',0)/total['failed_telemetry_laps']:.2f}%**).",
        f"- **{total['car_brackets_both_edges']:,}/{total['laps']:,}** eligible laps have car samples bracketing both edges under the v5 ±1 s crop (**{100*total['car_brackets_both_edges']/total['laps']:.2f}%**). **{total['entirely_missing_native_car_in_lap']}** eligible laps have no in-lap car observations.",
        "- Bracketing is a conservative input-feasibility check using the existing crop, not a new Tier 0 acceptance decision or a forecast of final coverage. Missing edge padding is not automatically complete source absence.",
        "- Downstream failures overlap with gaps: the all-failure tables retain those conditional diagnostics. Where a frozen reference or valid progress is absent, residual/scale/pair checks remain not evaluated.",
        "- Missing optional channels do not currently reject an entire lap. Peer-specific pair failures do not make a lap globally unusable.", "",
        "### Session-reference failures", "", "| Year | Sessions without a frozen v5 reference | No prepared reference candidate reached geometry checks |", "| --- | ---: | ---: |"]
    reasons = Counter()
    for year in audit["by_year"]:
        sessions = [r for r in ledger["sessions"] if str(r["year"]) == year and "gate_attribution" in r]
        missing = [r for r in sessions if not r["gate_attribution"]["reference"]["available"]]
        no_candidate = sum(not r["gate_attribution"]["reference"]["attempt_rejections"] for r in missing)
        rows.append(f"| {year} | {len(missing)} | {no_candidate} |")
        for row in missing:
            reasons.update(row["gate_attribution"]["reference"]["attempt_rejections"])
    rows += ["", "Reference-candidate rejection messages (counts are candidate attempts, not laps or sessions):", ""]
    rows.extend(f"- {reason}: {count}." for reason, count in reasons.most_common())
    rows += ["", "### All diagnostic pair-gap failures", "", "These are conditional residual probes after an earlier prerequisite failed, including currently disallowed same-driver pairs. They are **not** accepted comparison results or extra graph coverage. Counts overlap across checks.", "",
        "| Year | Cohort | Diagnostic sector 1 | Diagnostic sector 2 | Diagnostic lap gap |", "| --- | --- | ---: | ---: | ---: |"]
    for year, values in audit["by_year"].items():
        for cohort, stats in values["pair_gates"].items():
            gates = stats["diagnostic_pair_gap_failures"]
            rows.append(f"| {year} | {cohort} | {gates.get('pair_sector_1',0)} | {gates.get('pair_sector_2',0)} | {gates.get('pair_lap_gap',0)} |")
    rows += ["", "### First pair-level blockers", "", "Missing alignment is the actual early pair blocker when one or both laps have no published timing curve. Later residual differences are reported separately above, not silently substituted for this first gate.", "",
        "| Year | Cohort | First gate | Pairs |", "| --- | --- | --- | ---: |"]
    for year, values in audit["by_year"].items():
        for cohort, stats in values["pair_gates"].items():
            for gate, count in stats["actual_first_failed_gate"].items():
                rows.append(f"| {year} | {cohort} | {gate} | {count} |")
    rows += ["", "### Re-render or inspect a lap", "", "```powershell",
        ".venv\\Scripts\\python scripts/render_gate_attribution.py",
        ".venv\\Scripts\\python scripts/render_gate_attribution.py --lap-id fastf1_2026_19_Q_44_19", "```", "",
        "This renderer reads the committed derived ledger only. It neither reacquires data nor changes gates. The measurement command above followed by this renderer reproduces the complete report. Per-lap entries retain first/all lap gates, unknown downstream checks, raw eligibility reasons, channel availability, native gap measurements and actual/diagnostic peer context.", "",
        "**Step 0 is the stop point.** Tier 0/Tier 1, contracts, same-driver selection, RPM and UI changes are not implemented by this audit. Tier 2 gate bodies and all measured v5 runtime files remain unchanged.", ""]
    return render_report(audit) + "\n" + "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=ROOT / "config/telemetry-coverage.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/23-gate-attribution.md")
    parser.add_argument("--lap-id")
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_bytes())
    artifact = ledger["gate_attribution"]["per_lap_ledger"]
    path = ROOT / artifact["path"]
    assert sha256(path.read_bytes()).hexdigest() == artifact["sha256"], "Derived lap ledger changed"
    if args.lap_id:
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                if record["lap_id"] == args.lap_id:
                    print(json.dumps(record, indent=2, ensure_ascii=True))
                    return
        raise ValueError("Lap ID is absent from the audited index")
    args.report.write_text(render(ledger), encoding="utf-8", newline="\n")
    print(f"Rendered Step 0 report: {args.report.name}")


if __name__ == "__main__":
    main()
