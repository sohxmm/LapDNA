"""Only validated local artifacts are visible. No ingestion on request paths."""

import re
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from lapdna.models import Artifact, Catalog, ComparisonSummary

ARTIFACT_ADAPTER = TypeAdapter(Artifact)

MAX_ARTIFACT_BYTES = 20 * 1024 * 1024
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


class ArtifactNotFound(Exception):
    pass


class InvalidArtifact(Exception):
    pass


class QualityBlocked(Exception):
    pass


def read_local_json(directory: Path, identifier: str) -> bytes:
    if not ID_PATTERN.fullmatch(identifier):
        raise ArtifactNotFound
    path = directory / f"{identifier}.json"
    if path.resolve().parent != directory:
        raise ArtifactNotFound
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_ARTIFACT_BYTES + 1)
    except FileNotFoundError as exc:
        raise ArtifactNotFound from exc
    except OSError as exc:
        raise InvalidArtifact("artifact cannot be read") from exc
    if len(raw) > MAX_ARTIFACT_BYTES:
        raise InvalidArtifact("artifact exceeds size limit")
    return raw


class ArtifactStore:
    def __init__(self, directory: Path, resolver=None):
        self.directory = directory.resolve()
        self.resolver = resolver

    def load(self, comparison_id: str) -> Artifact:
        try:
            raw = read_local_json(self.directory, comparison_id)
        except ArtifactNotFound:
            if self.resolver is not None and ID_PATTERN.fullmatch(comparison_id):
                return self.resolver(comparison_id)
            raise
        try:
            artifact = ARTIFACT_ADAPTER.validate_json(raw)
        except (ValidationError, ValueError) as exc:
            raise InvalidArtifact("artifact failed schema validation") from exc
        if artifact.comparison_id != comparison_id:
            raise InvalidArtifact("artifact ID does not match its filename")
        if artifact.quality.status == "block":
            raise QualityBlocked
        return artifact

    def iter_ready(self):
        for path in sorted(self.directory.glob("*.json")):
            # A malformed artifact is an operator error, not an empty catalogue.
            try:
                artifact = self.load(path.stem)
            except ArtifactNotFound as exc:
                raise InvalidArtifact("catalog entry is not a supported artifact") from exc
            except QualityBlocked:
                # A deliberately withheld result is not a ready comparison.
                continue
            yield artifact

    def catalog(self) -> Catalog:
        comparisons = []
        for artifact in self.iter_ready():
            comparisons.append(ComparisonSummary(
                comparison_id=artifact.comparison_id,
                detail_level=artifact.detail_level,
                session=artifact.session,
                lap_a=artifact.lap_a,
                lap_b=artifact.lap_b,
                quality_status=artifact.quality.status,
            ))
        return Catalog(comparisons=comparisons)
