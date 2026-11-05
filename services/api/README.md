# LapDNA API scaffold

The API serves validated, already prepared comparison JSON files. It does not fetch timing data, generate telemetry, or claim that the analysis pipeline exists yet. An unpopulated artifact directory returns an empty catalogue.

Run from the repository root (PowerShell):

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r services/api/requirements.lock
.venv/Scripts/python.exe -m pip install --no-deps -e services/api
.venv/Scripts/python.exe -m uvicorn lapdna.main:app --reload --port 8000
```

On macOS/Linux substitute `.venv/bin/python` for `.venv/Scripts/python.exe`.

| Endpoint | Behavior |
| --- | --- |
| `GET /api/v1/health` | Process health; does not assert upstream data availability. |
| `GET /api/v1/catalog` | Summaries of validated local artifacts, initially empty. |
| `GET /api/v1/comparisons/{comparison_id}` | Full artifact; missing is 404, malformed is 503. |
| `GET /docs` | FastAPI's interactive OpenAPI viewer. |

`LAPDNA_ARTIFACT_DIR` overrides `data/artifacts` at the repository root. Use an absolute path in deployment. `LAPDNA_CORS_ORIGINS` is a comma-separated origin allowlist and defaults to the two local Vite origins on port 5173. Artifacts are flat files named `<comparison_id>.json`; a filename must match its payload ID. Files larger than 20 MiB, paths outside the configured directory, and unsupported schemas are rejected. A corrupt artifact makes the catalogue fail visibly so an operator can repair it.

Artifacts with `quality.status = block` are deliberately withheld from the ready catalogue; a direct request returns 503 with `quality_blocked`. This differs from corrupt data, which fails the catalogue visibly. The schema requires eleven distinct reconciliation records for a usable comparison: four checks per driver and three pair checks. It also checks segment partition accounting, evidence references, source fingerprints, support intervals, gain sensitivity, and the explicit reason when fewer than three findings exist. These are structural safeguards; the later pipeline computes the quantities and applies methodological thresholds.

```powershell
.venv/Scripts/python.exe -m pytest services/api
.venv/Scripts/python.exe scripts/export_contracts.py
.venv/Scripts/python.exe scripts/export_contracts.py --check
```

`models.py` is the contract source of truth. Generate the tracked JSON schemas and TypeScript types after changing it. Numeric values are finite and carry explicit units; absent telemetry is null, brake is boolean, gear is integer, and all sample arrays share one strictly increasing distance grid. Positive delta (`B - A`) favors A. Reconciliation records retain their validation basis; timing-derived endpoint constraints are not independent accuracy checks. Numerical processing and evidence generation still require the implementation tickets.

`requirements.lock` pins the tested runtime and test tools. The optional `data` extra declares FastF1 3.9.2 plus numerical dependencies for the later importer; it is intentionally absent from this scaffold's core lock. Before implementing ingestion, install that extra in a controlled environment, resolve and commit its lock, and verify the pinned release's actual cache and authentication interfaces. The lock is generated on Python 3.11; CI verifies installation on Linux too.

The payload factory in `tests/conftest.py` is entirely artificial, for wire validation only. It is never bundled with the app or treated as a real racing comparison.
