"""Wire contracts. Units and delta orientation are part of the public API."""

from bisect import bisect_left, bisect_right
from datetime import datetime
from math import isclose
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")]
Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Finite = Annotated[float, Field(allow_inf_nan=False)]
Nonnegative = Annotated[Finite, Field(ge=0)]
Duration = Annotated[Finite, Field(gt=0)]
QualityStatus = Literal["pass", "warn", "block"]
DriverSlot = Literal["A", "B"]
Phase = Literal["Q1", "Q2", "Q3"]
SpeedClass = Literal["low", "medium", "high"]
SchemaVersion = Literal["1.2.0", "1.3.0"]
Count = Annotated[int, Field(ge=0)]
ShortText = Annotated[str, Field(min_length=1, max_length=600)]
TeamColour = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]


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
    session_id: Identifier
    year: Annotated[int, Field(strict=True, ge=2018, le=2100)]
    round: Annotated[int, Field(strict=True, ge=1, le=30)]
    session_type: Literal["Q"] = "Q"
    circuit_id: Identifier
    event_name: Annotated[str, Field(min_length=1, max_length=150)]


class LapIdentity(Contract):
    lap_id: Identifier
    phase: Phase
    driver_code: Annotated[str, Field(pattern=r"^[A-Z0-9]{2,4}$")]
    driver_name: Annotated[str, Field(min_length=1, max_length=100)]
    driver_number: Annotated[str, Field(pattern=r"^[0-9]{1,3}$")]
    lap_number: Annotated[int, Field(strict=True, ge=1)]


class LapMetadata(LapIdentity):
    team_name: ShortText | None = None
    team_colour: TeamColour | None = None
    lap_time_ms: Duration
    sector_times_ms: tuple[Duration, Duration, Duration]
    compound: str
    tyre_life_laps: Annotated[Finite, Field(ge=0)] | None
    track_status: str
    lap_start_utc: datetime | None = None


class SourceComponent(Contract):
    source: ShortText
    version: str | None = None
    url: str
    sha256: Sha256
    retrieved_at: datetime
    license_name: str | None = None
    license_url: str | None = None


class TimingProvenance(Contract):
    source: Literal["fastf1", "openf1", "openf1_tracinginsights"] = "fastf1"
    fastf1_version: str | None = None
    provider_version: str | None = None
    source_retrieved_at: datetime | None = None
    source_urls: list[str] = []
    verification_scope: str | None = None
    components: list[SourceComponent] = []
    pipeline_version: str
    methodology_version: str
    source_snapshot_sha256: Sha256
    generated_at: datetime
    source_session: str

    @model_validator(mode="after")
    def require_timezone(self) -> Self:
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at must include a timezone")
        if self.source_retrieved_at is not None and self.source_retrieved_at.tzinfo is None:
            raise ValueError("source_retrieved_at must include a timezone")
        if self.source == "fastf1" and not self.fastf1_version:
            raise ValueError("FastF1 provenance requires its library version")
        if self.source == "openf1" and (not self.provider_version or self.fastf1_version is not None):
            raise ValueError("OpenF1 provenance names its provider version, not a FastF1 version")
        if self.source == "openf1_tracinginsights" and (
            not self.provider_version or not {"openf1", "tracinginsights"}.issubset(
                {component.source for component in self.components}
            )
        ):
            raise ValueError("composite provenance requires both explicit source components")
        return self


class Provenance(TimingProvenance):
    reference_sha256: Sha256
    circuit_revision: str
    reference_lap_id: Identifier


class PairingContext(Contract):
    mode: Literal["same_phase", "cross_phase"]
    warnings: list[ShortText]


class ArtifactHeader(Contract):
    schema_version: SchemaVersion = "1.2.0"
    comparison_id: Identifier
    session: SessionIdentity
    lap_a: LapMetadata
    lap_b: LapMetadata
    pairing: PairingContext

    @model_validator(mode="after")
    def validate_pair(self) -> Self:
        if self.lap_a.driver_number == self.lap_b.driver_number or self.lap_a.lap_id == self.lap_b.lap_id:
            raise ValueError("comparison requires distinct drivers and laps")
        cross_phase = self.lap_a.phase != self.lap_b.phase
        if cross_phase != (self.pairing.mode == "cross_phase"):
            raise ValueError("pairing mode must agree with individual lap phases")
        if cross_phase and not self.pairing.warnings:
            raise ValueError("cross-phase comparison requires a visible conditions warning")
        return self


