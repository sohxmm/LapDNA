"""Committed derived receipts reconcile without private native caches or network."""
from collections import Counter
import gzip
from hashlib import sha256
import json
from math import ceil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def verify_coverage(name):
    receipt = json.loads((ROOT / f"config/view-coverage-{name}.json").read_bytes())
    baseline = json.loads((ROOT / "config/telemetry-coverage.json").read_bytes())
    assert len(receipt["sessions"]) == baseline["session_count"] == 217
    assert receipt["tier2_function_sha256"] == baseline["gate_attribution"]["tier2_function_sha256"]
    path = ROOT / receipt["per_lap_ledger"]["path"]
    assert sha256(path.read_bytes()).hexdigest() == receipt["per_lap_ledger"]["sha256"]
    rows = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
    assert len(rows) == receipt["totals"]["eligible_laps"] == 25271
    by_id = {session["session_id"]: session for session in receipt["sessions"]}
    for year, summary in receipt["by_year"].items():
        cohort = [row for row in rows if str(by_id[row["session_id"]]["year"]) == year]
        assert len(cohort) == summary["eligible_laps"] == baseline["gate_attribution"]["by_year"][year]["timing_eligible"]["laps"]
        assert sum(row["tier0"] for row in cohort) == summary["tier0"]
        assert sum(row["tier1"] for row in cohort) == summary["tier1"]
        assert dict(Counter(row["first_failure"] for row in cohort if not row["tier1"])) == summary["first_failure"]
        bounds = sorted(row["cumulative_bound_m"] for row in cohort if row["speed_candidate"])
        for key, fraction in (("p50_m", .5), ("p90_m", .9), ("p99_m", .99)):
            assert summary["bound_distribution"][key] == bounds[ceil(len(bounds)*fraction)-1]
    assert all(not row["tier1"] or row["tier0"] and row["speed_candidate"] for row in rows)
    assert all((row["first_failure"] is None) == row["tier1"] for row in rows)
    return receipt


def test_legacy_reference_receipt_preserves_all_year_denominators():
    verify_coverage("legacy-reference")


def test_frozen_v5_compatibility_receipt_still_matches_source_bytes():
    receipt = json.loads((ROOT / "config/v5-view-compatibility.json").read_bytes())
    assert receipt["passing_pairs_compared"] == 464
    assert len(receipt["sessions"]) == 217
    for name, expected in receipt["unchanged_file_sha256"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
