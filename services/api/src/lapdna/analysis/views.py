"""Independent, opt-in v6 publication and comparison; never edits v5 inputs."""
from lapdna.alignment.native import utc_seconds
from lapdna.alignment.view import CarStream, ViewUnavailable
from lapdna.analysis.engine import canonical_hash
from lapdna.models import TimingProvenance
from lapdna.view_models import ViewArtifact


def prepare_views(snapshot, legacy):
    streams = {number: CarStream(rows) for number, rows in snapshot["car_data"].items()}
    raw = {row["lap_id"]: row for row in snapshot["laps"]}
    laps, failures = {}, {}
    for lap_id, record in legacy["laps"].items():
        metadata = record["metadata"]
        row = raw[lap_id]
        try:
            stream = streams.get(metadata["driver_number"], CarStream([]))
            view = stream.view(metadata, utc_seconds(row["lap_start_utc"]), utc_seconds(row["lap_end_utc"]))
            laps[lap_id] = view.model_dump(mode="json")
        except ViewUnavailable as error:
            failures[lap_id] = {"gate": error.gate, "reason": str(error)}
    method = "distance-v6-fastf1-native" if legacy["provenance"]["source"] == "fastf1" else "distance-v6-openf1-native-composite"
    provenance = {key: value for key, value in legacy["provenance"].items() if key in TimingProvenance.model_fields}
    provenance.update(methodology_version=method, pipeline_version="native-views-1")
    result = {"schema_version": "2.0.0", "session": legacy["session"], "provenance": provenance,
              "legacy_publication_sha256": legacy["publication_sha256"], "laps": laps, "failures": failures}
    result["publication_sha256"] = canonical_hash(result)
    return result


def build_view(publication, a_id, b_id, requested_tier="aligned_delta", legacy_analysis=None):
    a_id, b_id = sorted((a_id, b_id))
    identity = canonical_hash({"publication": publication["publication_sha256"], "a": a_id, "b": b_id,
                               "requested_tier": requested_tier})
    return ViewArtifact.model_validate_json(__import__("json").dumps({
        "schema_version": "2.0.0", "comparison_id": "view_" + identity,
        "detail_level": "telemetry", "requested_tier": requested_tier, "view_tier": "telemetry_view",
        "methodology_version": publication["provenance"]["methodology_version"],
        "session": publication["session"], "provenance": publication["provenance"],
        "lap_a": publication["laps"][a_id], "lap_b": publication["laps"][b_id],
        "alignment": None, "legacy_analysis": None,
        "unavailable_reasons": {} if requested_tier == "telemetry_view" else {"aligned_delta": ["Aligned progress has not been prepared."]},
        "warnings": ["Cross-phase comparison: conditions may differ."] if publication["laps"][a_id]["metadata"]["phase"] != publication["laps"][b_id]["metadata"]["phase"] else [],
    }))
