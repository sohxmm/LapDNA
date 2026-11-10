"""V6 coverage audit on the unchanged v5 eligible cohort; never activates v5 data."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from lapdna.alignment.view_delta import prepare_progress, annotate_sectors
from lapdna.analysis.engine import canonical_hash
from lapdna.analysis.store import PilotStore
from lapdna.analysis.views import prepare_views
from lapdna.ingestion.openf1 import atomic_json
from lapdna.view_models import NativeLapView
from prepare_view_publications import snapshots_by_digest, write_publication
from attribute_telemetry_gates import protected_functions


def bounds_distribution(values):
    ordered = sorted(values)
    return {"count": len(ordered), **{key: ordered[ceil(len(ordered) * q) - 1] if ordered else None
        for key, q in (("p50_m", .5), ("p90_m", .9), ("p99_m", .99), ("maximum_m", 1.))}}


def summarize(sessions):
    rows = [lap for session in sessions for lap in session["laps"]]
    return {"sessions": len(sessions), "eligible_laps": len(rows),
        "v5_telemetry": sum(s["v5_telemetry"] for s in sessions),
        "tier0": sum(r["tier0"] for r in rows), "tier1": sum(r["tier1"] for r in rows),
        "speed_candidates": sum(r["speed_candidate"] for r in rows),
        "first_failure": dict(Counter(r["first_failure"] for r in rows if not r["tier1"])),
        "bound_distribution": bounds_distribution([r["cumulative_bound_m"] for r in rows if r["speed_candidate"]]),
        "tier1_bound_distribution": bounds_distribution([r["cumulative_bound_m"] for r in rows if r["tier1"]]),
        "grade_c_interior_laps": sum(r.get("grade_c_interior", False) for r in rows),
        "distance_scale_over_3pct": sum(r.get("scale_over_3pct", False) for r in rows)}


def session_measurement(publication, entry):
    rows = []
    for identifier in sorted(set(publication["laps"]) | set(publication["failures"])):
        tier0 = identifier in publication["laps"]
        candidate = identifier in publication["alignment_candidates"]
        tier1 = candidate and publication["reference"] is not None
        failure = publication["failures"].get(identifier) or publication["alignment_failures"].get(identifier)
        first = failure["gate"] if failure else "session_reference" if not tier1 else None
        record = {"lap_id": identifier, "tier0": tier0, "tier1": tier1, "speed_candidate": candidate,
                  "first_failure": first, "cumulative_bound_m": None, "bridges": None}
        if candidate:
            record.update(publication["alignment_candidates"][identifier])
        if tier1:
            view = NativeLapView.model_validate_json(json.dumps(publication["laps"][identifier]))
            progress = prepare_progress(view, publication["reference"]["length_m"])
            annotate_sectors(progress, view.metadata, publication["sector_boundaries_m"], identifier == publication["reference"]["lap_id"])
            record["grade_c_interior"] = any(s.grade == "C" for s in progress.sector_annotations)
            record["interior_residual_ms"] = [s.residual_ms for s in progress.sector_annotations]
            record["scale_over_3pct"] = abs(progress.scale_factor - 1) > .0300001
            record["endpoint_residual_ms"] = progress.endpoint_residual_ms
        rows.append(record)
    assert len(rows) == entry["gate_attribution"]["summary"]["timing_eligible"]["laps"]
    return {"session_id": entry["session_id"], "year": entry["year"],
        "v5_telemetry": entry["capabilities"].get("telemetry", 0),
        "reference": publication["reference"], "source_snapshot_sha256": entry["source_snapshot_sha256"],
        "legacy_publication_sha256": entry["publication_sha256"],
        "view_publication_sha256": publication["publication_sha256"], "laps": rows}


def render_report(report):
    lines = ["# V6 telemetry-view coverage checkpoint", "",
        "Measured on the unchanged v5 timing-eligible cohort; native snapshots and v5 publications are retained and hash-checked. No frontend rollout.", "",
        "Tier 0 requires car timestamps at both timing edges only. Tier 1 requires native speed bracketing, increasing integrated progress, no speed gap above 2 s and a reference. No geometry/marker gate, sector-time fitting, interior-residual block, 3% scale block or pair-gap block is applied to Tier 1. These remain unchanged for Tier 2.", "",
        "Cumulative bounds below are raw metres before canonical distance normalization. Quantiles use nearest rank over all speed-ready eligible laps, including those in reference-less sessions. Tier-1-only distributions and per-session denominators are also retained in the ledger. The bound is an endpoint-speed model diagnostic, not a physical guarantee, calibrated probability or independent validation.", "",
        f"Mode: `{report['reference_mode']}`. Sessions: {len(report['sessions'])}. Catalogue: `{report['catalogue_sha256']}`.", "",
        "| Year | Eligible | V5 graphs % | Tier 0 | Tier 0 % | Tier 1 | Tier 1 % | Bound P50 m | P90 m | P99 m |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for year, row in report["by_year"].items():
        n, d = row["eligible_laps"], row["bound_distribution"]
        fmt = lambda v: "n/a" if v is None else f"{v:.3f}"
        lines.append(f"| {year} | {n} | {100*row['v5_telemetry']/n:.2f} | {row['tier0']} | {100*row['tier0']/n:.2f} | {row['tier1']} | {100*row['tier1']/n:.2f} | {fmt(d['p50_m'])} | {fmt(d['p90_m'])} | {fmt(d['p99_m'])} |")
    lines += ["", "## Remaining first failures", "", "| Year | Gate | Laps |", "| --- | --- | ---: |"]
    for year, row in report["by_year"].items():
        for gate, count in sorted(row["first_failure"].items()):
            lines.append(f"| {year} | {gate} | {count} |")
    lines += ["", "## Per-session coverage", "", "| Session | Eligible | Tier 0 | Tier 1 | First failures |", "| --- | ---: | ---: | ---: | --- |"]
    for session in report["sessions"]:
        row = session["summary"]
        lines.append(f"| {session['session_id']} | {row['eligible_laps']} | {row['tier0']} | {row['tier1']} | {json.dumps(row['first_failure'], sort_keys=True)} |")
    lines += ["", "## Qualification", "",
        "Grade C is currently assigned for an absolute S1/S2 interior residual above 150 ms; other results remain ungraded pending the proposed distribution-based review. A small or zero endpoint-model bound does not establish accuracy, especially for equal endpoint speeds. Bridged spans never feed corner observations.",
        "The 80-90% Tier 1 projection for 2022-2025 is a hypothesis, not an acceptance target. Compare the measured rows above; no threshold was tuned to reach that range.",
        "Existing v5 runtime bytes, inputs and Tier 2 body hashes remain frozen. The old endpoint retains its original serializers/IDs; v6 is opt-in and has separate publications.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", nargs="+")
    parser.add_argument("--output", type=Path, default=ROOT / "services/api/src/lapdna/view_data")
    parser.add_argument("--ledger", type=Path, default=ROOT / "config/view-coverage-legacy-reference.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/24-v6-view-coverage-legacy-reference.md")
    parser.add_argument("--lap-ledger", type=Path, default=ROOT / "config/view-laps-legacy-reference.jsonl.gz")
    args = parser.parse_args(argv)
    baseline = json.loads((ROOT / "config/telemetry-coverage.json").read_bytes())
    protected = baseline["gate_attribution"]["runtime_sha256"]
    for name, expected in protected.items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    assert protected_functions() == baseline["gate_attribution"]["tier2_function_sha256"]
    source_hash = canonical_hash({name: sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        "scripts/attribute_view_gates.py", "services/api/src/lapdna/alignment/view.py",
        "services/api/src/lapdna/alignment/view_delta.py", "services/api/src/lapdna/analysis/views.py")})
    pilot = ROOT / "services/api/src/lapdna/pilot_data"
    catalogue_hash = sha256((pilot / "publication.json").read_bytes()).hexdigest()
    assert catalogue_hash == baseline["gate_attribution"]["catalogue_sha256"]
    store, snapshots = PilotStore(pilot), snapshots_by_digest()
    entries = [row for row in baseline["sessions"] if not args.sessions or row["session_id"] in args.sessions]
    if not entries or args.sessions and len(entries) != len(set(args.sessions)):
        raise ValueError("Unknown sessions")
    if args.sessions and args.ledger == ROOT / "config/view-coverage-legacy-reference.json":
        raise ValueError("Partial audits require separate --ledger, --report and --lap-ledger outputs")
    work = ROOT / "work/view-attribution"
    work.mkdir(parents=True, exist_ok=True)
    sessions = []
    for entry in entries:
        sid = entry["session_id"]
        cache = work / (sid + ".json")
        snapshot_path = snapshots[entry["source_snapshot_sha256"]]
        source_bytes = snapshot_path.read_bytes()
        source_file_hash = sha256(source_bytes).hexdigest()
        key = [source_hash, source_file_hash, entry["source_snapshot_sha256"], entry["publication_sha256"]]
        saved = json.loads(cache.read_bytes()) if cache.exists() else None
        if saved and saved["key"] == key:
            from lapdna.analysis.view_store import ViewStore
            publication = ViewStore(args.output).load(sid)
            assert publication["publication_sha256"] == saved["session"]["view_publication_sha256"]
            session = saved["session"]
        else:
            snapshot = json.loads(source_bytes)
            assert canonical_hash(snapshot) == entry["source_snapshot_sha256"]
            legacy = store.load(sid)
            assert legacy["publication_sha256"] == entry["publication_sha256"]
            publication = prepare_views(snapshot, legacy)
            write_publication(args.output, publication)
            session = session_measurement(publication, entry)
            atomic_json(cache, {"key": key, "session": session})
        sessions.append(session)
        row = summarize([session])
        print(f"{sid}: Tier 0 {row['tier0']}/{row['eligible_laps']}; Tier 1 {row['tier1']}; {row['first_failure']}", flush=True)
    args.lap_ledger.parent.mkdir(parents=True, exist_ok=True)
    with args.lap_ledger.open("wb") as file:
        with gzip.GzipFile(fileobj=file, mode="wb", mtime=0, filename="") as stream:
            for session in sessions:
                for lap in session["laps"]:
                    stream.write((json.dumps({"session_id": session["session_id"], **lap}, allow_nan=False, separators=(",", ":")) + "\n").encode())
    report = {"audit_version": "v6-linear-bound-1", "reference_mode": "legacy_v5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "implementation_sha256": source_hash, "catalogue_sha256": catalogue_hash,
        "runtime_sha256": protected, "tier2_function_sha256": protected_functions(),
        "per_lap_ledger": {"path": args.lap_ledger.resolve().relative_to(ROOT).as_posix(), "sha256": sha256(args.lap_ledger.read_bytes()).hexdigest()},
        "by_year": {str(year): summarize([s for s in sessions if s["year"] == year]) for year in sorted({s["year"] for s in sessions})},
        "totals": summarize(sessions), "sessions": [{**{k: v for k, v in s.items() if k != "laps"}, "summary": summarize([s])} for s in sessions]}
    atomic_json(args.ledger, report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(report), encoding="utf-8", newline="\n")
    assert protected_functions() == baseline["gate_attribution"]["tier2_function_sha256"]
    assert catalogue_hash == sha256((pilot / "publication.json").read_bytes()).hexdigest()
    print("Wrote v6 coverage receipt", flush=True)


if __name__ == "__main__":
    main()
