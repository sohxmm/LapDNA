"""Export deterministic schemas from the Python source of truth; run at repo root."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "services" / "api" / "src"))

from lapdna.main import create_app
from lapdna.models import Catalog
from lapdna.store import ARTIFACT_ADAPTER


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if committed schemas have drifted")
    args = parser.parse_args()
    destination = REPO_ROOT / "packages" / "contracts"
    documents = {
        "openapi.json": create_app().openapi(),
        "comparison.schema.json": ARTIFACT_ADAPTER.json_schema(),
        "catalog.schema.json": Catalog.model_json_schema(),
    }
    stale = []
    for name, value in documents.items():
        content = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path = destination / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            destination.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if stale:
        print("Regenerate stale contracts: " + ", ".join(stale))
        return 1
    print("Contracts are current." if args.check else "Exported OpenAPI and artifact schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
