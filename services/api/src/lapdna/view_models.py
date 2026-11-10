"""Opt-in v6 view contracts. Legacy v5 models/serializers remain unchanged."""
from typing import Annotated, Literal, Self

from pydantic import Field, StrictBool, model_validator

from lapdna.models import (ComparisonArtifact, Contract, Finite, Identifier,
    LapMetadata, Nonnegative, SessionIdentity, Sha256, ShortText, TimingProvenance)

ViewTier = Literal["telemetry_view", "aligned_delta", "analysis"]
Channel = Literal["speed_kph", "throttle_pct", "rpm", "gear", "brake"]
CHANNELS = ("speed_kph", "throttle_pct", "rpm", "gear", "brake")


class ViewCompareRequest(Contract):
    session_id: Identifier
    lap_a_id: Identifier
    lap_b_id: Identifier
    allow_cross_phase: bool = False
    requested_tier: ViewTier = "aligned_delta"


class ChannelSpan(Contract):
    channel: Channel
    start_elapsed_ms: Nonnegative
    end_elapsed_ms: Nonnegative
    state: Literal["bridged", "gap"]
    render_hint: Literal["dashed_connector", "hatched_no_data", "blank_gap"]
    reason: ShortText

    @model_validator(mode="after")
    def valid_span(self) -> Self:
        if self.end_elapsed_ms <= self.start_elapsed_ms:
            raise ValueError("span must have positive duration")
        if self.channel in ("gear", "brake") and (self.state != "gap" or self.render_hint != "hatched_no_data"):
            raise ValueError("discrete channel gaps cannot be bridged or held")
        return self


class NativeChannels(Contract):
    speed_kph: list[Nonnegative | None]
    throttle_pct: list[Annotated[Finite, Field(ge=0, le=100)] | None]
    rpm: list[Nonnegative | None]
    gear: list[Annotated[int, Field(strict=True, ge=0, le=8)] | None]
    brake: list[StrictBool | None]


class NativeLapView(Contract):
    metadata: LapMetadata
    source_duration_ms: Annotated[Finite, Field(gt=0)]
    elapsed_ms: list[Finite]  # Real padding samples can lie outside lap edges.
    channels: NativeChannels
    sample_masks: dict[Channel, list[Literal["measured", "gap"]]]
    interpolation: dict[Channel, Literal["linear_connector", "none"]]
    spans: list[ChannelSpan]
    warnings: list[ShortText]

    @model_validator(mode="after")
    def native_integrity(self) -> Self:
        t = self.elapsed_ms
        if len(t) < 2 or t[0] > 0 or t[-1] < self.source_duration_ms or any(b <= a for a, b in zip(t, t[1:])):
            raise ValueError("native samples must increase and bracket both timing edges")
        if set(self.sample_masks) != set(CHANNELS) or set(self.interpolation) != set(CHANNELS):
            raise ValueError("every channel requires explicit mask/interpolation semantics")
        for name in CHANNELS:
            values = getattr(self.channels, name)
            if len(values) != len(t) or len(self.sample_masks[name]) != len(t):
                raise ValueError("native channel/mask lengths must match source timestamps")
            if any((v is None) != (mask == "gap") for v, mask in zip(values, self.sample_masks[name])):
                raise ValueError("null values must have gap masks; zero is measured")
            if name in ("gear", "brake") and self.interpolation[name] != "none":
                raise ValueError("gear/brake may not be interpolated or forward-filled")
        if any(s.end_elapsed_ms > self.source_duration_ms for s in self.spans):
            raise ValueError("display gap masks must stay within lap timing edges")
        return self


class SpeedBridge(Contract):
    start_elapsed_ms: Nonnegative
    end_elapsed_ms: Nonnegative
    native_interval_ms: Nonnegative
    speed_before_kph: Nonnegative
    speed_after_kph: Nonnegative
    full_interval_bound_m: Nonnegative
    in_lap_bound_m: Nonnegative
    excluded_from_analysis: Literal[True] = True


class SectorAnnotation(Contract):
    sector: Literal[1, 2]
    official_elapsed_ms: Nonnegative
    estimated_elapsed_ms: Nonnegative
    residual_ms: Finite
    grade: Literal["C", "ungraded"]
    basis: Literal["reference_timing_constraint", "shared_progress_estimate"]


