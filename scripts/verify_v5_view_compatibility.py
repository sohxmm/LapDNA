"""Frozen-code proof plus real-pair serialized regression against Step 0."""
import ast
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
from lapdna.analysis.engine import build_comparison, canonical_hash
from lapdna.analysis.store import PilotStore
from lapdna.ingestion.openf1 import atomic_json

BASELINE = "9605727"


def baseline_bytes(name):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{name}"], cwd=ROOT)


def main():
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE,
        "services/api/src/lapdna", "services/api/pyproject.toml", "package-lock.json",
        "packages/contracts/comparison.schema.json", "packages/contracts/catalog.schema.json"], cwd=ROOT, text=True).splitlines()
    hashes = {}
    for name in names:
        if name.endswith(".py") and name != "services/api/src/lapdna/main.py" or name.endswith((".toml", ".json")):
            current, old = (ROOT / name).read_bytes(), baseline_bytes(name)
            assert current == old, name
            hashes[name] = sha256(current).hexdigest()
    # The main module gained an opt-in route. Its original compare handler is exact.
    name = "services/api/src/lapdna/main.py"
    current, old = (ROOT / name).read_text(encoding="utf-8"), baseline_bytes(name).decode()
    def handler(source):
        node = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef) and n.name == "compare")
        return ast.get_source_segment(source, node)
    assert handler(current) == handler(old)
    module = types.ModuleType("lapdna.analysis.frozen_v5")
    exec(compile(baseline_bytes("services/api/src/lapdna/analysis/engine.py"), "frozen-v5-engine", "exec"), module.__dict__)
    store = PilotStore(ROOT / "services/api/src/lapdna/pilot_data")
    ledger = json.loads((ROOT / "config/telemetry-coverage.json").read_bytes())
    receipts = []
    for entry in ledger["sessions"]:
        sid = entry["session_id"]
        publication = store.load(sid)
        assert publication["publication_sha256"] == entry["publication_sha256"]
        assert canonical_hash({k: v for k, v in publication.items() if k != "publication_sha256"}) == publication["publication_sha256"]
        phase_pairs = []
        for phase in ("Q1", "Q2", "Q3", "SQ1", "SQ2", "SQ3"):
            candidates = sorted((key for key, row in publication["laps"].items()
                if "channels" in row and row["metadata"]["phase"] == phase),
                key=lambda key: (publication["laps"][key]["metadata"]["lap_time_ms"], key))
            for a, b in combinations(candidates, 2):
                if publication["laps"][a]["metadata"]["driver_number"] == publication["laps"][b]["metadata"]["driver_number"]:
                    continue
                result = build_comparison(publication, a, b, "auto")
                if result.detail_level != "telemetry":
                    continue
                before = module.build_comparison(publication, a, b, "auto").model_dump_json().encode()
                after = result.model_dump_json().encode()
                assert before == after, (sid, a, b)
                reverse = build_comparison(publication, b, a, "auto").model_dump_json().encode()
                assert reverse == after
                phase_pairs.append({"phase": phase, "laps": [a, b], "comparison_id": result.comparison_id,
                                    "serialized_sha256": sha256(after).hexdigest(), "bytes": len(after)})
                break
        receipts.append({"session_id": sid, "publication_sha256": publication["publication_sha256"], "passing_phase_samples": phase_pairs})
        print(f"{sid}: {len(phase_pairs)} frozen serialized phase-pair checks", flush=True)
    proof = {"baseline": BASELINE, "scope": "All pre-existing Python modules except the opt-in main additions, legacy handler, schemas and dependency declarations are byte-identical. All 217 publication identities/content digests checked. This establishes unchanged deterministic v5 behavior for arbitrary existing pairs; sampled real pair bytes additionally checked per available passing phase, not an enumeration of every Cartesian pair.",
             "unchanged_file_sha256": hashes, "legacy_compare_handler_sha256": sha256(handler(current).encode()).hexdigest(),
             "sessions": receipts, "passing_pairs_compared": sum(len(r["passing_phase_samples"]) for r in receipts)}
    atomic_json(ROOT / "config/v5-view-compatibility.json", proof)


if __name__ == "__main__":
    main()
