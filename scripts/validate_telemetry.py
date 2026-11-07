"""Validate every same-phase fastest eligible driver pair in a local publication."""

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
from statistics import median
from time import perf_counter

from lapdna.analysis.store import PilotStore
from lapdna.inventory import SessionLapIndex


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    parser.add_argument("--output", type=Path, default=Path("work/monza2024/validation-report.json"))
    args = parser.parse_args()
    store = PilotStore(args.publication)
    session_id = "2024-16-monza-Q"
    publication = store.load(session_id)
    index = SessionLapIndex.model_validate_json((args.publication / "sessions" / f"{session_id}.json").read_bytes())
    results, elapsed = [], []
    for phase in ("Q1", "Q2", "Q3"):
        by_driver = {}
        for lap in index.laps:
            if lap.phase != phase or lap.capability == "unavailable":
                continue
            previous = by_driver.get(lap.driver_number)
            if previous is None or (lap.lap_time_ms, lap.lap_number) < (previous.lap_time_ms, previous.lap_number):
                by_driver[lap.driver_number] = lap
        for a, b in combinations(by_driver.values(), 2):
            start = perf_counter()
            artifact = store.compare(session_id, a.lap_id, b.lap_id, "auto")
            elapsed.append((perf_counter() - start) * 1000)
            reverse = store.compare(session_id, b.lap_id, a.lap_id, "auto")
            assert reverse.model_dump() == artifact.model_dump()
            if artifact.detail_level == "telemetry":
                final = artifact.delta_ms[-1] - artifact.delta_ms[0]
                assert abs(sum(segment.gain_ms for segment in artifact.segments) - final) < 1e-6
                assert abs(sum(section.gain_ms for section in artifact.estimated_minisectors) - final) < 1e-6
                assert len(artifact.distance_m) <= 5000
            results.append({"phase": phase, "a": a.lap_id, "b": b.lap_id,
                            "comparison_id": artifact.comparison_id, "tier": artifact.detail_level,
                            "quality": artifact.quality.status, "observations": len(getattr(artifact, "observations", [])),
                            "fallback_reason": getattr(artifact, "fallback_reason", None)})
    official = {
        "openf1_9586_4_11": (79327., [26492., 26579., 26256.]),
        "openf1_9586_81_15": (79436., [26407., 26643., 26386.]),
    }
    for identifier, (lap_ms, sectors) in official.items():
        metadata = publication["laps"][identifier]["metadata"]
        assert metadata["lap_time_ms"] == lap_ms and metadata["sector_times_ms"] == sectors
    report = {"session_id": session_id, "source_snapshot_sha256": index.source_snapshot_sha256,
              "publication_sha256": publication["publication_sha256"],
              "scope": "All distinct-driver, fastest eligible same-phase pairs; source download disabled/not used. This does not exhaust every actual lap pair.",
              "driver_count": len(index.drivers), "indexed_laps": len(index.laps),
              "capabilities": dict(Counter(lap.capability for lap in index.laps)),
              "pair_counts": dict(Counter(result["tier"] for result in results)),
              "phase_counts": dict(Counter(result["phase"] for result in results)),
              "observation_counts": dict(Counter(str(result["observations"]) for result in results if result["tier"] == "telemetry")),
              "cold_calculation_ms": {"median": median(elapsed), "maximum": max(elapsed)},
              "official_spot_checks": {"source": "FIA 2024 Italian Grand Prix qualifying sector analysis; NOR and PIA Q3 best rows checked separately.",
                                      "url": "https://www.fia.com/sites/default/files/2024_16_ita_f1_q0_timing_qualifyingsessionsectoranalysis_v01.pdf",
                                      "lap_number_note": "FIA report ordinals differ from provider ordinals; matching uses driver, phase, duration and sector triple.",
                                      "records": {identifier: {"lap_time_ms": duration, "sector_times_ms": sectors} for identifier, (duration, sectors) in official.items()}},
              "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Validated {len(results)} pairs and their reversed selections: {report['pair_counts']}")
    print(f"Phases {report['phase_counts']}; observation counts {report['observation_counts']}")
    print(f"Median cold {median(elapsed):.1f} ms; maximum {max(elapsed):.1f} ms")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
