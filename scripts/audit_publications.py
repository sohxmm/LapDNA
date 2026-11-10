"""Audit activated publications and their actual supported comparison coverage."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.analysis.engine import canonical_hash
from lapdna.analysis.store import PilotStore
from lapdna.inventory import SessionLapIndex


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    parser.add_argument("--output", type=Path, default=Path("config/telemetry-coverage.json"))
    parser.add_argument("--reports", type=Path, default=Path("work/publication-validation"))
    args = parser.parse_args()
    store = PilotStore(args.publication)
    manifests = store.manifests()
    indexed = {path.stem for path in (args.publication / "sessions").glob("*.json")}
    if indexed != set(manifests):
        raise ValueError(f"Inventory/activation mismatch: {sorted(indexed.symmetric_difference(manifests))}; republish the retained source snapshots before release")
    results = []
    args.reports.mkdir(parents=True, exist_ok=True)
    for identifier in sorted(manifests):
        index_path = args.publication / "sessions" / f"{identifier}.json"
        raw_index = index_path.read_bytes()
        if sha256(raw_index).hexdigest() != manifests[identifier]["files"][f"sessions/{identifier}.json"]:
            raise ValueError(f"Session inventory digest mismatch: {identifier}")
        index = SessionLapIndex.model_validate_json(raw_index)
        publication = store.load(identifier)
        expected_hash = canonical_hash({key: value for key, value in publication.items() if key != "publication_sha256"})
        if publication["publication_sha256"] != expected_hash or publication["provenance"]["source_snapshot_sha256"] != index.source_snapshot_sha256:
            raise ValueError(f"Publication/source identity mismatch: {identifier}")
        eligible = {lap.lap_id for lap in index.laps if lap.capability != "unavailable"}
        if eligible != set(publication["laps"]):
            raise ValueError(f"Normalized lap identities disagree with the selection inventory: {identifier}")
        roster = {driver.driver_number: driver for driver in index.drivers}
        for record in publication["laps"].values():
            metadata = record["metadata"]
            driver = roster[metadata["driver_number"]]
            if metadata["driver_code"] != driver.driver_code or metadata.get("team_colour") != driver.team_colour:
                raise ValueError(f"Source roster/colour identity mismatch: {identifier}")
        report = args.reports / f"{identifier}.json"
        command = [sys.executable, str(Path(__file__).with_name("validate_telemetry.py")), "--publication", str(args.publication), "--session", identifier, "--output", str(report)]
        checked = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if checked.returncode:
            raise ValueError(f"Comparison validation failed: {identifier}\n{checked.stderr[-1500:]}")
        validation = json.loads(report.read_text(encoding="utf-8"))
        capabilities = Counter(lap.capability for lap in index.laps)
        row = {"session_id": identifier, "year": index.session.year, "round": index.session.round,
               "event_name": index.session.event_name, "source": publication["provenance"]["source"],
               "drivers": len(index.drivers), "lap_records": len(index.laps), "capabilities": dict(capabilities),
               "verified_fastest_phase_pairs": validation["pair_counts"],
               "telemetry_discovery_choices": validation["telemetry_discovery_choices"],
               "source_snapshot_sha256": index.source_snapshot_sha256, "publication_sha256": publication["publication_sha256"],
               "method": manifests[identifier]["method"]}
        results.append(row)
        print(identifier, dict(capabilities), validation["pair_counts"], flush=True)
    output = {"schema_version": "1.0.0", "scope": "Digest-checked actual native publications, fastest eligible same-phase pairs and explicit telemetry-discovery choices plus reversals. Calendar/provider year ranges do not imply coverage; arbitrary actual-lap pairs are checked when requested.",
              "source_year_target": [2018, 2026], "session_count": len(results),
              "sessions_by_year": dict(sorted(Counter(str(row["year"]) for row in results).items())),
              "sessions": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(output, indent=2), encoding="utf-8")
    temporary.replace(args.output)
    print(f"Audited {len(results)} real session publications. Coverage: {output['sessions_by_year']}")


if __name__ == "__main__":
    main()
