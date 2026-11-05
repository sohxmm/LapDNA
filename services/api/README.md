# LapDNA API

The scaffold reads imported session inventories and prepared comparison artifacts from local storage. Its wire schema is `1.1.0`. The route prefix is `/api/v1`. Run the following from the repository root in PowerShell.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r services/api/requirements.lock
.venv/Scripts/python.exe -m pip install --no-deps -e services/api
.venv/Scripts/python.exe -m uvicorn lapdna.main:app --reload --port 8000
```

On macOS/Linux use `.venv/bin/python`.

## Routes

| Endpoint | Response |
| --- | --- |
| `GET /api/v1/health` | Service version and process health |
| `GET /api/v1/sessions` | Imported sessions with driver and selectable-lap counts |
| `GET /api/v1/sessions/{session_id}/laps` | Participant roster and each indexed lap's phase, timing, capability and exclusion reasons |
| `POST /api/v1/compare` | A validated local result and its requested display order, or a specific selection error |
| `GET /api/v1/catalog` | Prepared comparison summaries with result detail level |
| `GET /api/v1/comparisons/{comparison_id}` | Immutable telemetry or sector-only artifact |
| `GET /docs` | Interactive OpenAPI explorer |

The index includes participants who lack an eligible lap. Each indexed lap has a capability of `telemetry`, `sector_only` or `unavailable`. The client uses those records to offer available Q1, Q2 and Q3 laps independently for two drivers.

Send exact IDs returned by the inventory. This example shows the request shape.

```json
{
  "session_id": "session-id",
  "lap_a_id": "first-lap-id",
  "lap_b_id": "second-lap-id",
  "allow_cross_phase": false,
  "detail_level": "auto"
}
```

Selection checks the session, both lap IDs, distinct driver numbers, eligibility and phase choice before reading a cached pair. A cross-phase request requires `allow_cross_phase: true`. The resulting artifact carries the phase on each lap and a visible conditions warning. A valid cache hit matches the snapshot digest, session identity, driver identities, lap numbers and recorded times. With `auto`, selection prefers a compatible telemetry artifact, then a prepared sector-only artifact. An explicit detail level requests that tier alone.

The response has `artifact` and `swapped`. A true swap flag means the request names the two laps in the reverse order from the stored result. The client swaps display labels and signs. A bare artifact always retains its stored B-minus-A orientation.

| Selection error | Meaning |
| --- | --- |
| 404 `session_not_found` or `lap_not_found` | Inventory lookup missed |
| 409 `data_not_imported` | The requested session needs an imported index |
| 409 `comparison_not_prepared` | Valid selection, local artifact absent |
| 422 `same_driver`, `cross_phase_not_enabled`, `lap_unavailable`, `telemetry_unavailable` | The selected pair or requested tier needs attention |
| 503 `artifact_invalid` or `quality_blocked` | Local data requires repair or the requested immutable artifact failed quality checks |

T01–T05 add the importer, local normalization and calculation on a cache miss. The current POST performs a read-only lookup. A fresh checkout returns empty session and comparison lists.

## Result details

**Telemetry** carries aligned arrays on a common distance grid, boolean brake, integer gear, estimated timing-line locations, turn markers and derived 100 m minisectors. Each mini gain equals the endpoint change in supported raw delta. The final bin may be shorter. The independent corner/straight partition supports local ranking. Speed categories use reviewed frozen reference markers. Category summaries retain included and excluded segment IDs, independent-unit counts, distance coverage, gross gains, net gain and sensitivity bounds. The schema checks the supplied partition arithmetic and rejects category claims that contradict their structured evidence. The later numerical pipeline computes those values from native samples.

**Sector-only** carries recorded lap and S1/S2/S3 times, individual sector deltas, cumulative delta at each boundary, the fallback reason and two sector-sum reconciliation checks. Its schema limits output to timing evidence. The client plots the three recorded boundaries on an ordinal sector axis.

## Local storage and configuration

- `LAPDNA_ARTIFACT_DIR` defaults to `data/artifacts`. Store one artifact per `<comparison_id>.json`.
- `LAPDNA_SESSION_DIR` defaults to a sibling `sessions` directory beside the artifact directory, normally `data/sessions`. Store one `SessionLapIndex` per `<session_id>.json`.
- `LAPDNA_CORS_ORIGINS` is a comma-separated allowlist. The defaults allow the two local Vite origins on port 5173.

The reader validates filename identity, root confinement, a 20 MiB file limit and the versioned Pydantic models. Corrupt files produce visible service errors. Blocked artifacts are withheld from the catalogue. The scaffold scans local files. T05 introduces the indexed cache and promotion mechanism for larger inventories.

## Verification

```powershell
.venv/Scripts/python.exe -m pytest services/api/tests
npm run contracts
npm run contracts:check
```

`models.py` and `inventory.py` define the schemas. The export script produces OpenAPI and JSON Schema, and the npm contract command also generates the browser types. Tests use artificial input in temporary directories. The optional `data` extra pins FastF1 3.9.2 for the importer ticket. The core service can run without installing that extra or contacting an upstream source.
