"""Independent closed-form examples for native-clock integration and missingness."""

import pytest

from lapdna.alignment.native import (
    AlignmentError, aligned_channels, elapsed_at, integral_at,
    integrated_distance, native_car, prepare_lap, support,
)


def rows(speed=180, count=11, interval=.25):
    from datetime import datetime, timezone
    return [{"date": datetime.fromtimestamp(i * interval, timezone.utc).isoformat(),
             "speed": speed, "throttle": 100, "n_gear": 5, "brake": 0}
            for i in range(count)]


def test_constant_speed_integral_has_closed_form_and_real_edges():
    prepared = prepare_lap(rows(), .1, 2.1)
    assert prepared["integrated_length_m"] == pytest.approx(100)
    assert elapsed_at(prepared, 25) == pytest.approx(500)
    assert elapsed_at(prepared, 100) == pytest.approx(2000)
    assert prepared["native"]["elapsed_ms"][0] == pytest.approx(-100)


def test_accelerating_native_interval_integrates_partial_interval():
    distance = integrated_distance([0., 1.], [0., 36.])
    assert distance[-1] == pytest.approx(5)
    assert integral_at(.5, [0., 1.], [0., 36.], distance) == pytest.approx(1.25)


def test_missing_edge_is_not_padded():
    with pytest.raises(AlignmentError, match="bracket"):
        prepare_lap(rows(), -.1, 1.5)


def test_long_speed_gap_blocks_alignment():
    with pytest.raises(AlignmentError, match="gap"):
        prepare_lap(rows(interval=1), .1, 3.1)


def test_duplicate_native_timestamp_conflict_fails():
    source = rows()
    source.insert(2, {**source[2], "speed": 200})
    with pytest.raises(AlignmentError, match="conflicting"):
        prepare_lap(source, .1, 2.1)


def test_identical_duplicate_does_not_inflate_native_support():
    source = rows()
    source.insert(2, dict(source[2]))
    assert prepare_lap(source, .1, 2.1)["native"]["native_count"] == 8


def test_gear_and_brake_are_previous_sample_states_and_null_stays_unknown():
    source = rows()
    source[1].update(n_gear=6, brake=100)
    source[2].update(brake=104, throttle=104)
    prepared = prepare_lap(source, 0., 2.)
    channels = aligned_channels(prepared, [0., 6.25, 12.5, 18.75, 25., 100.])
    assert channels["gear"][:4] == [5, 5, 6, 6]
    assert channels["brake"][:5] == [False, False, True, True, None]
    assert channels["throttle_pct"][4] is None
    assert all(type(value) is int for value in channels["gear"])


def test_invalid_speed_is_not_clamped_and_gap_keeps_missing_support():
    source = rows()
    source[2]["speed"] = 500
    prepared = prepare_lap(source, 0., 2.)
    assert prepared["native"]["max_gap_ms"] == pytest.approx(500)
    assert 500 not in prepared["native"]["speed_kph"]


def test_resampling_does_not_increase_native_evidence_counts():
    prepared = prepare_lap(rows(), 0., 2.)
    before = support(prepared, 25., 50.)["count"]
    aligned_channels(prepared, [x / 10 for x in range(1001)])
    assert support(prepared, 25., 50.)["count"] == before == 3


def test_fixed_reference_length_preserves_swap_sign():
    a = prepare_lap(rows(speed=180, count=21), 0., 2., 100.)
    b = prepare_lap(rows(speed=120, count=21), 0., 3., 100.)
    grid = [0., 25., 50., 100.]
    delta = [elapsed_at(b, value) - elapsed_at(a, value) for value in grid]
    assert delta == pytest.approx([0, 250, 500, 1000])
    assert [elapsed_at(a, value) - elapsed_at(b, value) for value in grid] == pytest.approx([-x for x in delta])


def test_marker_windows_merge_without_double_counting_and_keep_mixed_classes():
    from lapdna.alignment.reference import marker_regions
    markers = [{"marker_id": "T" + str(i), "label": "T" + str(i), "distance_m": distance,
                "speed_class": band} for i, distance, band in ((1, 200., "low"), (2, 300., "medium"), (3, 800., "high"))]
    regions = marker_regions(markers, 1000.)
    assert sum(row["end_m"] - row["start_m"] for row in regions) == 1000.
    assert all(a["end_m"] == b["start_m"] for a, b in zip(regions, regions[1:]))
    complexes = [row for row in regions if row["kind"] == "complex"]
    assert len(complexes) == 1 and complexes[0]["speed_class"] == "mixed"
    assert markers[0]["segment_id"] == markers[1]["segment_id"]
    assert markers[2]["segment_id"] != markers[0]["segment_id"]
