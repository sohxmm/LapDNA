"""Tier 0/1 reference choice without markers, geometry or position coverage."""
from copy import deepcopy
import json

from lapdna.alignment.native import linear
from lapdna.alignment.view_delta import prepare_progress
from lapdna.analysis.engine import canonical_hash
from lapdna.view_models import NativeLapView


def select_speed_reference(publication, legacy=None):
    """Choose by source lap duration, driver number, lap number, then stable ID.

    Eligibility and speed support are established offline. Neither positions,
    markers nor legacy reference existence participates in candidate selection.
    """
    result = deepcopy(publication)
    if legacy is not None:
        if legacy["publication_sha256"] != publication["legacy_publication_sha256"]:
            raise ValueError("Conditions must come from the matching frozen legacy publication")
        result["conditions"] = {identifier: {"weather_context": row.get("weather_context", "unknown")}
            for identifier, row in legacy["laps"].items()}
    previous = result.get("reference")
    result["reference"] = None
    result["sector_boundaries_m"] = []
    candidates = publication["alignment_candidates"]
    if candidates:
        def order(identifier):
            meta = publication["laps"][identifier]["metadata"]
            return (meta["lap_time_ms"], int(meta["driver_number"]), meta["lap_number"], identifier)
        identifier = min(candidates, key=order)
        view = NativeLapView.model_validate_json(json.dumps(publication["laps"][identifier]))
        progress = prepare_progress(view)
        length = progress.integrated_length_m
        same_frame = previous is not None and previous["lap_id"] == identifier and previous["length_m"] == length
        result["reference"] = {"lap_id": identifier, "length_m": length,
            "selection_basis": "speed_only", "sha256": canonical_hash({
                "selection": "fastest-source-timing-speed-ready-v1", "lap_id": identifier,
                "source_snapshot_sha256": result["provenance"]["source_snapshot_sha256"],
                "elapsed_ms": view.elapsed_ms, "speed_kph": view.channels.speed_kph,
                "integration": "v5-linear-native-speed", "length_m": length}),
            "geometry_available": same_frame and previous["geometry_available"],
            "markers_available": same_frame and previous["markers_available"]}
        # These are reference timing constraints, never independent validation.
        s1, s2, _ = view.metadata.sector_times_ms
        result["sector_boundaries_m"] = [linear(progress.elapsed_ms, progress.distance_m, t) for t in (s1, s1+s2)]
        if any(value is None for value in result["sector_boundaries_m"]):
            raise ValueError("Reference sector clocks lie outside source timing edges")
    result.pop("publication_sha256", None)
    result["publication_sha256"] = canonical_hash(result)
    return result