class DriverChannels(Contract):
    """Null means unsupported; brake is a switch, never a pressure value."""

    speed_kph: list[Annotated[Finite, Field(ge=0)] | None]
    throttle_pct: list[Annotated[Finite, Field(ge=0, le=100)] | None]
    gear: list[Annotated[int, Field(strict=True, ge=0, le=8)] | None]
    brake: list[StrictBool | None]
    time_raw_ms: list[Nonnegative | None]


class ChannelProvenance(Contract):
    """An aligned display signal must originate in its named native source channel."""

    status: Literal["measured", "missing"]
    source_channel: ShortText | None
    reason: ShortText | None

    @model_validator(mode="after")
    def require_source_or_reason(self) -> Self:
        if self.status == "measured" and (self.source_channel is None or self.reason is not None):
            raise ValueError("measured channels require their native source field and no missing-data reason")
        if self.status == "missing" and (self.source_channel is not None or self.reason is None):
            raise ValueError("missing channels require an explanation and no claimed source field")
        return self


class ChannelProvenanceSet(Contract):
    speed_kph: ChannelProvenance
    throttle_pct: ChannelProvenance
    gear: ChannelProvenance
    brake: ChannelProvenance


class TrackGeometry(Contract):
    """Display coordinates in metres; distance_m is the measurement axis."""

    x: list[Finite | None]
    y: list[Finite | None]
    coordinate_unit: Literal["m", "source_units"] = "m"
    coordinate_note: str | None = None


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
    speed_class: Literal["low", "medium", "high", "mixed", "unknown"] | None
    label: str
    start_m: Nonnegative
    end_m: Nonnegative
    gain_ms: Finite | None
    gain_sensitivity_ms: GainSensitivity | None
    quality_status: QualityStatus
    evidence_ids: list[Identifier]

    @model_validator(mode="after")
    def require_class_for_corner(self) -> Self:
        if (self.kind == "straight") != (self.speed_class is None):
            raise ValueError("only corner and complex segments carry a speed class")
        return self


class CornerMarker(Contract):
    marker_id: Identifier
    number: Annotated[int, Field(ge=1)]
    label: ShortText
    distance_m: Nonnegative
    segment_id: Identifier
    reference_speed_kph: Nonnegative | None
    speed_class: Literal["low", "medium", "high", "unknown"]

    @model_validator(mode="after")
    def require_reference(self) -> Self:
        if self.speed_class != "unknown" and self.reference_speed_kph is None:
            raise ValueError("a classified marker requires its frozen reference speed")
        return self


class EstimatedMiniSector(Contract):
    source: Literal["derived_telemetry"]
    start_m: Nonnegative
    end_m: Nonnegative
    gain_ms: Finite | None


class CornerClassSummary(Contract):
    speed_class: SpeedClass
    included_segment_ids: list[Identifier]
    excluded_segment_ids: list[Identifier]
    independent_units: Count
    distance_coverage: Annotated[Finite, Field(ge=0, le=1)]
    gains_a_ms: Nonnegative | None
    gains_b_ms: Nonnegative | None
    net_gain_ms: Finite | None
    a_wins: Count
    b_wins: Count
    neutral_units: Count
    sensitivity: GainSensitivity | None
    assessment: Literal["insufficient", "mixed", "balanced", "a_advantage", "b_advantage"]
    evidence_ids: list[Identifier]


class AnalysisSummary(Contract):
    categories: Annotated[list[CornerClassSummary], Field(min_length=3, max_length=3)]
    classification_rule: Literal["reference_apex_minimum_v1"]
    medium_from_kph: Nonnegative
    high_from_kph: Nonnegative
    pattern: Literal["high_medium_gain_low_loss", "mixed", "insufficient"]
    pattern_driver: DriverSlot | None
    text: ShortText
    evidence_ids: list[Identifier]
    limitations: list[ShortText]

    @model_validator(mode="after")
    def validate_pattern(self) -> Self:
        if self.medium_from_kph >= self.high_from_kph:
            raise ValueError("speed class thresholds must be increasing")
        if {item.speed_class for item in self.categories} != {"low", "medium", "high"}:
            raise ValueError("include one summary for each speed class")
        if self.pattern == "high_medium_gain_low_loss":
            if self.pattern_driver is None or not self.evidence_ids:
                raise ValueError("a category pattern requires a driver and evidence")
            for item in self.categories:
                favour_a = (self.pattern_driver == "A") == (item.speed_class != "low")
                expected = "a_advantage" if favour_a else "b_advantage"
                opposing = item.b_wins if favour_a else item.a_wins
                if item.assessment != expected or item.distance_coverage != 1 or opposing:
                    raise ValueError("category pattern requires consistent, fully supported classes")
        elif self.pattern_driver is not None:
            raise ValueError("only a directional category pattern names a driver")
        return self


