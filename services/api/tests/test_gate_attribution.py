"""Artificial fixtures verify the offline audit; no production telemetry is added."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import pytest

from lapdna.alignment.native import AlignmentError, aligned_channels, prepare_lap
from lapdna.analysis.engine import quality

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("gate_audit", ROOT / "scripts/attribute_telemetry_gates.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
START = datetime(2024, 1, 1, tzinfo=timezone.utc)


def rows_at(times):
    return [{"date": (START + timedelta(seconds=t)).isoformat(), "speed": 36} for t in times]


def inputs(capability="telemetry", length=20, sectors=None):
    raw = {"lap_id": "a", "lap_start_utc": START.isoformat(),
           "lap_end_utc": (START + timedelta(seconds=2)).isoformat(),
           "lap_time_ms": 2000, "sector_times_ms": sectors or [500, 500, 1000]}
    option = {"lap_id": "a", "driver_number": "1", "phase": "Q1",
              "capability": capability, "reasons": []}
    publication = {"reference_lap_id": "ref", "distance_m": [0, length / 4, length / 2, length],
                   "sector_boundaries_m": [length / 4, length / 2], "laps": {}}
    return raw, option, publication


def test_passing_lap_matches_v5_and_missing_optional_channels_do_not_block_graphs():
    raw, option, pub = inputs()
    rows = rows_at([0, .5, 1, 1.5, 2])
    original = prepare_lap(rows, START.timestamp(), START.timestamp() + 2, 20)
    pub["laps"]["a"] = {"channels": aligned_channels(original, pub["distance_m"])}
    record, distributions = audit.probe_lap(raw, option, rows, pub)
    assert record["first_failed_gate"] is None
    assert record["all_failed_lap_gates"] == []
    assert record["measurements"]["missing_channels"] == ["throttle", "gear", "brake", "rpm"]
    assert distributions["native_speed_spacing"] == {500000: 4}


def test_collects_all_conditional_failures_without_accepting_a_gap_or_changing_v5():
    raw, option, pub = inputs("sector_only", length=10, sectors=[200, 200, 1600])
    rows = rows_at([0, .5, 1.8, 2])
    with pytest.raises(AlignmentError, match="native speed gap"):
        prepare_lap(rows, START.timestamp(), START.timestamp() + 2, 10)
    record, _ = audit.probe_lap(raw, option, rows, pub)
    assert record["first_failed_gate"] == "native_gap"
    assert set(record["all_failed_lap_gates"]) == {"native_gap", "interior_residual", "scale"}
    assert record["diagnostic_continuation"] is True
    with pytest.raises(AlignmentError, match="native speed gap"):
        prepare_lap(rows, START.timestamp(), START.timestamp() + 2, 10)


def test_missing_reference_is_not_reported_as_passing_residual_or_scale():
    raw, option, _ = inputs("sector_only")
    record, _ = audit.probe_lap(raw, option, rows_at([0, .5, 1.8, 2]), {"reference_lap_id": None})
    assert record["first_failed_gate"] == "native_gap"
    assert "session_reference" in record["all_failed_lap_gates"]
    assert "interior_residual" in record["not_evaluated"] and "scale" in record["not_evaluated"]
    assert "scale_factor" not in record["measurements"]


def test_missing_clock_is_unknown_not_a_zero_duration_or_false_pass():
    raw, option, pub = inputs("unavailable")
    raw["lap_start_utc"] = None
    option["reasons"] = ["source_clock_unavailable"]
    record, _ = audit.probe_lap(raw, option, [], pub)
    assert record["first_failed_gate"] == "timing_eligibility"
    assert record["not_evaluated"]["native_gap"] == "missing/invalid lap-clock edges"
    assert "sliced_duration_residual_ms" not in record["measurements"]


@pytest.mark.parametrize("gate", ["sector_sum", "sliced_duration"])
def test_earlier_importer_five_ms_gate_is_not_hidden_by_later_twenty_ms_limit(gate):
    raw, option, pub = inputs("unavailable")
    raw["exclusion_reasons"] = option["reasons"] = ["native_timing_inconsistent"]
    if gate == "sector_sum":
        raw["sector_times_ms"] = [500, 500, 1006]
    else:
        raw["lap_end_utc"] = (START + timedelta(seconds=2.006)).isoformat()
    record, _ = audit.probe_lap(raw, option, rows_at([0, .5, 1, 1.5, 2.1]), pub)
    assert record["first_failed_gate"] == gate
    assert gate in record["all_failed_lap_gates"]
    assert "timing_eligibility" not in record["all_failed_lap_gates"]
    assert record["measurements"]["source_import_consistency_limit_ms"] == 5
    assert abs(record["measurements"].get("sliced_duration_residual_ms", 0)) < 20
    assert abs(record["measurements"]["sector_sum_residual_ms"]) < 20


def test_distribution_bins_and_weighted_quantiles_use_actual_interval_counts():
    result = audit.distribution(Counter({250000: 8, 750000: 1, 1200000: 1}))
    assert result["count"] == 10 and result["p50_ms"] == 250 and result["p99_ms"] == 1200
    assert result["bins"] == {"(100, 250] ms": 8, "(500, 750] ms": 1, "(1000, 1500] ms": 1}


def pair_record(identifier, driver, residual, capability="telemetry"):
    return {"lap_id": identifier, "driver_number": driver, "phase": "Q1", "timing_eligible_v5": True,
            "capability_v5": capability, "pair_context": {}, "measurements": {
                "interior_residual_ms": [residual, residual], "sliced_duration_residual_ms": 0,
                "sector_sum_residual_ms": 0, "scale_factor": 1., "max_speed_gap_ms": 250.}}


def test_pair_gaps_are_context_not_an_intrinsic_lap_failure_and_match_current_quality():
    a, b = pair_record("a", "1", -100), pair_record("b", "2", 100)
    result = audit.pair_attribution([a, b])["same_phase"]
    assert result["actual_first_failed_gate"] == {"pair_sector_1": 1}
    assert result["actual_pair_gap_failures"] == {"pair_sector_1": 1, "pair_sector_2": 1}
    assert a["pair_context"]["same_phase"]["example_failed_peer"]["lap_id"] == "b"
    pub = {"reference_lap_id": "ref", "distance_m": [0, 5, 10, 20], "sector_boundaries_m": [5, 10], "provenance": {"source": "fastf1"}}
    def native_record(record):
        r = record["measurements"]["interior_residual_ms"][0]
        return {"metadata": {"lap_id": record["lap_id"], "lap_time_ms": 2000, "sector_times_ms": [500, 500, 1000]},
                "channels": {"time_raw_ms": [0, 500+r, 1000+r, 2000]},
                "scale_factor": 1., "max_native_gap_ms": 250., "native_count": 10, "integrated_length_m": 20.}
    assert quality(pub, native_record(a), native_record(b))["status"] == "block"


def test_same_driver_and_blocked_lap_pair_probes_do_not_become_current_graph_acceptance():
    a, b = pair_record("a", "1", -100), pair_record("b", "1", 100)
    result = audit.pair_attribution([a, b])["same_driver_selection_blocked"]
    assert result["actual_evaluated"] == 0 and result["diagnostic_evaluated"] == 1
    assert result["actual_first_failed_gate"] == {"selection_same_driver": 1}
    b = pair_record("b", "2", 100, "sector_only")
    result = audit.pair_attribution([pair_record("a", "1", -100), b])["same_phase"]
    assert result["actual_first_failed_gate"] == {"missing_alignment": 1}
    assert result["actual_pair_gap_failures"] == {}
    assert result["diagnostic_pair_gap_failures"] == {"pair_sector_1": 1, "pair_sector_2": 1}
