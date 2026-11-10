"""Bounded local v6 publications. Raw source parsing stays offline."""
from collections import OrderedDict
import gzip
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from threading import BoundedSemaphore, RLock

from lapdna.analysis.engine import canonical_hash
from lapdna.analysis.views import build_view
from lapdna.inventory import SelectionError
from lapdna.store import ID_PATTERN, InvalidArtifact
from lapdna.view_models import ViewCompareResponse


class ViewStore:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.cache = OrderedDict()
        self.lock = RLock()
        self.capacity = BoundedSemaphore(2)

    def load(self, session_id):
        if not ID_PATTERN.fullmatch(session_id):
            raise SelectionError(404, "session_not_found", "Unknown session.")
        path = self.directory / "publication.json"
        if not path.is_file():
            raise SelectionError(409, "view_not_prepared", "This opt-in v6 view has not been prepared.")
        if path.stat().st_size > 256 * 1024:
            raise InvalidArtifact("View catalogue exceeds size bound")
        root = json.loads(path.read_bytes())
        entry = root["sessions"].get(session_id)
        if entry is None:
            raise SelectionError(409, "view_not_prepared", "This session has no prepared v6 views.")
        with self.lock:
            key = (session_id, entry["sha256"])
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            blob = self.directory / entry["path"]
            if not blob.resolve().is_relative_to(self.directory) or blob.stat().st_size > 32 * 1024 * 1024:
                raise InvalidArtifact("Invalid view publication path/size")
            compressed = blob.read_bytes()
            if sha256(compressed).hexdigest() != entry["sha256"]:
                raise InvalidArtifact("View publication digest mismatch")
            with gzip.GzipFile(fileobj=BytesIO(compressed)) as handle:
                raw = handle.read(64 * 1024 * 1024 + 1)
            if len(raw) > 64 * 1024 * 1024:
                raise InvalidArtifact("View publication decompression bound exceeded")
            publication = json.loads(raw)
            digest = publication.pop("publication_sha256")
            if digest != canonical_hash(publication) or publication["session"]["session_id"] != session_id or len(publication["laps"]) > 512:
                raise InvalidArtifact("View publication identity mismatch")
            publication["publication_sha256"] = digest
            self.cache[key] = publication
            while len(self.cache) > 2:
                self.cache.popitem(last=False)
            return publication

    def compare(self, request, legacy_store=None):
        from lapdna.analysis.store import ComparisonBusy
        if not self.capacity.acquire(blocking=False):
            raise ComparisonBusy
        try:
            return self._compare(request, legacy_store)
        finally:
            self.capacity.release()

    def _compare(self, request, legacy_store):
        publication = self.load(request.session_id)
        a, b = request.lap_a_id, request.lap_b_id
        for identifier in (a, b):
            if identifier in publication["failures"]:
                raise SelectionError(422, "telemetry_view_unavailable", publication["failures"][identifier]["reason"])
            if identifier not in publication["laps"]:
                raise SelectionError(404, "lap_not_found", "A selected timing-eligible lap is absent from this publication.")
        ma, mb = (publication["laps"][identifier]["metadata"] for identifier in (a, b))
        # Selection changes are explicitly deferred to Step 5.
        if ma["driver_number"] == mb["driver_number"]:
            raise SelectionError(422, "same_driver", "Choose two different drivers.")
        if ma["phase"] != mb["phase"] and not request.allow_cross_phase:
            raise SelectionError(422, "cross_phase_not_enabled", "Enable cross-phase comparison for these laps.")
        legacy_analysis = None
        if request.requested_tier == "analysis" and legacy_store is not None:
            from lapdna.analysis.engine import ComparisonUnavailable
            from lapdna.store import ArtifactNotFound
            if legacy_store.load(request.session_id)["publication_sha256"] != publication["legacy_publication_sha256"]:
                raise InvalidArtifact("Legacy and view publications disagree")
            try:
                candidate = legacy_store.compare(request.session_id, a, b, "telemetry")
                if candidate.detail_level == "telemetry":
                    legacy_analysis = candidate
            except (ComparisonUnavailable, ArtifactNotFound):
                pass
        artifact = build_view(publication, a, b, request.requested_tier, legacy_analysis)
        return ViewCompareResponse(artifact=artifact, swapped=artifact.lap_a.metadata.lap_id != a)
