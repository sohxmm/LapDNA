"""Wire contracts. Units and delta orientation are part of the public API."""

from datetime import datetime
from math import isclose
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")]
Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Finite = Annotated[float, Field(allow_inf_nan=False)]
Nonnegative = Annotated[Finite, Field(ge=0)]
QualityStatus = Literal["pass", "warn", "block"]
DriverSlot = Literal["A", "B"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Health(Contract):
    status: Literal["ok"] = "ok"
    service: Literal["lapdna-api"] = "lapdna-api"
    version: str


class ErrorDetail(Contract):
    code: str
    message: str


class ErrorResponse(Contract):
    error: ErrorDetail


class SessionIdentity(Contract):
    year: Annotated[int, Field(strict=True, ge=2018, le=2100)]
    round: Annotated[int, Field(strict=True, ge=1, le=30)]
    session_type: Literal["Q"] = "Q"
    phase: Literal["Q1", "Q2", "Q3"]
    circuit_id: Literal["monza", "silverstone", "suzuka"]
    event_name: Annotated[str, Field(min_length=1, max_length=150)]


class LapMetadata(Contract):
    lap_id: Identifier
    driver_code: Annotated[str, Field(pattern=r"^[A-Z0-9]{2,4}$")]
    driver_name: Annotated[str, Field(min_length=1, max_length=100)]
    driver_number: Annotated[str, Field(pattern=r"^[0-9]{1,3}$")]
    lap_number: Annotated[int, Field(strict=True, ge=1)]
    lap_time_ms: Annotated[Finite, Field(gt=0)]
    sector_times_ms: tuple[Nonnegative, Nonnegative, Nonnegative]
    compound: str
    tyre_life_laps: Annotated[Finite, Field(ge=0)] | None
    track_status: str


class Provenance(Contract):
    source: Literal["fastf1"] = "fastf1"
    fastf1_version: str
    pipeline_version: str
    methodology_version: str
    reference_sha256: Sha256
    source_snapshot_sha256: Sha256
    generated_at: datetime
    source_session: str
    circuit_revision: str
    reference_lap_id: Identifier

    @model_validator(mode="after")
    def require_timezone(self) -> Self:
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must include a timezone")
        return self


class DriverChannels(Contract):
    """Null means unsupported; brake is a switch, never a pressure value."""

    speed_kph: list[Annotated[Finite, Field(ge=0)] | None]
    throttle_pct: list[Annotated[Finite, Field(ge=0, le=100)] | None]
    gear: list[Annotated[int, Field(strict=True, ge=0, le=8)] | None]
    brake: list[StrictBool | None]
    time_raw_ms: list[Nonnegative | None]


class TrackGeometry(Contract):
    """Display coordinates in metres; distance_m is the measurement axis."""

    x: list[Finite | None]
    y: list[Finite | None]


class ReconciliationCheck(Contract):
    driver: Literal["A", "B", "pair"]
    metric: Literal[
        "sector_sum", "sliced_duration", "cumulative_sector_1",
        "cumulative_sector_2", "lap_gap",
    ]
    basis: Literal["timing_record_consistency", "timing_constraint", "cross_lap_consistency", "calibration"]
    official_ms: Finite
    observed_ms: Finite | None
    residual_ms: Finite | None
    status: QualityStatus

    @model_validator(mode="after")
    def coherent_residual(self) -> Self:
        if self.driver == "pair" and self.metric in ("sector_sum", "sliced_duration"):
            raise ValueError("timing-record checks apply to individual drivers")
        if self.driver != "pair" and self.metric == "lap_gap":
            raise ValueError("lap_gap applies to the pair")
        if self.driver != "pair" and (self.official_ms < 0 or (self.observed_ms is not None and self.observed_ms < 0)):
            raise ValueError("individual timing values must be nonnegative")
        if (self.observed_ms is None) != (self.residual_ms is None):
            raise ValueError("observed_ms and residual_ms must both be present or null")
        if self.observed_ms is None and self.status == "pass":
            raise ValueError("an unavailable check cannot pass")
        if self.observed_ms is not None and not isclose(
            self.observed_ms - self.official_ms,
            self.residual_ms,
            abs_tol=1e-6,
        ):
            raise ValueError("residual_ms must equal observed_ms minus official_ms")
        return self


class DistanceScale(Contract):
    integrated_length_m: Annotated[Finite, Field(gt=0)]
    scale_factor: Annotated[Finite, Field(gt=0)]


class QualityReport(Contract):
    status: QualityStatus
    warnings: list[str]
    checks: list[ReconciliationCheck]
    native_samples_a: Annotated[int, Field(strict=True, ge=0)]
    native_samples_b: Annotated[int, Field(strict=True, ge=0)]
    max_native_gap_ms_a: Nonnegative
    max_native_gap_ms_b: Nonnegative
    distance_a: DistanceScale
    distance_b: DistanceScale

    @model_validator(mode="after")
    def respect_check_severity(self) -> Self:
        severity = {"pass": 0, "warn": 1, "block": 2}
        if any(severity[check.status] > severity[self.status] for check in self.checks):
            raise ValueError("quality status cannot be lower than a check status")
        keys = [(check.driver, check.metric) for check in self.checks]
        if len(keys) != len(set(keys)):
            raise ValueError("reconciliation checks must have unique driver/metric keys")
        expected = {
            (driver, metric)
            for driver in ("A", "B")
            for metric in ("sector_sum", "sliced_duration", "cumulative_sector_1", "cumulative_sector_2")
        } | {("pair", metric) for metric in ("cumulative_sector_1", "cumulative_sector_2", "lap_gap")}
        if self.status != "block" and not expected.issubset(set(keys)):
            raise ValueError("usable comparisons require the complete reconciliation check set")
        return self


class MetricEvidence(Contract):
    evidence_id: Identifier
    metric: Literal[
        "segment_gain", "minimum_speed", "entry_speed", "exit_speed",
        "brake_onset", "throttle_pickup", "full_throttle_fraction", "gear_at_marker",
    ]
    unit: Literal["ms", "km/h", "m", "%", "gear"]
    start_m: Nonnegative
    end_m: Nonnegative
    value_a: Finite | None
    value_b: Finite | None
    difference_b_minus_a: Finite | None
    native_samples_a: Annotated[int, Field(strict=True, ge=0)]
    native_samples_b: Annotated[int, Field(strict=True, ge=0)]
    max_support_span_ms_a: Nonnegative
    max_support_span_ms_b: Nonnegative
    interval_a: tuple[Finite, Finite] | None = None
    interval_b: tuple[Finite, Finite] | None = None
    difference_interval_b_minus_a: tuple[Finite, Finite] | None = None

    @model_validator(mode="after")
    def validate_range_and_difference(self) -> Self:
        if self.end_m < self.start_m:
            raise ValueError("evidence end must not precede start")
        for interval in (self.interval_a, self.interval_b, self.difference_interval_b_minus_a):
            if interval is not None and interval[1] < interval[0]:
                raise ValueError("evidence interval bounds must be ordered")
        if self.difference_interval_b_minus_a is not None:
            if self.interval_a is None or self.interval_b is None:
                raise ValueError("a difference interval requires both source intervals")
            expected = (self.interval_b[0] - self.interval_a[1], self.interval_b[1] - self.interval_a[0])
            if not all(isclose(a, b, abs_tol=1e-6) for a, b in zip(expected, self.difference_interval_b_minus_a)):
                raise ValueError("difference interval must represent B minus A")
        if self.difference_b_minus_a is not None:
            if self.value_a is None or self.value_b is None:
                raise ValueError("a difference requires both observed values")
            if not isclose(self.value_b - self.value_a, self.difference_b_minus_a, abs_tol=1e-6):
                raise ValueError("evidence difference must equal B minus A")
        return self


class GainSensitivity(Contract):
    minimum_ms: Finite
    maximum_ms: Finite

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.maximum_ms < self.minimum_ms:
            raise ValueError("gain sensitivity limits must be ordered")
        return self


class Segment(Contract):
    segment_id: Identifier
    kind: Literal["corner", "complex", "straight"]
    group_id: Identifier | None = None
    label: str
    start_m: Nonnegative
    end_m: Nonnegative
    gain_ms: Finite | None
    gain_sensitivity_ms: GainSensitivity | None
    quality_status: QualityStatus
    evidence_ids: list[Identifier]


class Observation(Contract):
    observation_id: Identifier
    template_id: Literal["segment_gain", "speed_pattern", "control_pattern"]
    segment_id: Identifier
    text: Annotated[str, Field(min_length=1, max_length=600)]
    evidence_ids: Annotated[list[Identifier], Field(min_length=1)]


class ComparisonArtifact(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    comparison_id: Identifier
    provenance: Provenance
    session: SessionIdentity
    lap_a: LapMetadata
    lap_b: LapMetadata
    distance_m: Annotated[list[Nonnegative], Field(min_length=2, max_length=5000)]
    channels_a: DriverChannels
    channels_b: DriverChannels
    geometry: TrackGeometry
    delta_ms: list[Finite | None]
    valid: list[StrictBool]
    sector_boundaries_m: tuple[Nonnegative, Nonnegative]
    quality: QualityReport
    segments: list[Segment]
    evidence: list[MetricEvidence]
    observations: Annotated[list[Observation], Field(max_length=3)]
    insufficient_evidence_reason: str | None

    @model_validator(mode="after")
    def validate_comparison(self) -> Self:
        grid = self.distance_m
        size = len(grid)
        if grid[0] != 0 or any(b <= a for a, b in zip(grid, grid[1:])):
            raise ValueError("distance_m must start at zero and strictly increase")
        arrays = [self.delta_ms, self.valid, self.geometry.x, self.geometry.y]
        for channels in (self.channels_a, self.channels_b):
            arrays.extend(getattr(channels, name) for name in type(channels).model_fields)
        if any(len(values) != size for values in arrays):
            raise ValueError("all sample arrays must match distance_m length")
        if not 0 < self.sector_boundaries_m[0] < self.sector_boundaries_m[1] < grid[-1]:
            raise ValueError("sector boundaries must be increasing and internal to the lap")
        if self.lap_a.driver_number == self.lap_b.driver_number:
            raise ValueError("comparison requires two different drivers")
        for index, (delta, valid) in enumerate(zip(self.delta_ms, self.valid)):
            time_a, time_b = self.channels_a.time_raw_ms[index], self.channels_b.time_raw_ms[index]
            supported = time_a is not None and time_b is not None
            if valid and (not supported or delta is None):
                raise ValueError("valid samples require both elapsed times and a delta")
            if not valid and delta is not None:
                raise ValueError("invalid comparison samples must have null delta")
            if delta is not None and not isclose(time_b - time_a, delta, abs_tol=1e-6):
                raise ValueError("delta_ms must equal time B minus time A")
        for x, y in zip(self.geometry.x, self.geometry.y):
            if (x is None) != (y is None):
                raise ValueError("geometry x and y must be null together")
        for channels in (self.channels_a, self.channels_b):
            known = [t for t in channels.time_raw_ms if t is not None]
            if any(b < a for a, b in zip(known, known[1:])):
                raise ValueError("elapsed times must not decrease")
        segment_ids = [s.segment_id for s in self.segments]
        evidence_ids = [e.evidence_id for e in self.evidence]
        observation_ids = [o.observation_id for o in self.observations]
        for ids in (segment_ids, evidence_ids, observation_ids):
            if len(ids) != len(set(ids)):
                raise ValueError("IDs must be unique within each collection")
        evidence_id_set, segment_id_set = set(evidence_ids), set(segment_ids)
        previous_end = 0.0
        grid_indices = {distance: index for index, distance in enumerate(grid)}
        for segment in self.segments:
            if not (0 <= segment.start_m < segment.end_m <= grid[-1]):
                raise ValueError("segment bounds must lie within the lap")
            if segment.start_m != previous_end:
                raise ValueError("segments must form an adjacent partition beginning at zero")
            if segment.start_m not in grid_indices or segment.end_m not in grid_indices:
                raise ValueError("segment boundaries must be inserted in the distance grid")
            previous_end = segment.end_m
            start_index, end_index = grid_indices[segment.start_m], grid_indices[segment.end_m]
            supported = all(self.valid[start_index:end_index + 1])
            if segment.gain_ms is not None:
                if not supported:
                    raise ValueError("segment gain requires full valid elapsed-time support")
                expected_gain = self.delta_ms[end_index] - self.delta_ms[start_index]
                if not isclose(segment.gain_ms, expected_gain, abs_tol=1e-6):
                    raise ValueError("segment gain must equal end delta minus start delta")
            if segment.gain_sensitivity_ms is not None:
                sensitivity = segment.gain_sensitivity_ms
                if segment.gain_ms is None or not sensitivity.minimum_ms <= segment.gain_ms <= sensitivity.maximum_ms:
                    raise ValueError("sensitivity interval must contain the unshifted segment gain")
            if not set(segment.evidence_ids).issubset(evidence_id_set):
                raise ValueError("segment references unknown evidence")
        if self.segments and previous_end != grid[-1]:
            raise ValueError("segment partition must end at lap distance")
        if self.quality.status != "block" and not self.segments:
            raise ValueError("usable comparisons require a segment partition")
        for evidence in self.evidence:
            if evidence.end_m > grid[-1]:
                raise ValueError("evidence must lie within the lap")
        for observation in self.observations:
            if observation.segment_id not in segment_id_set:
                raise ValueError("observation references unknown segment")
            if not set(observation.evidence_ids).issubset(evidence_id_set):
                raise ValueError("observation references unknown evidence")
        if self.quality.status == "block" and self.observations:
            raise ValueError("blocked comparisons must not carry observations")
        if len(self.observations) < 3 and not self.insufficient_evidence_reason:
            raise ValueError("fewer than three observations require an insufficient-evidence reason")
        if len(self.observations) == 3 and self.insufficient_evidence_reason is not None:
            raise ValueError("three observations must not carry an insufficient-evidence reason")
        return self


class ComparisonSummary(Contract):
    comparison_id: Identifier
    session: SessionIdentity
    lap_a: LapMetadata
    lap_b: LapMetadata
    quality_status: QualityStatus


class Catalog(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    comparisons: list[ComparisonSummary]
