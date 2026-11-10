import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
audit = importlib.import_module("attribute_view_gates")


def test_bound_distribution_uses_nearest_rank_in_metres():
    result = audit.bounds_distribution(list(range(1, 101)))
    assert result == {"count": 100, "p50_m": 50, "p90_m": 90, "p99_m": 99, "maximum_m": 100}
    assert audit.bounds_distribution([])["p50_m"] is None


def test_coverage_keeps_reference_failures_in_fixed_denominator():
    session = {"v5_telemetry": 0, "laps": [
        {"tier0": True, "tier1": False, "speed_candidate": True,
         "cumulative_bound_m": 4., "first_failure": "session_reference"},
        {"tier0": True, "tier1": False, "speed_candidate": False,
         "cumulative_bound_m": None, "first_failure": "speed_gap_over_2s"}]}
    result = audit.summarize([session])
    assert result["eligible_laps"] == 2
    assert result["tier0"] == 2 and result["tier1"] == 0
    assert result["bound_distribution"]["count"] == 1
    assert result["tier1_bound_distribution"]["count"] == 0
    assert sum(result["first_failure"].values()) == 2