class Observation(Contract):
    observation_id: Identifier
    template_id: Literal["segment_gain", "speed_pattern", "control_pattern"]
    segment_id: Identifier
    text: Annotated[str, Field(min_length=1, max_length=600)]
    evidence_ids: Annotated[list[Identifier], Field(min_length=1)]


class ComparisonArtifact(ArtifactHeader):
    detail_level: Literal["telemetry"]
    provenance: Provenance
    distance_m: Annotated[list[Nonnegative], Field(min_length=2, max_length=5000)]
    channels_a: DriverChannels
    channels_b: DriverChannels
    channel_provenance_a: ChannelProvenanceSet
    channel_provenance_b: ChannelProvenanceSet
    geometry: TrackGeometry
    delta_ms: list[Finite | None]
    valid: list[StrictBool]
    sector_boundaries_m: tuple[Nonnegative, Nonnegative]
    quality: QualityReport
    segments: list[Segment]
    corners: list[CornerMarker]
    estimated_minisectors: list[EstimatedMiniSector]
    analysis: AnalysisSummary
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
        native_fields = {
            "speed_kph": {"Speed"} if self.provenance.source == "fastf1" else {"speed"},
            "throttle_pct": {"Throttle"} if self.provenance.source == "fastf1" else {"throttle"},
            "gear": {"nGear"} if self.provenance.source == "fastf1" else {"n_gear"},
            "brake": {"Brake"} if self.provenance.source == "fastf1" else {"brake"},
        }
        for channels, provenance in ((self.channels_a, self.channel_provenance_a),
                                     (self.channels_b, self.channel_provenance_b)):
            for name, recognized_fields in native_fields.items():
                signal = getattr(provenance, name)
                values = getattr(channels, name)
                has_data = any(value is not None for value in values)
                if signal.status == "missing" and has_data:
                    raise ValueError("missing channels must contain only null samples")
                if signal.status == "measured" and (not has_data or signal.source_channel not in recognized_fields):
                    raise ValueError("measured signals require supported samples from a recognized native channel")
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
            channel = {
                "minimum_speed": "speed_kph", "entry_speed": "speed_kph", "exit_speed": "speed_kph",
                "brake_onset": "brake", "throttle_pickup": "throttle_pct",
                "full_throttle_fraction": "throttle_pct", "gear_at_marker": "gear",
            }.get(evidence.metric)
            if channel:
                for provenance, channels, value, interval, native_samples in (
                    (self.channel_provenance_a, self.channels_a, evidence.value_a,
                     evidence.interval_a, evidence.native_samples_a),
                    (self.channel_provenance_b, self.channels_b, evidence.value_b,
                     evidence.interval_b, evidence.native_samples_b),
                ):
                    if value is None and interval is None:
                        continue
                    if getattr(provenance, channel).status != "measured":
                        raise ValueError("channel evidence requires that driver's measured source signal")
                    if native_samples == 0:
                        raise ValueError("channel evidence requires positive native sample support")
                    values = getattr(channels, channel)
                    first = bisect_left(grid, evidence.start_m)
                    after = bisect_right(grid, evidence.end_m)
                    # Display support is only a consistency check; native counts
                    # must still come from the original source observations.
                    if first < after:
                        local_support = any(value is not None for value in values[first:after])
                    else:
                        # A narrow window may lie between display-grid samples.
                        local_support = (0 < first < size and values[first - 1] is not None
                                         and values[first] is not None)
                    if not local_support:
                        raise ValueError("channel evidence requires local display support within or bracketing its window")
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
        self.validate_track_details(grid_indices)
        return self

    def validate_track_details(self, grid_indices: dict[float, int]) -> None:
        segments = {segment.segment_id: segment for segment in self.segments}
        ids = [marker.marker_id for marker in self.corners]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate turn marker")
        if any(b.distance_m < a.distance_m for a, b in zip(self.corners, self.corners[1:])):
            raise ValueError("turn markers must follow track distance order")
        marker_classes: dict[str, set[str]] = {}
        for marker in self.corners:
            segment = segments.get(marker.segment_id)
            if segment is None or segment.kind == "straight" or not segment.start_m <= marker.distance_m <= segment.end_m:
                raise ValueError("turn marker must belong to its corner segment")
            marker_classes.setdefault(segment.group_id or segment.segment_id, set()).add(marker.speed_class)
            if marker.speed_class != "unknown":
                speed = marker.reference_speed_kph
                expected = "low" if speed < self.analysis.medium_from_kph else "medium" if speed < self.analysis.high_from_kph else "high"
                if marker.speed_class != expected:
                    raise ValueError("marker class must match the configured reference-speed bands")
        for segment in self.segments:
            if segment.kind == "straight" or segment.speed_class == "unknown":
                continue
            classes = marker_classes.get(segment.group_id or segment.segment_id, set())
            if not classes or "unknown" in classes:
                raise ValueError("classified corner segments require reviewed reference markers")
            expected = "mixed" if len(classes) > 1 else next(iter(classes))
            if segment.speed_class != expected:
                raise ValueError("corner segment class disagrees with its constituent markers")
        previous = 0.0
        for section in self.estimated_minisectors:
            expected_end = min(previous + 100.0, self.distance_m[-1])
            if section.start_m != previous or section.end_m != expected_end or section.end_m <= previous:
                raise ValueError("estimated minisectors must partition the lap into consecutive 100 m bins")
            if section.start_m not in grid_indices or section.end_m not in grid_indices:
                raise ValueError("minisector bounds must be present on the shared grid")
            i, j = grid_indices[section.start_m], grid_indices[section.end_m]
            if section.gain_ms is not None:
                if not all(self.valid[i:j + 1]) or not isclose(section.gain_ms, self.delta_ms[j] - self.delta_ms[i], abs_tol=1e-6):
                    raise ValueError("minisector gain requires supported endpoint delta arithmetic")
            previous = section.end_m
        if self.quality.status != "block" and previous != self.distance_m[-1]:
            raise ValueError("minisectors must reach the finish")
        evidence_ids = {item.evidence_id for item in self.evidence}
        if not set(self.analysis.evidence_ids).issubset(evidence_ids):
            raise ValueError("analysis references unknown evidence")
        for row in self.analysis.categories:
            self.validate_class_summary(row, segments, evidence_ids)

    def validate_class_summary(self, row: CornerClassSummary, segments: dict[str, Segment], evidence_ids: set[str]) -> None:
        classified = {key for key, segment in segments.items() if segment.speed_class == row.speed_class}
        ids = row.included_segment_ids + row.excluded_segment_ids
        if len(set(ids)) != len(ids) or set(ids) != classified:
            raise ValueError("category coverage must account for every classified segment once")
        selected = [segments[key] for key in row.included_segment_ids]
        if any(item.gain_ms is None or item.gain_sensitivity_ms is None or item.quality_status == "block" for item in selected):
            raise ValueError("included class segment requires supported gain and sensitivity")
        units = {item.group_id or item.segment_id for item in selected}
        if any((segments[key].group_id or key) in units for key in row.excluded_segment_ids):
            raise ValueError("all pieces of a linked unit must share coverage")
        if row.independent_units != len(units) or row.a_wins + row.b_wins + row.neutral_units != len(units):
            raise ValueError("category counts must match independent units")
        if not set(row.evidence_ids).issubset(evidence_ids):
            raise ValueError("category references unknown evidence")
        expected_length = sum(segments[key].end_m - segments[key].start_m for key in classified)
        covered = sum(item.end_m - item.start_m for item in selected)
        coverage = covered / expected_length if expected_length else 0.0
        if not isclose(coverage, row.distance_coverage, abs_tol=1e-6):
            raise ValueError("category coverage must be distance weighted")
        totals = (row.gains_a_ms, row.gains_b_ms, row.net_gain_ms)
        if not selected:
            if totals != (None, None, None) or row.assessment != "insufficient" or row.sensitivity is not None:
                raise ValueError("missing category support requires unavailable totals")
            return
        group_gains: dict[str, float] = {}
        bounds: dict[str, tuple[float, float]] = {}
        for item in selected:
            key = item.group_id or item.segment_id
            group_gains[key] = group_gains.get(key, 0.0) + item.gain_ms
            lower, upper = bounds.get(key, (0.0, 0.0))
            bounds[key] = (lower + item.gain_sensitivity_ms.minimum_ms, upper + item.gain_sensitivity_ms.maximum_ms)
        gains_a = sum(max(value, 0.0) for value in group_gains.values())
        gains_b = sum(max(-value, 0.0) for value in group_gains.values())
        expected = (gains_a, gains_b, gains_a - gains_b)
        if any(actual is None or not isclose(actual, value, abs_tol=1e-6) for actual, value in zip(totals, expected)):
            raise ValueError("gross and net class gains must agree with the included units")
        lower = sum(interval[0] for interval in bounds.values())
        upper = sum(interval[1] for interval in bounds.values())
        if (row.sensitivity is None or not isclose(lower, row.sensitivity.minimum_ms, abs_tol=1e-6)
                or not isclose(upper, row.sensitivity.maximum_ms, abs_tol=1e-6)):
            raise ValueError("aggregate sensitivity must account for all included segments")
        a_wins = b_wins = 0
        for key, (unit_lower, unit_upper) in bounds.items():
            material = abs(group_gains[key]) >= max(30.0, 2 * (unit_upper - unit_lower))
            a_wins += int(material and unit_lower > 0)
            b_wins += int(material and unit_upper < 0)
        if row.a_wins != a_wins or row.b_wins != b_wins:
            raise ValueError("material win counts must match unit gains and sensitivity")
        if row.assessment.endswith("_advantage"):
            wins = row.a_wins if row.assessment == "a_advantage" else row.b_wins
            sign = 1 if row.assessment == "a_advantage" else -1
            if row.independent_units < 2 or coverage < 0.8 or row.sensitivity is None or not row.evidence_ids:
                raise ValueError("directional class analysis requires coverage, sensitivity and evidence")
            spread = row.sensitivity.maximum_ms - row.sensitivity.minimum_ms
            if (lower * upper <= 0 or row.net_gain_ms * sign < max(30, 2 * spread) or wins < 2
                    or wins * 3 < (row.a_wins + row.b_wins) * 2):
                raise ValueError("directional class analysis requires consistent material gains")


