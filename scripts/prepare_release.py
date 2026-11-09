"""Freeze tracked application source plus digest-verified active data for Vercel."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.analysis.store import PilotStore
from lapdna.inventory import SessionLapIndex


def freeze_data(source: Path, target: Path):
    source, target = source.resolve(), target.resolve()
    for attempt in range(5):
        catalogue_bytes = (source / "publication.json").read_bytes()
        catalogue = json.loads(catalogue_bytes)
        if catalogue.get("catalogue_version") != 2:
            raise ValueError("Release requires the explicit multi-session catalogue")
        payloads = {}
        try:
            for identifier, entry in catalogue["sessions"].items():
                manifest_path = source / entry["manifest"]
                if manifest_path.resolve().parent != (source / "manifests").resolve():
                    raise ValueError("Manifest escaped the publication root")
                manifest_bytes = manifest_path.read_bytes()
                if sha256(manifest_bytes).hexdigest() != entry["sha256"]:
                    raise ValueError("Manifest changed while preparing the release")
                manifest = json.loads(manifest_bytes)
                if manifest["schema_version"] != "1.4.0" or not manifest["method"].startswith("distance-v5-"):
                    raise ValueError(f"Rebuild {identifier} with the current method/contracts before release")
                payloads[entry["manifest"]] = manifest_bytes
                for relative, expected in manifest["files"].items():
                    path = source / relative
                    if not path.resolve().is_relative_to(source):
                        raise ValueError("Publication file escaped the root")
                    raw = path.read_bytes()
                    if sha256(raw).hexdigest() != expected:
                        raise ValueError("A publication is being activated; retry a stable snapshot")
                    payloads[relative] = raw
            break
        except ValueError:
            if attempt == 4:
                raise
            time.sleep(.15)
    for relative, raw in payloads.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (target / "publication.json").write_bytes(catalogue_bytes)
    store = PilotStore(target)
    counts = {}
    for identifier in catalogue["sessions"]:
        index = SessionLapIndex.model_validate_json((target / "sessions" / f"{identifier}.json").read_bytes())
        store.load(identifier)
        counts[str(index.session.year)] = counts.get(str(index.session.year), 0) + 1
    return {"catalogue_sha256": sha256(catalogue_bytes).hexdigest(), "sessions": len(catalogue["sessions"]),
            "sessions_by_year": counts, "publication_bytes": sum(map(len, payloads.values())) + len(catalogue_bytes)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-from", type=Path, default=Path("services/api/src/lapdna/pilot_data"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=root).returncode:
        raise ValueError("Commit the reviewed source changes before preparing a release")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output or root / "work" / "releases" / f"{commit[:8]}-{stamp}").resolve()
    if not output.is_relative_to((root / "work" / "releases").resolve()) or output.exists():
        raise ValueError("Use a new release folder inside this project's private work/releases directory")
    output.mkdir(parents=True)
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    for relative in filter(None, tracked):
        source = root / relative
        if not source.resolve().is_relative_to(root):
            raise ValueError("Tracked source escaped the repository")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    link = root / ".vercel" / "project.json"
    if link.exists():
        (output / ".vercel").mkdir()
        shutil.copy2(link, output / ".vercel" / "project.json")
    receipt = freeze_data(args.data_from, output / "services/api/src/lapdna/pilot_data")
    receipt.update(code_commit=commit, frozen_at=datetime.now(timezone.utc).isoformat())
    (output / "release-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"release_path": str(output), **receipt}, indent=2))


if __name__ == "__main__":
    main()
