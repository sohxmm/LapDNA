"""Artificial source messages exercise field absence before library default filling."""

import base64
import json
import zlib

import pytest

from lapdna.ingestion.fastf1_native import native_rows, stream_records
from lapdna.ingestion.openf1 import ImportFailure


def frame(value):
    compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    raw = compressor.compress(json.dumps(value).encode()) + compressor.flush()
    return b"00:00:01.000" + json.dumps(base64.b64encode(raw).decode()).encode() + b"\r\n"


def test_native_absence_never_becomes_zero_false_or_another_drivers_sample():
    raw = frame({"Entries": [{"Utc": "2018-09-01T13:00:00.1234567Z", "Cars": {
        "44": {"Channels": {"2": 250, "3": 7}},
        "5": {"Channels": {"2": 240, "3": 6, "4": 104, "5": 100}},
    }}]})
    rows = native_rows(raw, "car")
    assert rows["44"][0]["speed"] == 250
    assert "brake" not in rows["44"][0] and "throttle" not in rows["44"][0]
    assert "drs" not in rows["44"][0]  # no library-inserted off-state
    assert rows["5"][0]["throttle"] == 104  # preserve sentinel for downstream mask
    assert rows["5"][0]["brake"] == 100
    assert rows["44"][0]["date"] == "2018-09-01T13:00:00.123456+00:00"


def test_missing_native_coordinates_and_status_never_become_map_origin_or_offtrack():
    raw = frame({"Position": [{"Timestamp": "2019-01-01T00:00:01Z", "Entries": {
        "44": {"X": 0, "Y": 10}, "5": {"Y": 12, "Z": 3},
    }}]})
    rows = native_rows(raw, "position")
    assert rows["44"][0]["x"] == 0  # a genuine zero is retained
    assert "status" not in rows["44"][0]
    assert "x" not in rows["5"][0] and "status" not in rows["5"][0]


def test_corrupt_or_oversized_frames_fail_before_native_publication(monkeypatch):
    from lapdna.ingestion import fastf1_native
    with pytest.raises(ImportFailure):
        list(stream_records(b'00:00:01.000"not_base64"', compressed=True))
    monkeypatch.setattr(fastf1_native, "MAX_FRAME_BYTES", 10)
    with pytest.raises(ImportFailure) as error:
        list(stream_records(frame({"Entries": ["x" * 100]}), compressed=True))
    assert error.value.code == "native_frame_too_large"


def test_complete_primary_snapshot_can_be_reused_offline_before_loading_optional_dependencies(tmp_path):
    from lapdna.ingestion.fastf1_native import import_fastf1_session
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"source":"fastf1", "session":{"year":2018,"round":14},
        "provenance":{"fastf1_version":"3.9.2","native_mask_policy":"raw-presence-v1"}}))
    (tmp_path / "snapshot-pointer.json").write_text(json.dumps({"snapshot_path":str(snapshot)}))
    assert import_fastf1_session(tmp_path, 2018, 14, progress=lambda _:None) == snapshot


def test_lap_window_excludes_stale_samples_but_rejects_unknown_driver_during_laps():
    from lapdna.ingestion.fastf1_native import lap_window_rows
    stream = {"1": [{"date":"2019-07-27T12:27:00Z", "speed":100}],
              "44": [{"date":"2019-07-27T13:00:00Z", "speed":200}]}
    kept, excluded = lap_window_rows(stream, {"44"}, "2019-07-27T13:00:00Z", "2019-07-27T13:02:00Z")
    assert excluded == 1 and kept == {"44":stream["44"]}
    stream["1"][0]["date"] = "2019-07-27T13:01:00Z"
    with pytest.raises(ImportFailure, match="unknown driver inside"):
        lap_window_rows(stream, {"44"}, "2019-07-27T13:00:00Z", "2019-07-27T13:02:00Z")


def test_unassigned_stream_is_quarantined_only_when_every_timed_driver_matches_roster():
    from lapdna.ingestion.fastf1_native import quarantine_unrostered
    stream = {"23":[{"speed":100}], "2":[{"speed":50}]}
    kept, excluded = quarantine_unrostered(stream, {"23"}, {"23"})
    assert kept == {"23":stream["23"]} and excluded == {"2":1}
    with pytest.raises(ImportFailure, match="Actual lap timing"):
        quarantine_unrostered(stream, {"23"}, {"23","2"})