class SectorQuality(Contract):
    status: QualityStatus
    warnings: list[ShortText]
    checks: tuple[ReconciliationCheck, ReconciliationCheck]


class SectorComparisonArtifact(ArtifactHeader):
    detail_level: Literal["sector_only"]
    provenance: TimingProvenance
    quality: SectorQuality
    fallback_reason: ShortText
    sector_delta_ms: tuple[Finite, Finite, Finite]
    cumulative_delta_ms: tuple[Finite, Finite, Finite]

    @model_validator(mode="after")
    def validate_sectors(self) -> Self:
        by_driver = {check.driver: check for check in self.quality.checks}
        if set(by_driver) != {"A", "B"}:
            raise ValueError("sector-only quality requires one sector-sum check per lap")
        severity = {"pass": 0, "warn": 1, "block": 2}
        for driver, lap in (("A", self.lap_a), ("B", self.lap_b)):
            check = by_driver[driver]
            if check.metric != "sector_sum" or check.basis != "timing_record_consistency":
                raise ValueError("sector-only checks reconcile sector durations to recorded lap time")
            if (not isclose(check.official_ms, lap.lap_time_ms, abs_tol=1e-6) or check.observed_ms is None
                    or not isclose(check.observed_ms, sum(lap.sector_times_ms), abs_tol=1e-6)):
                raise ValueError("sector-sum check must use the selected lap and sector timings")
            if severity[check.status] > severity[self.quality.status]:
                raise ValueError("sector-only quality cannot understate a timing check")
        running = 0.0
        for a, b, delta, cumulative in zip(self.lap_a.sector_times_ms, self.lap_b.sector_times_ms,
                                           self.sector_delta_ms, self.cumulative_delta_ms):
            running += b - a
            if not isclose(b - a, delta, abs_tol=1e-6) or not isclose(running, cumulative, abs_tol=1e-6):
                raise ValueError("sector-only deltas must follow recorded sector durations")
        return self


Artifact = Annotated[ComparisonArtifact | SectorComparisonArtifact, Field(discriminator="detail_level")]


class ComparisonSummary(Contract):
    comparison_id: Identifier
    detail_level: Literal["telemetry", "sector_only"]
    session: SessionIdentity
    lap_a: LapMetadata
    lap_b: LapMetadata
    quality_status: QualityStatus


class Catalog(Contract):
    schema_version: SchemaVersion = "1.2.0"
    comparisons: list[ComparisonSummary]
