"""Only validated local artifacts are visible. No ingestion on request paths."""

import re
from pathlib import Path

from pydantic import ValidationError

from lapdna.models import Catalog, ComparisonArtifact, ComparisonSummary

MAX_ARTIFACT_BYTES = 20 * 1024 * 1024
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


class ArtifactNotFound(Exception):
    pass


class InvalidArtifact(Exception):
    pass


class QualityBlocked(Exception):
    pass


class ArtifactStore:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()

    def load(self, comparison_id: str) -> ComparisonArtifact:
        if not ID_PATTERN.fullmatch(comparison_id):
            raise ArtifactNotFound
        path = self.directory / f"{comparison_id}.json"
        # Reject links outside the configured root, even if an operator created one.
        if path.resolve().parent != self.directory:
            raise ArtifactNotFound
        try:
            if path.stat().st_size > MAX_ARTIFACT_BYTES:
                raise InvalidArtifact("artifact exceeds size limit")
            raw = path.read_bytes()
        except FileNotFoundError as exc:
            raise ArtifactNotFound from exc
        except OSError as exc:
            raise InvalidArtifact("artifact cannot be read") from exc
        try:
            artifact = ComparisonArtifact.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            raise InvalidArtifact("artifact failed schema validation") from exc
        if artifact.comparison_id != comparison_id:
            raise InvalidArtifact("artifact ID does not match its filename")
        if artifact.quality.status == "block":
            raise QualityBlocked
        return artifact

    def catalog(self) -> Catalog:
        comparisons = []
        for path in sorted(self.directory.glob("*.json")):
            # A malformed artifact is an operator error, not an empty catalogue.
            try:
                artifact = self.load(path.stem)
            except ArtifactNotFound as exc:
                raise InvalidArtifact("catalog entry is not a supported artifact") from exc
            except QualityBlocked:
                # A deliberately withheld result is not a ready comparison.
                continue
            comparisons.append(ComparisonSummary(
                comparison_id=artifact.comparison_id,
                session=artifact.session,
                lap_a=artifact.lap_a,
                lap_b=artifact.lap_b,
                quality_status=artifact.quality.status,
            ))
        return Catalog(comparisons=comparisons)
