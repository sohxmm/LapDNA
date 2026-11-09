"""Upload a frozen release's normalized files and verify them before offloading.

Operator credentials are read only from an ignored environment file. They are
passed in the child environment, never arguments, logs, receipts or artifacts.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services/api/src"))
from lapdna.ingestion.openf1 import atomic_json


def main():
    import os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--environment-file", type=Path, default=Path("work/blob-operator.env"))
    parser.add_argument("--receipt", type=Path, default=Path("work/blob-upload-receipt.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    release = args.release.resolve()
    if not release.is_relative_to((root / "work/releases").resolve()):
        raise ValueError("Only a frozen release inside work/releases can be offloaded")
    data = release / "services/api/src/lapdna/pilot_data"
    catalogue = json.loads((data / "publication.json").read_text(encoding="utf-8"))
    assets = []
    for entry in catalogue["sessions"].values():
        manifest = json.loads((data / entry["manifest"]).read_text(encoding="utf-8"))
        name = manifest["normalized"]
        path = data / name
        expected = manifest["files"][name]
        if path.is_file() and sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen normalized artifact changed before upload")
        assets.append((path, expected))
    # Stay below the included storage allowance; do not enable paid overages.
    total = sum(path.stat().st_size for path, _ in assets if path.is_file())
    if total > 750 * 1024 * 1024:
        raise ValueError("Release exceeds the project's 750 MiB storage budget; review before uploading")
    env = os.environ.copy()
    token = None
    for line in args.environment_file.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("BLOB_READ_WRITE_TOKEN="):
            value = line.partition("=")[2]
            token = json.loads(value) if value.startswith('"') else value.strip("'")
    if not token:
        raise ValueError("Pull the project's production Blob environment into the ignored operator file first")
    env["BLOB_READ_WRITE_TOKEN"] = token
    receipt = json.loads(args.receipt.read_text(encoding="utf-8")) if args.receipt.exists() else {"assets":{}}
    npx = shutil.which("npx.cmd" if os.name == "nt" else "npx")

    def upload(asset):
        path, expected = asset
        saved = receipt["assets"].get(path.name)
        if saved and saved["sha256"] == expected:
            return path.name, saved
        if not path.is_file():
            raise ValueError("Missing normalized input and no verified upload receipt")
        result = subprocess.run([npx, "--yes", "vercel@65.12.1", "blob", "put", str(path), "--pathname", "telemetry/" + expected + ".json.gz",
                                 "--access", "public", "--force", "--no-multipart", "--content-type", "application/gzip", "--scope", "sohxm44s-projects"],
                                cwd=root, env=env, capture_output=True, text=True, encoding="utf-8")
        if result.returncode:
            # Never echo arbitrary CLI output which might contain credentials.
            raise ValueError(f"Blob upload failed for {path.name}; existing frozen publication retained")
        urls = re.findall(r"https://[a-z0-9]+\.public\.blob\.vercel-storage\.com/telemetry/[A-Za-z0-9_.-]+", result.stdout + result.stderr)
        if not urls:
            raise ValueError("Upload did not return the expected public artifact URL")
        url = urls[-1]
        with urlopen(url, timeout=30) as response:
            body = response.read(20 * 1024 * 1024 + 1)
        if sha256(body).hexdigest() != expected:
            raise ValueError("Uploaded artifact did not pass independent download verification")
        return path.name, {"url":url, "sha256":expected, "bytes":len(body)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        for name, item in pool.map(upload, assets):
            receipt["assets"][name] = item
            atomic_json(args.receipt, receipt)
            print(f"Verified {name}", flush=True)
    bases = {receipt["assets"][path.name]["url"].rsplit("/", 1)[0] for path, _ in assets}
    if len(bases) != 1:
        raise ValueError("Release assets must belong to one verified storage origin")
    atomic_json(data / "remote.json", {"schema_version":"1.0.0", "base_url":bases.pop()})
    for path, _ in assets:
        # Exact verified files inside the frozen release only; no recursive delete.
        if path.is_file() and path.resolve().parent == (data / "normalized").resolve():
            path.unlink()
    print(f"Offloaded {len(assets)} verified normalized publications; no account token is included in the release", flush=True)


if __name__ == "__main__":
    main()