class AlignedLap(Contract):
    elapsed_ms: list[Nonnegative]
    distance_m: list[Nonnegative]
    cumulative_bound_m: list[Nonnegative]
    distance_lower_m: list[Nonnegative]
    distance_upper_m: list[Nonnegative]
    integrated_length_m: Annotated[Finite, Field(gt=0)]
    scale_factor: Annotated[Finite, Field(gt=0)]
    source_duration_ms: Annotated[Finite, Field(gt=0)]
    endpoint_residual_ms: Finite
    bridges: list[SpeedBridge]
    sector_annotations: list[SectorAnnotation]

    @model_validator(mode="after")
    def bounded_progress(self) -> Self:
        n = len(self.elapsed_ms)
        if n < 2 or any(len(getattr(self, key)) != n for key in ("distance_m", "cumulative_bound_m", "distance_lower_m", "distance_upper_m")):
            raise ValueError("progress and bound lengths must agree")
        if self.elapsed_ms[0] != 0 or self.elapsed_ms[-1] != self.source_duration_ms or any(b <= a for a, b in zip(self.elapsed_ms, self.elapsed_ms[1:])):
            raise ValueError("elapsed endpoints must be the unrescaled source timing edges")
        if self.distance_m[0] != 0 or any(b <= a for a, b in zip(self.distance_m, self.distance_m[1:])):
            raise ValueError("nominal distance must increase")
        if self.cumulative_bound_m[0] != 0 or any(b < a for a, b in zip(self.cumulative_bound_m, self.cumulative_bound_m[1:])):
            raise ValueError("raw cumulative gap bound must accumulate, not reset at finish")
        if any(not lo <= x <= hi for lo, x, hi in zip(self.distance_lower_m, self.distance_m, self.distance_upper_m)):
            raise ValueError("distance band must contain nominal progress")
        return self


class ViewReference(Contract):
    lap_id: Identifier
    length_m: Annotated[Finite, Field(gt=0)]
    sha256: Sha256
    selection_basis: Literal["legacy_v5", "speed_only"]
    geometry_available: bool
    markers_available: bool


class AlignedDelta(Contract):
    reference: ViewReference
    distance_m: list[Nonnegative]
    elapsed_a_ms: list[Nonnegative]
    elapsed_b_ms: list[Nonnegative]
    delta_ms: list[Finite]
    delta_lower_ms: list[Finite]
    delta_upper_ms: list[Finite]
    lap_a: AlignedLap
    lap_b: AlignedLap
    recorded_lap_gap_ms: Finite
    quality_grade: Literal["C", "ungraded"]
    bound_model: Literal["linear_endpoint_speed_v1"] = "linear_endpoint_speed_v1"
    warnings: list[ShortText]

    @model_validator(mode="after")
    def aligned_integrity(self) -> Self:
        n = len(self.distance_m)
        if n < 2 or any(len(getattr(self, key)) != n for key in ("elapsed_a_ms", "elapsed_b_ms", "delta_ms", "delta_lower_ms", "delta_upper_ms")):
            raise ValueError("aligned grid lengths disagree")
        if self.distance_m[0] != 0 or self.distance_m[-1] != self.reference.length_m or any(b <= a for a, b in zip(self.distance_m, self.distance_m[1:])):
            raise ValueError("distance grid must span the frozen reference")
        if any(not lo <= d <= hi for lo, d, hi in zip(self.delta_lower_ms, self.delta_ms, self.delta_upper_ms)):
            raise ValueError("delta uncertainty band must contain nominal delta")
        if any(abs(d - (b - a)) > 1e-7 for a, b, d in zip(self.elapsed_a_ms, self.elapsed_b_ms, self.delta_ms)):
            raise ValueError("delta must be B minus A")
        return self


class ViewArtifact(Contract):
    schema_version: Literal["2.0.0"] = "2.0.0"
    comparison_id: Identifier
    detail_level: Literal["telemetry"] = "telemetry"
    requested_tier: ViewTier
    view_tier: ViewTier
    methodology_version: Literal["distance-v6-fastf1-native", "distance-v6-openf1-native-composite"]
    session: SessionIdentity
    provenance: TimingProvenance
    lap_a: NativeLapView
    lap_b: NativeLapView
    alignment: AlignedDelta | None
    legacy_analysis: ComparisonArtifact | None
    unavailable_reasons: dict[str, list[ShortText]]
    warnings: list[ShortText]

    @model_validator(mode="after")
    def tier_integrity(self) -> Self:
        if self.view_tier == "telemetry_view" and (self.alignment is not None or self.legacy_analysis is not None):
            raise ValueError("Tier 0 cannot contain delta/analysis claims")
        if self.view_tier != "telemetry_view" and self.alignment is None:
            raise ValueError("Tier 1/2 require an aligned delta")
        if (self.view_tier == "analysis") != (self.legacy_analysis is not None):
            raise ValueError("Tier 2 must carry the unchanged accepted legacy analysis")
        if self.provenance.methodology_version != self.methodology_version:
            raise ValueError("method identity must agree with provenance")
        return self


class ViewCompareResponse(Contract):
    artifact: ViewArtifact
    swapped: bool
