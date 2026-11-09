import io
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from lapdna.ingestion import openf1, tracing
from lapdna.ingestion.openf1 import (
    ImportFailure, OpenF1Client, atomic_json, channel_statistics, deletion_records,
    import_session, normalize_laps, phase_windows,
)
from lapdna.ingestion.tracing import archive_json, combine_laps, column_rows, enrich_snapshot


def control():
    return [
        {"date": f"2024-08-31T14:{minute:02}:00+00:00", "qualifying_phase": phase, "message": message}
        for phase, begin, finish in ((1, 0, 18), (2, 29, 44), (3, 52, 59))
        for minute, message in ((begin, "SESSION STARTED"), (finish, "SESSION FINISHED"))
    ]


def lap():
    return {"driver_number": 4, "lap_number": 11, "date_start": "2024-08-31T14:53:00+00:00", "lap_duration": 79.327,
        "duration_sector_1": 26.492, "duration_sector_2": 26.579, "duration_sector_3": 26.256,
        "is_pit_out_lap": False, "segments_sector_1": [2049], "segments_sector_2": [2049], "segments_sector_3": [2049]}


def normalized():
    return normalize_laps([lap()], control(), [{"driver_number": 4, "lap_start": 10, "lap_end": 12, "compound": "SOFT", "tyre_age_at_start": 0}],
        [{"date": "2024-08-31T14:53:20+00:00", "rainfall": 0}], 9586)[0]


def test_phase_requires_source_status_not_lap_order():
    assert [row["phase"] for row in phase_windows(control())] == ["Q1", "Q2", "Q3"]
    assert normalized()["phase"] == "Q3"
    with pytest.raises(ImportFailure, match="Q3"):
        phase_windows(control()[:-1])


def test_openf1_unknown_fastf1_flags_stay_unknown_and_timing_edges_disclosed():
    row = normalized()
    assert row["timing_candidate"] is True
    assert row["source_flags"]["Deleted"] is None
    assert row["source_flags"]["IsAccurate"] is None
    assert row["source_flags"]["FastF1Generated"] is None
    assert row["sector_times_ms"] == [26492, 26579, 26256]
    assert "approximate" in row["timing_edge_basis"]


def test_deletion_reinstatement_and_pit_codes_are_not_guessed_timings():
    records = [{"date": "2024-08-31T14:54:00+00:00", "message": "CAR 4 (NOR) TIME 1:19.327 DELETED - TRACK LIMITS AT TURN 2 LAP 11"},
        {"date": "2024-08-31T14:55:00+00:00", "message": "CAR 4 (NOR) TIME REINSTATED LAP 11"}]
    assert deletion_records(records)[(4, 11)]["deleted"] is False
    raw = lap()
    raw["segments_sector_3"] = [2049, 2064]
    value = normalize_laps([raw], control(), [{"driver_number": 4, "lap_start": 11, "lap_end": 11, "compound": "SOFT"}],
        [{"date": raw["date_start"], "rainfall": 0}], 9586)[0]
    assert "pit_lane_segment" in value["exclusion_reasons"]


def test_sentinels_and_missing_rows_do_not_become_measured_zero_or_brake_off():
    result = channel_statistics([{"speed": 0, "brake": 0, "throttle": 0, "n_gear": 0}, {"speed": 280, "brake": 104, "throttle": 104}, {"speed": 240}])
    assert result["present"]["speed"] == 3
    assert result["present"]["brake"] == 2
    assert result["invalid"]["brake"] == result["invalid"]["throttle"] == 1
    assert result["missing"]["brake"] == 1


def test_hashed_cache_reuses_exact_records_and_detects_tampering(tmp_path):
    calls = []
    def opener(request, timeout):
        calls.append(request.full_url)
        return io.BytesIO(b'[{"session_key":9586,"driver_number":4,"speed":0}]')
    client = OpenF1Client(tmp_path, opener=opener, sleep=lambda _: None)
    assert client.fetch("car_data", 9586, 4)[0]["speed"] == 0
    assert client.fetch("car_data", 9586, 4)[0]["speed"] == 0
    assert len(calls) == 1
    (tmp_path / "car_data-4.json").write_text("[]")
    assert len(client.fetch("car_data", 9586, 4)) == 1
    assert len(calls) == 2


