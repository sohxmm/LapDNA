"""Bounded read-only normalized publications and a disposable process cache."""

from collections import OrderedDict
from concurrent.futures import Future, TimeoutError
import gzip
from hashlib import sha256
from itertools import combinations
import json
from io import BytesIO
from pathlib import Path
from math import isfinite
from threading import BoundedSemaphore, RLock

from lapdna.analysis.engine import build_comparison, comparison_identity, canonical_hash
from lapdna.store import ArtifactNotFound, ID_PATTERN, InvalidArtifact, MAX_ARTIFACT_BYTES
from lapdna.models import DriverChannels, LapMetadata


class ComparisonBusy(Exception):
    pass


class PilotStore:
    """The frozen publication regenerates exact results after process restarts.

    There are no source requests, session parsing or per-lap normalization on
    this path. Cache retention is an optimization, not share-link identity.
    """

    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self._publications = OrderedDict()
        self._results = OrderedDict()
        self._lock = RLock()
        self._capacity = BoundedSemaphore(2)
        self._pending = {}

    def manifests(self):
        path = self.directory / "publication.json"
        if path.resolve().parent != self.directory or path.stat().st_size > 256 * 1024:
            raise InvalidArtifact("invalid publication catalogue")
        root = json.loads(path.read_text(encoding="utf-8"))
        if root.get("catalogue_version") != 2:
            return {root["session_id"]: root}
        if len(root["sessions"]) > 500:
            raise InvalidArtifact("publication catalogue exceeds session bound")
        manifests = {}
        for identifier, entry in root["sessions"].items():
            if not ID_PATTERN.fullmatch(identifier):
                raise InvalidArtifact("invalid publication session ID")
            manifest_path = self.directory / entry["manifest"]
            if manifest_path.resolve().parent != (self.directory / "manifests").resolve() or not manifest_path.resolve().is_relative_to(self.directory):
                raise InvalidArtifact("publication manifest escaped root")
            if manifest_path.stat().st_size > 256 * 1024:
                raise InvalidArtifact("publication manifest exceeds size limit")
            raw = manifest_path.read_bytes()
            if sha256(raw).hexdigest() != entry["sha256"]:
                raise InvalidArtifact("publication manifest digest mismatch")
            manifest = json.loads(raw)
            if manifest["session_id"] != identifier:
                raise InvalidArtifact("publication manifest session mismatch")
            manifests[identifier] = manifest
        return manifests

    def load(self, session_id: str):
        if not ID_PATTERN.fullmatch(session_id):
            raise ArtifactNotFound
        with self._lock:
            manifest_path = self.directory / "publication.json"
            try:
                if manifest_path.resolve().parent != self.directory:
                    raise InvalidArtifact("publication manifest escaped root")
                if manifest_path.stat().st_size > 256 * 1024:
                    raise InvalidArtifact("publication manifest exceeds size limit")
                manifest = self.manifests().get(session_id)
                if manifest is None:
                    raise ArtifactNotFound
                cached = self._publications.get(session_id)
                if cached is not None and cached["publication_sha256"] == manifest["publication_sha256"]:
                    self._publications.move_to_end(session_id)
                    return cached
                relative = manifest.get("normalized", f"normalized/{session_id}.json.gz")
                path = self.directory / relative
                if not path.resolve().is_relative_to(self.directory) or path.resolve().parent != (self.directory / "normalized").resolve():
                    raise InvalidArtifact("normalized publication path escaped root")
                if path.stat().st_size > MAX_ARTIFACT_BYTES:
                    raise InvalidArtifact("compressed publication exceeds size limit")
                compressed = path.read_bytes()
                if sha256(compressed).hexdigest() != manifest["files"][relative]:
                    raise InvalidArtifact("normalized publication digest mismatch")
                with gzip.GzipFile(fileobj=BytesIO(compressed), mode="rb") as handle:
                    raw = handle.read(MAX_ARTIFACT_BYTES + 1)
                if len(raw) > MAX_ARTIFACT_BYTES:
                    raise InvalidArtifact("normalized publication exceeds decompressed size limit")
                publication = json.loads(raw)
                if (publication["session"]["session_id"] != session_id
                        or publication["publication_sha256"] != manifest["publication_sha256"]):
                    raise InvalidArtifact("normalized publication identity mismatch")
                grid = publication["distance_m"]
                if (not isinstance(grid, list) or not 2 <= len(grid) <= 5000 or grid[0] != 0
                        or any(type(value) not in (int, float) or not isfinite(value) for value in grid)
                        or any(right <= left for left, right in zip(grid, grid[1:]))):
                    raise InvalidArtifact("normalized publication distance grid is invalid")
                if not isinstance(publication["laps"], dict) or len(publication["laps"]) > 256:
                    raise InvalidArtifact("normalized publication exceeds bounded lap count")
                if len(publication["regions"]) > 128 or len(publication["corners"]) > 200:
                    raise InvalidArtifact("normalized publication exceeds bounded region count")
                if any(len(publication["geometry"][axis]) != len(grid) for axis in ("x", "y")):
                    raise InvalidArtifact("normalized publication geometry length mismatch")
                sectors = publication["sector_boundaries_m"]
                if len(sectors) != 2 or not 0 < sectors[0] < sectors[1] < grid[-1]:
                    raise InvalidArtifact("normalized publication sector boundaries are invalid")
                for identifier, record in publication["laps"].items():
                    metadata = LapMetadata.model_validate_json(json.dumps(record["metadata"]))
                    if metadata.lap_id != identifier:
                        raise InvalidArtifact("normalized lap key disagrees with its identity")
                    if "channels" in record:
                        channels = DriverChannels.model_validate_json(json.dumps(record["channels"]))
                        if any(len(getattr(channels, field)) != len(grid) for field in type(channels).model_fields):
                            raise InvalidArtifact("normalized channel lengths disagree with distance grid")
            except FileNotFoundError as exc:
                raise ArtifactNotFound from exc
            except (OSError, KeyError, ValueError, TypeError) as exc:
                raise InvalidArtifact("invalid normalized publication") from exc
            self._publications[session_id] = publication
            while len(self._publications) > 3:
                self._publications.popitem(last=False)
            return publication

    def compare(self, session_id, lap_a, lap_b, detail_level):
        publication = self.load(session_id)
        if lap_a not in publication["laps"] or lap_b not in publication["laps"]:
            raise InvalidArtifact("lap index and normalized publication disagree")
        key = (publication["publication_sha256"], *sorted((lap_a, lap_b)), detail_level)
        with self._lock:
            if key in self._results:
                self._results.move_to_end(key)
                return self._results[key]
            pending = self._pending.get(key)
            owner = pending is None
            if owner:
                if not self._capacity.acquire(blocking=False):
                    raise ComparisonBusy
                pending = Future()
                self._pending[key] = pending
        if not owner:
            try:
                return pending.result(timeout=5)
            except TimeoutError as exc:
                raise ComparisonBusy from exc
        try:
            result = build_comparison(publication, lap_a, lap_b, detail_level)
            with self._lock:
                self._results[key] = result
                while len(self._results) > 48:
                    self._results.popitem(last=False)
            pending.set_result(result)
            return result
        except BaseException as exc:
            pending.set_exception(exc)
            raise
        finally:
            with self._lock:
                self._pending.pop(key, None)
            self._capacity.release()

    def resolve(self, comparison_id):
        # Only candidate IDs are enumerated, not pair calculations. The pilot
        # has fewer than 100 timing-eligible laps; no Cartesian artifacts exist.
        with self._lock:
            for result in self._results.values():
                if result.comparison_id == comparison_id:
                    return result
        try:
            manifests = self.manifests()
        except (FileNotFoundError, KeyError, ValueError):
            raise ArtifactNotFound
        # Session tag prevents an archive-wide Cartesian search or bulk load.
        for session_id in manifests:
            if not comparison_id.startswith("cmp_" + canonical_hash(session_id)[:8] + "_"):
                continue
            publication = self.load(session_id)
            candidates = sorted(publication["laps"])
            if len(candidates) > 256:
                raise InvalidArtifact("identity resolver exceeds bounded lap count")
            for a, b in combinations(candidates, 2):
                if publication["laps"][a]["metadata"]["driver_number"] == publication["laps"][b]["metadata"]["driver_number"]:
                    continue
                for tier in ("telemetry", "sector_only"):
                    if comparison_identity(publication, a, b, tier) == comparison_id:
                        result = self.compare(session_id, a, b, tier)
                        if result.comparison_id == comparison_id:
                            return result
        raise ArtifactNotFound
