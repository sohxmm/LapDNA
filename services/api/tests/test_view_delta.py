import pytest

from lapdna.alignment.native import prepare_lap
from lapdna.alignment.view import CarStream, ViewUnavailable
from lapdna.alignment.view_delta import prepare_progress, align_pair
from test_native_views import EPOCH, rows


def make_view(payload, times, speeds, end=None, slot="lap_a", start=0.):
    data = rows(times)
    for row, speed in zip(data, speeds):
        row["speed"] = speed
    end = times[-1] if end is None else end
    return CarStream(data).view(payload[slot], EPOCH.timestamp() + start, EPOCH.timestamp() + end)


def test_same_v5_equations_without_gap_bridging(artifact_payload):
    data = rows([0, .25, .5, .75, 1])
    for row, speed in zip(data, [100, 110, 130, 120, 90]):
        row["speed"] = speed
    view = CarStream(data).view(artifact_payload["lap_a"], EPOCH.timestamp(), EPOCH.timestamp()+1)
    old = prepare_lap(data, EPOCH.timestamp(), EPOCH.timestamp()+1)
    new = prepare_progress(view)
    assert new.distance_m == old["native"]["distance_m"]
    assert new.elapsed_ms == old["native"]["elapsed_ms"]
    assert new.cumulative_bound_m == [0.] * 5


@pytest.mark.parametrize("dt", [.8, 1., 2.])
def test_bridge_bound_has_correct_units_and_never_changes_clock(artifact_payload, dt):
    view = make_view(artifact_payload, [0, dt], [72, 144])
    lap = prepare_progress(view)
    assert lap.integrated_length_m == pytest.approx(dt * 30)
    assert lap.bridges[0].full_interval_bound_m == pytest.approx(dt * 10)
    assert lap.cumulative_bound_m[-1] == pytest.approx(dt * 10)
    assert lap.elapsed_ms == [0, view.source_duration_ms]
    assert lap.distance_lower_m[-1] == lap.distance_upper_m[-1] == lap.distance_m[-1]
    assert lap.bridges[0].excluded_from_analysis is True


def test_edge_interval_is_clipped_and_bounds_accumulate(artifact_payload):
    view = make_view(artifact_payload, [-.5, .5, 1.5], [72, 108, 144], start=0, end=1)
    lap = prepare_progress(view)
    assert [b.full_interval_bound_m for b in lap.bridges] == [5, 5]
    assert [b.in_lap_bound_m for b in lap.bridges] == [2.5, 2.5]
    assert lap.cumulative_bound_m == [0, 2.5, 5]
    assert lap.source_duration_ms == 1000


def test_over_two_seconds_keeps_tier0_but_blocks_alignment(artifact_payload):
    view = make_view(artifact_payload, [0, 2.001], [100, 110])
    assert view.channels.speed_kph == [100, 110]
    with pytest.raises(ViewUnavailable) as error:
        prepare_progress(view)
    assert error.value.gate == "speed_gap_over_2s"


def test_equal_endpoint_speed_has_zero_model_bound_but_stays_flagged(artifact_payload):
    lap = prepare_progress(make_view(artifact_payload, [0, 1], [100, 100]))
    assert lap.bridges
    assert lap.cumulative_bound_m == [0, 0]


def test_zero_progress_is_not_silently_filled(artifact_payload):
    view = make_view(artifact_payload, [0, .4, .8, 1.2], [100, 0, 0, 100])
    with pytest.raises(ViewUnavailable) as error:
        prepare_progress(view)
    assert error.value.gate == "progress"
    assert view.channels.speed_kph == [100, 0, 0, 100]


def test_nonpositive_uncertainty_normalization_falls_back_instead_of_dividing(artifact_payload):
    view = make_view(artifact_payload, [0, 1], [0, 400])
    with pytest.raises(ViewUnavailable) as error:
        prepare_progress(view)
    assert error.value.gate == "uncertainty_denominator"


def test_delta_band_contains_nominal_and_interior_failure_is_annotation(artifact_payload):
    a = make_view(artifact_payload, [0, .4, 1.4, 1.8], [72, 100, 140, 130])
    b = make_view(artifact_payload, [0, .4, 1.4, 1.9], [72, 90, 150, 130], slot="lap_b")
    ref = {"lap_id": "test-A", "length_m": 60., "sha256": "0"*64,
           "selection_basis": "legacy_v5", "geometry_available": False, "markers_available": False}
    result = align_pair(a, b, ref, [40., 50.])
    assert result.quality_grade == "C"
    assert any(s.grade == "C" for s in result.lap_a.sector_annotations)
    assert result.delta_ms[0] == 0
    assert result.delta_ms[-1] == b.source_duration_ms - a.source_duration_ms
    assert result.delta_lower_ms[-1] == result.delta_upper_ms[-1] == result.delta_ms[-1]
    assert result.lap_a.endpoint_residual_ms == pytest.approx(800, abs=.001)
    assert all(lo <= d <= hi for lo, d, hi in zip(result.delta_lower_ms, result.delta_ms, result.delta_upper_ms))
    assert any(hi > lo for lo, hi in zip(result.delta_lower_ms, result.delta_upper_ms))