def test_access_error_is_sanitized_and_long_retry_retains_progress(tmp_path):
    def denied(request, timeout):
        raise HTTPError(request.full_url, 401, "private detail", {}, None)
    with pytest.raises(ImportFailure) as denied_error:
        OpenF1Client(tmp_path, opener=denied, sleep=lambda _: None).fetch("laps", 9586)
    assert denied_error.value.code == "access_required"
    assert "private detail" not in str(denied_error.value)
    def limited(request, timeout):
        raise HTTPError(request.full_url, 429, "private", {"Retry-After": "120"}, None)
    with pytest.raises(ImportFailure) as retry_error:
        OpenF1Client(tmp_path, opener=limited, sleep=lambda _: None).fetch("laps", 9586)
    assert retry_error.value.code == "retry_later"


def test_atomic_write_failure_keeps_prior_publication_and_cleans_temp(tmp_path, monkeypatch):
    target = tmp_path / "snapshot.json"
    target.write_text('{"old":true}')
    original_replace = Path.replace
    def fail_replace(path, destination):
        if destination == target:
            raise OSError("disk unavailable")
        return original_replace(path, destination)
    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError):
        atomic_json(target, {"new": True})
    assert json.loads(target.read_text()) == {"old": True}
    assert not (tmp_path / "snapshot.json.tmp").exists()


def archive_inputs():
    row = normalized()
    archive = {"lap": [11], "dNum": ["4"], "drv": ["NOR"], "time": [79.327], "s1": [26.492], "s2": [26.579], "s3": [26.256],
        "lST": [60], "sesT": [139.327], "qs": ["Q3"], "del": [False], "ff1G": [False], "iacc": [True], "pin": ["None"], "pout": ["None"],
        "status": ["1"], "compound": ["SOFT"], "life": [2], "s1T": [86.492], "s2T": [113.071], "s3T": [139.327]}
    info = {"t0_date": "2024-08-31T14:52:00", "session_info": {"Key": 9586, "Meeting": {"Key": 1244}, "Path": "2024/2024-09-01_Italian_Grand_Prix/2024-08-31_Qualifying/"}}
    drivers = [{"driver_number": 4, "name_acronym": "NOR"}]
    return row, drivers, {"NOR": archive}, info


def test_composite_uses_actual_clock_and_original_flags_only_after_identity_check():
    row, drivers, archives, info = archive_inputs()
    result, report = combine_laps([row], drivers, archives, info)
    assert result[0]["timing_candidate"] is True
    assert result[0]["source_flags"]["IsAccurate"] is True
    assert result[0]["sector_crossing_utc"][0] == "2024-08-31T14:53:26.492000+00:00"
    assert report["independent_validation"] is False
    assert report["driver_lap_identity_count"] == 1
    archives["NOR"]["s2"] = [26.58]
    with pytest.raises(ImportFailure) as error:
        combine_laps([row], drivers, archives, info)
    assert error.value.code == "source_timing_mismatch"


def test_unknown_archived_flags_or_incomplete_fields_cannot_pass():
    row, drivers, archives, info = archive_inputs()
    archives["NOR"]["del"] = ["None"]
    result, _ = combine_laps([row], drivers, archives, info)
    assert result[0]["timing_candidate"] is False
    assert "lap_deleted_or_unknown" in result[0]["exclusion_reasons"]
    archives["NOR"].pop("pin")
    with pytest.raises(ImportFailure):
        column_rows(archives["NOR"])


def test_unreviewed_round_cannot_be_attached_to_verified_session(tmp_path):
    with pytest.raises(ImportFailure) as error:
        import_session(tmp_path, round_number=17)
    assert error.value.code == "unreviewed_session"
    assert not list(tmp_path.iterdir())


def test_oversized_or_foreign_source_never_enters_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(openf1, "MAX_SOURCE_BYTES", 32)
    client = OpenF1Client(tmp_path, opener=lambda request, timeout: io.BytesIO(b"x" * 33), sleep=lambda _: None)
    with pytest.raises(ImportFailure) as error:
        client.fetch("car_data", 9586, 4)
    assert error.value.code == "source_too_large"
    assert not list(tmp_path.iterdir())
    monkeypatch.setattr(openf1, "MAX_SOURCE_BYTES", 1024)
    for payload, code in ((b'[{"session_key":9999,"driver_number":4}]', "foreign_session"),
                          (b'[{"session_key":9586,"driver_number":81}]', "foreign_driver")):
        client = OpenF1Client(tmp_path, opener=lambda request, timeout: io.BytesIO(payload), sleep=lambda _: None)
        with pytest.raises(ImportFailure) as error:
            client.fetch("car_data", 9586, 4)
        assert error.value.code == code
        assert not list(tmp_path.iterdir())


