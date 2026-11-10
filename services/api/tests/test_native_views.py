from datetime import datetime, timedelta, timezone

import pytest

from lapdna.alignment.view import CarStream, ViewUnavailable

EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)


def rows(times, **values):
    return [{"date": (EPOCH + timedelta(seconds=t)).isoformat(), "speed": 100,
             "throttle": 0, "rpm": 9000, "n_gear": 3, "brake": 0, **values} for t in times]


def view(artifact_payload, times, **values):
    start = EPOCH.timestamp()
    return CarStream(rows(times, **values)).view(artifact_payload["lap_a"], start, start + 1)


def test_tier0_needs_no_reference_and_keeps_distant_real_padding(artifact_payload):
    result = view(artifact_payload, [-5, .2, .8, 6])
    assert result.elapsed_ms == [-5000, pytest.approx(200), pytest.approx(800), 6000]
    assert result.channels.throttle_pct == [0] * 4
    assert result.channels.brake == [False] * 4
    assert result.sample_masks["brake"] == ["measured"] * 4
    assert result.interpolation["brake"] == "none"


def test_missing_and_discrete_channels_never_invent_values(artifact_payload):
    result = view(artifact_payload, [0, 1], brake=None, rpm=None)
    assert result.channels.brake == [None, None]
    assert result.channels.rpm == [None, None]
    assert result.sample_masks["brake"] == ["gap", "gap"]
    assert all(s.render_hint == "hatched_no_data" for s in result.spans if s.channel in ("gear", "brake"))
    assert next(s for s in result.spans if s.channel == "speed_kph").state == "bridged"


def test_tier0_can_survive_long_gaps_but_labels_breaks(artifact_payload):
    result = view(artifact_payload, [-1, 3])
    assert {s.state for s in result.spans} == {"gap"}


def test_conflicts_are_unknown_not_first_wins(artifact_payload):
    data = rows([0, 1]) + rows([0], speed=120)
    result = CarStream(data).view(artifact_payload["lap_a"], EPOCH.timestamp(), EPOCH.timestamp() + 1)
    assert result.channels.speed_kph == [None, 100]
    assert result.warnings


def test_unbracketed_car_stream_has_explicit_reason(artifact_payload):
    with pytest.raises(ViewUnavailable) as failure:
        view(artifact_payload, [.2, .8])
    assert failure.value.gate == "car_edges"
