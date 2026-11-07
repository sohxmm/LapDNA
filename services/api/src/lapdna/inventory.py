"""Session selection contracts and bounded lookup against local prepared data."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, ValidationError, model_validator

from lapdna.models import (
    Artifact, Contract, Count, Identifier, LapIdentity, Nonnegative,
    SchemaVersion, SessionIdentity, Sha256, ShortText,
)
from lapdna.store import ArtifactNotFound, ArtifactStore, InvalidArtifact, read_local_json


class DriverEntry(Contract):
    driver_number: Annotated[str, Field(pattern=r"^[0-9]{1,3}$")]
    driver_code: Annotated[str, Field(pattern=r"^[A-Z0-9]{2,4}$")]
    driver_name: ShortText
    team_name: ShortText | None = None


class LapOption(LapIdentity):
    lap_time_ms: Nonnegative | None
    sector_times_ms: tuple[Nonnegative | None, Nonnegative | None, Nonnegative | None]
    capability: Literal["telemetry", "sector_only", "unavailable"]
    reasons: list[ShortText]
    compound: str | None = None
    tyre_life_laps: Nonnegative | None = None
    lap_start_utc: str | None = None

    @model_validator(mode="after")
    def check_capability(self) -> Self:
        if self.capability != "unavailable" and (
            not self.lap_time_ms or any(value is None or value <= 0 for value in self.sector_times_ms)
        ):
            raise ValueError("selectable laps require complete positive recorded timing")
        if self.capability != "telemetry" and not self.reasons:
            raise ValueError("reduced availability requires a reason")
        return self


class SessionLapIndex(Contract):
    schema_version: SchemaVersion = "1.2.0"
    session: SessionIdentity
    source_snapshot_sha256: Sha256
    drivers: list[DriverEntry]
    laps: list[LapOption]
    source_name: str | None = None
    source_url: str | None = None
    data_points: list[ShortText] = []
    warnings: list[ShortText] = []

    @model_validator(mode="after")
    def check_identity(self) -> Self:
        drivers = {driver.driver_number: driver for driver in self.drivers}
        if len(drivers) != len(self.drivers) or len({lap.lap_id for lap in self.laps}) != len(self.laps):
            raise ValueError("duplicate driver or lap ID")
        for lap in self.laps:
            driver = drivers.get(lap.driver_number)
            if driver is None or (driver.driver_code, driver.driver_name) != (lap.driver_code, lap.driver_name):
                raise ValueError("lap driver must match the session roster")
        return self


class SessionSummary(Contract):
    session: SessionIdentity
    driver_count: Count
    selectable_lap_count: Count


class SessionInventory(Contract):
    schema_version: SchemaVersion = "1.2.0"
    sessions: list[SessionSummary]


class CompareRequest(Contract):
    session_id: Identifier
    lap_a_id: Identifier
    lap_b_id: Identifier
    allow_cross_phase: bool = False
    detail_level: Literal["auto", "telemetry", "sector_only"] = "auto"


class CompareResponse(Contract):
    artifact: Artifact
    swapped: bool


class SelectionError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


class SessionStore:
    def __init__(self, directory: Path, engine=None):
        self.directory = directory.resolve()
        self.engine = engine

    def load(self, session_id: str) -> SessionLapIndex:
        raw = read_local_json(self.directory, session_id)
        try:
            index = SessionLapIndex.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            raise InvalidArtifact("invalid session lap index") from exc
        if index.session.session_id != session_id:
            raise InvalidArtifact("session ID does not match filename")
        return index

    def inventory(self) -> SessionInventory:
        sessions = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                index = self.load(path.stem)
            except ArtifactNotFound as exc:
                raise InvalidArtifact("invalid session index entry") from exc
            sessions.append(SessionSummary(
                session=index.session, driver_count=len(index.drivers),
                selectable_lap_count=sum(lap.capability != "unavailable" for lap in index.laps),
            ))
        return SessionInventory(sessions=sessions)

    def compare(self, request: CompareRequest, artifacts: ArtifactStore) -> CompareResponse:
        try:
            index = self.load(request.session_id)
        except ArtifactNotFound as exc:
            raise SelectionError(409, "data_not_imported", "Import this qualifying session first.") from exc
        options = {lap.lap_id: lap for lap in index.laps}
        try:
            a, b = options[request.lap_a_id], options[request.lap_b_id]
        except KeyError as exc:
            raise SelectionError(404, "lap_not_found", "A selected lap is absent from this session.") from exc
        if a.driver_number == b.driver_number:
            raise SelectionError(422, "same_driver", "Choose two different drivers.")
        if a.phase != b.phase and not request.allow_cross_phase:
            raise SelectionError(422, "cross_phase_not_enabled", "Enable cross-phase comparison for these laps.")
        if "unavailable" in (a.capability, b.capability):
            raise SelectionError(422, "lap_unavailable", "A selected lap failed eligibility checks.")

        supports_telemetry = a.capability == b.capability == "telemetry"
        if request.detail_level == "telemetry" and not supports_telemetry:
            raise SelectionError(422, "telemetry_unavailable", "Use sector timing for these laps.")
        allowed = {"sector_only"}
        if supports_telemetry:
            allowed.add("telemetry")
        if request.detail_level != "auto":
            allowed = {request.detail_level}
        # Once normalized session data is available T05 can compute cache misses here.
        # The scaffold validates both the inventory and prepared result before use.
        candidates = []
        for artifact in artifacts.iter_ready():
            if artifact.session != index.session or artifact.detail_level not in allowed:
                continue
            if {artifact.lap_a.lap_id, artifact.lap_b.lap_id} != {a.lap_id, b.lap_id}:
                continue
            if artifact.provenance.source_snapshot_sha256 != index.source_snapshot_sha256:
                continue
            for lap in (artifact.lap_a, artifact.lap_b):
                option = options[lap.lap_id]
                if (lap.driver_number, lap.driver_code, lap.driver_name, lap.phase, lap.lap_number,
                    lap.lap_time_ms, lap.sector_times_ms) != (
                    option.driver_number, option.driver_code, option.driver_name, option.phase,
                    option.lap_number, option.lap_time_ms, option.sector_times_ms,
                ):
                    raise InvalidArtifact("cached lap disagrees with imported inventory")
            candidates.append(artifact)
        if not candidates:
            if self.engine is not None:
                from lapdna.analysis.engine import ComparisonUnavailable
                from lapdna.analysis.store import ComparisonBusy
                try:
                    chosen = self.engine.compare(request.session_id, a.lap_id, b.lap_id, request.detail_level)
                except ArtifactNotFound as exc:
                    raise SelectionError(409, "comparison_not_prepared", "This session has no normalized local publication.") from exc
                except ComparisonBusy as exc:
                    raise SelectionError(503, "comparison_busy", "Comparison capacity is busy. Retry this selection shortly.") from exc
                except ComparisonUnavailable as exc:
                    raise SelectionError(422, "telemetry_quality_blocked", str(exc)) from exc
                except (ValidationError, KeyError, TypeError, ValueError) as exc:
                    raise InvalidArtifact("computed comparison failed dataset validation") from exc
                if chosen.provenance.source_snapshot_sha256 != index.source_snapshot_sha256:
                    raise InvalidArtifact("normalized publication disagrees with session snapshot")
                for lap in (chosen.lap_a, chosen.lap_b):
                    option = options.get(lap.lap_id)
                    if option is None or (lap.driver_number, lap.driver_code, lap.driver_name, lap.phase,
                                          lap.lap_number, lap.lap_time_ms, lap.sector_times_ms) != (
                            option.driver_number, option.driver_code, option.driver_name, option.phase,
                            option.lap_number, option.lap_time_ms, option.sector_times_ms):
                        raise InvalidArtifact("normalized lap disagrees with imported inventory")
                return CompareResponse(artifact=chosen, swapped=chosen.lap_a.lap_id != a.lap_id)
            raise SelectionError(409, "comparison_not_prepared", "This lap pair has no prepared result yet.")
        chosen = max(candidates, key=lambda item: (
            item.detail_level == "telemetry", item.provenance.generated_at, item.comparison_id,
        ))
        return CompareResponse(artifact=chosen, swapped=chosen.lap_a.lap_id != a.lap_id)
