"""Independent, opt-in v6 publication and comparison; never edits v5 inputs."""
import json

from lapdna.alignment.native import utc_seconds
from lapdna.alignment.view import CarStream, ViewUnavailable
from lapdna.alignment.view_delta import prepare_progress, align_pair
from lapdna.analysis.engine import canonical_hash, pairing
from lapdna.models import TimingProvenance
from lapdna.view_models import NativeLapView, ViewArtifact


def prepare_views(snapshot, legacy):
    streams = {number: CarStream(rows) for number, rows in snapshot["car_data"].items()}
    raw = {row["lap_id"]: row for row in snapshot["laps"]}
    laps, failures, candidates, alignment_failures = {}, {}, {}, {}
    for lap_id, record in legacy["laps"].items():
        metadata = record["metadata"]
        row = raw[lap_id]
        try:
            stream = streams.get(metadata["driver_number"], CarStream([]))
            view = stream.view(metadata, utc_seconds(row["lap_start_utc"]), utc_seconds(row["lap_end_utc"]))
            laps[lap_id] = view.model_dump(mode="json")
            try:
                progress = prepare_progress(view)
                candidates[lap_id] = {"integrated_length_m": progress.integrated_length_m,
                    "cumulative_bound_m": progress.cumulative_bound_m[-1], "bridges": len(progress.bridges)}
            except ViewUnavailable as error:
                alignment_failures[lap_id] = {"gate": error.gate, "reason": str(error)}
        except ViewUnavailable as error:
            failures[lap_id] = {"gate": error.gate, "reason": str(error)}
    method = "distance-v6-fastf1-native" if legacy["provenance"]["source"] == "fastf1" else "distance-v6-openf1-native-composite"
    provenance = {key: value for key, value in legacy["provenance"].items() if key in TimingProvenance.model_fields}
    provenance.update(methodology_version=method, pipeline_version="native-views-1")
    result = {"schema_version": "2.0.0", "session": legacy["session"], "provenance": provenance,
              "legacy_publication_sha256": legacy["publication_sha256"], "laps": laps, "failures": failures,
              "alignment_candidates": candidates, "alignment_failures": alignment_failures,
              "reference": None, "sector_boundaries_m": []}
    if legacy.get("reference_lap_id"):
        result["reference"] = {"lap_id": legacy["reference_lap_id"], "length_m": legacy["distance_m"][-1],
            "sha256": legacy["reference_sha256"], "selection_basis": "legacy_v5",
            "geometry_available": bool(legacy.get("geometry")), "markers_available": bool(legacy.get("corners"))}
        result["sector_boundaries_m"] = legacy["sector_boundaries_m"]
    result["publication_sha256"] = canonical_hash(result)
    return result


def build_view(publication, a_id, b_id, requested_tier="aligned_delta", legacy_analysis=None):
    a_id, b_id = sorted((a_id, b_id))
    identity = canonical_hash({"publication": publication["publication_sha256"], "a": a_id, "b": b_id,
                               "requested_tier": requested_tier})
    alignment, reasons, analysis = None, {}, None
    if requested_tier != "telemetry_view":
        if not publication.get("reference"):
            reasons["aligned_delta"] = ["No timing/speed reference has been prepared for this session."]
        elif any(identifier not in publication.get("alignment_candidates", {}) for identifier in (a_id, b_id)):
            reasons["aligned_delta"] = [publication.get("alignment_failures", {}).get(identifier,
                {"reason": "Native speed progress has not been prepared."})["reason"] for identifier in (a_id, b_id)
                if identifier not in publication.get("alignment_candidates", {})]
        else:
            alignment = align_pair(*(NativeLapView.model_validate_json(json.dumps(publication["laps"][identifier]))
                for identifier in (a_id, b_id)), publication["reference"], publication["sector_boundaries_m"])
        if requested_tier == "analysis":
            if alignment is not None and legacy_analysis is not None and not (alignment.lap_a.bridges or alignment.lap_b.bridges):
                analysis = legacy_analysis
            else:
                reasons["analysis"] = ["Unchanged v5 corner-analysis gates did not accept this pair; bridges cannot supply evidence."]
    return ViewArtifact.model_validate_json(json.dumps({
        "schema_version": "2.0.0", "comparison_id": "view_" + identity,
        "detail_level": "telemetry", "requested_tier": requested_tier,
        "view_tier": "analysis" if analysis is not None else "aligned_delta" if alignment is not None else "telemetry_view",
        "methodology_version": publication["provenance"]["methodology_version"],
        "session": publication["session"], "provenance": publication["provenance"],
        "lap_a": publication["laps"][a_id], "lap_b": publication["laps"][b_id],
        "alignment": alignment.model_dump(mode="json") if alignment is not None else None,
        "legacy_analysis": analysis.model_dump(mode="json") if analysis is not None else None,
        "unavailable_reasons": reasons,
        "warnings": pairing(*(publication["laps"][identifier]["metadata"] for identifier in (a_id, b_id)),
            records=[publication.get("conditions", {}).get(identifier, {}) for identifier in (a_id, b_id)])["warnings"],
    }))