def test_merged_archive_telemetry_is_outside_native_import_allowlist(tmp_path):
    with pytest.raises(ImportFailure) as error:
        archive_json(tmp_path, "NOR/11_tel.json", opener=lambda *_args, **_kwargs: pytest.fail("must not fetch"))
    assert error.value.code == "archive_path_invalid"
    assert not list(tmp_path.iterdir())


def test_failed_composite_reconciliation_preserves_active_snapshot(tmp_path, monkeypatch):
    row, drivers, archives, info = archive_inputs()
    archives["NOR"]["s1"] = [26.493]
    original_pointer = {"source_digest": "previous", "snapshot_path": "previous-snapshot.json"}
    atomic_json(tmp_path / "snapshot-pointer.json", original_pointer)
    source = tmp_path / "openf1.json"
    atomic_json(source, {"drivers": drivers, "laps": [row], "provenance": {"source_records": []}})
    def cached_archive(_cache, name):
        return (info if name == "session_info.json" else archives["NOR"]), {"source_url": name, "sha256": "fixture"}
    monkeypatch.setattr(tracing, "archive_json", cached_archive)
    with pytest.raises(ImportFailure) as error:
        enrich_snapshot(source, tmp_path, progress=lambda _: None)
    assert error.value.code == "source_timing_mismatch"
    assert json.loads((tmp_path / "snapshot-pointer.json").read_text()) == original_pointer
    assert not (tmp_path / "snapshots").exists()


def test_time_window_cache_keeps_native_utc_rows_and_rejects_ignored_filters(tmp_path):
    from datetime import datetime, timezone, timedelta
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(minutes=10)
    payload = [{"session_key": 9586, "driver_number": 4, "date": start.isoformat(), "brake": 0}]
    requests = []
    def opener(request, timeout):
        requests.append(request.full_url)
        return io.BytesIO(json.dumps(payload).encode())
    client = OpenF1Client(tmp_path, opener=opener, sleep=lambda _: None)
    assert client.fetch("car_data", 9586, start=start, end=end) == payload
    assert client.fetch("car_data", 9586, start=start, end=end) == payload
    assert len(requests) == 1 and "date%3E=" in requests[0]
    payload[0]["date"] = (end + timedelta(seconds=1)).isoformat()
    with pytest.raises(ImportFailure) as error:
        client.fetch("car_data", 9586, start=start + timedelta(seconds=1), end=end)
    assert error.value.code == "source_filter_mismatch"


def test_generalized_archive_identity_still_rejects_another_event():
    row, drivers, archives, info = archive_inputs()
    spec = {"session_key": 9492, "meeting_key": 1232,
            "archive_session_path": "2024/2024-04-07_Japanese_Grand_Prix/2024-04-06_Qualifying/"}
    with pytest.raises(ImportFailure) as error:
        combine_laps([row], drivers, archives, info, spec=spec)
    assert error.value.code == "archive_session_mismatch"
    info["session_info"].update(Key=9492, Meeting={"Key":1232}, Path=spec["archive_session_path"])
    assert combine_laps([row], drivers, archives, info, spec=spec)[1]["session_identity_verified"]


def test_empty_filtered_native_range_stays_empty_without_masking_missing_metadata(tmp_path):
    from datetime import datetime, timezone, timedelta
    def missing(request, timeout):
        raise HTTPError(request.full_url, 404, "No matching records", {}, None)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    client = OpenF1Client(tmp_path, opener=missing, sleep=lambda _: None)
    assert client.fetch("car_data", 9586, start=start, end=start+timedelta(minutes=10)) == []
    assert client.records[-1]["http_status"] == 404
    with pytest.raises(ImportFailure) as error:
        client.fetch("laps", 9586)
    assert error.value.code == "source_missing"
