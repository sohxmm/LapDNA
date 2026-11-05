"""Deliberately artificial wire-contract data; never copied to app artifacts."""

import pytest


@pytest.fixture
def artifact_payload():
    def lap(slot, number, time, sectors):
        return {
            "lap_id": f"test-{slot}", "driver_code": f"TS{slot}", "phase": "Q3",
            "driver_name": f"Synthetic test {slot}", "driver_number": number,
            "lap_number": 1, "lap_time_ms": time, "sector_times_ms": sectors,
            "compound": "TEST", "tyre_life_laps": None, "track_status": "TEST",
        }

    def channels(times):
        return {
            "speed_kph": [1.0, 2.0, 3.0], "throttle_pct": [0.0, 50.0, 100.0],
            "gear": [1, 1, 2], "brake": [True, False, False], "time_raw_ms": times,
        }

    checks = []
    for driver, lap_time, cumulative1, cumulative2 in (("A", 1000.0, 250.0, 750.0), ("B", 1100.0, 275.0, 825.0)):
        for metric, value in (("sector_sum", lap_time), ("sliced_duration", lap_time), ("cumulative_sector_1", cumulative1), ("cumulative_sector_2", cumulative2)):
            checks.append({
                "driver": driver, "metric": metric, "official_ms": value,
                "observed_ms": value, "residual_ms": 0.0, "status": "pass",
                "basis": "timing_record_consistency" if metric == "sector_sum" else "timing_constraint" if metric == "sliced_duration" else "cross_lap_consistency",
            })
    for metric, value in (("cumulative_sector_1", 25.0), ("cumulative_sector_2", 75.0), ("lap_gap", 100.0)):
        checks.append({
            "driver": "pair", "metric": metric, "official_ms": value,
            "observed_ms": value, "residual_ms": 0.0, "status": "pass",
            "basis": "timing_constraint" if metric == "lap_gap" else "cross_lap_consistency",
        })

    return {
        "schema_version": "1.1.0", "comparison_id": "synthetic-contract-test",
        "detail_level": "telemetry", "pairing": {"mode": "same_phase", "warnings": []},
        "provenance": {
            "source": "fastf1", "fastf1_version": "test", "pipeline_version": "test",
            "methodology_version": "test", "reference_sha256": "0" * 64,
            "source_snapshot_sha256": "1" * 64,
            "generated_at": "2024-01-01T00:00:00Z",
            "source_session": "ARTIFICIAL TEST PAYLOAD; not fetched FastF1 data",
            "circuit_revision": "test-only", "reference_lap_id": "test-reference",
        },
        "session": {
            "year": 2024, "round": 1, "session_type": "Q", "session_id": "synthetic-session",
            "circuit_id": "monza", "event_name": "Synthetic contract test",
        },
        "lap_a": lap("A", "901", 1000.0, [250.0, 500.0, 250.0]),
        "lap_b": lap("B", "902", 1100.0, [275.0, 550.0, 275.0]),
        "distance_m": [0.0, 1.0, 2.0],
        "channels_a": channels([0.0, 500.0, 1000.0]),
        "channels_b": channels([0.0, 550.0, 1100.0]),
        "geometry": {"x": [0.0, 1.0, 0.0], "y": [0.0, 0.0, 1.0]},
        "delta_ms": [0.0, 50.0, 100.0], "valid": [True, True, True],
        "sector_boundaries_m": [0.5, 1.5],
        "quality": {
            "status": "warn", "warnings": ["Artificial data for API tests only"],
            "checks": checks, "native_samples_a": 3, "native_samples_b": 3,
            "max_native_gap_ms_a": 500.0, "max_native_gap_ms_b": 550.0,
            "distance_a": {"integrated_length_m": 2.0, "scale_factor": 1.0},
            "distance_b": {"integrated_length_m": 2.0, "scale_factor": 1.0},
        },
        "segments": [{
            "segment_id": "test-segment", "kind": "straight", "label": "Test interval", "speed_class": None,
            "start_m": 0.0, "end_m": 2.0, "gain_ms": 100.0,
            "gain_sensitivity_ms": {"minimum_ms": 100.0, "maximum_ms": 100.0},
            "quality_status": "warn", "evidence_ids": [],
        }],
        "evidence": [], "observations": [],
        "corners": [],
        "estimated_minisectors": [{"source": "derived_telemetry", "start_m": 0.0, "end_m": 2.0, "gain_ms": 100.0}],
        "analysis": {
            "classification_rule": "reference_apex_minimum_v1", "medium_from_kph": 150.0, "high_from_kph": 250.0,
            "pattern": "insufficient", "pattern_driver": None, "text": "Synthetic straight has no corners.",
            "evidence_ids": [], "limitations": ["Artificial wire-contract test"],
            "categories": [{
                "speed_class": band, "included_segment_ids": [], "excluded_segment_ids": [],
                "independent_units": 0, "distance_coverage": 0.0, "gains_a_ms": None, "gains_b_ms": None,
                "net_gain_ms": None, "a_wins": 0, "b_wins": 0, "neutral_units": 0, "sensitivity": None,
                "assessment": "insufficient", "evidence_ids": [],
            } for band in ("low", "medium", "high")],
        },
        "insufficient_evidence_reason": "Synthetic contract fixture; no publication findings",
    }


@pytest.fixture
def index_payload(artifact_payload):
    payload = artifact_payload
    laps = []
    drivers = []
    for item in (payload["lap_a"], payload["lap_b"]):
        drivers.append({key: item[key] for key in ("driver_number", "driver_code", "driver_name")})
        laps.append({key: value for key, value in item.items() if key not in ("tyre_life_laps", "compound", "track_status")})
        laps[-1].update(capability="telemetry", reasons=[])
    return {
        "schema_version": "1.1.0", "session": payload["session"],
        "source_snapshot_sha256": payload["provenance"]["source_snapshot_sha256"],
        "drivers": drivers, "laps": laps,
    }
