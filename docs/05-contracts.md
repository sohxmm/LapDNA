# Data and API contracts

Authoritative source: `services/api/src/lapdna/models.py`. Generated outputs: `packages/contracts/openapi.json`, `comparison.schema.json`, `catalog.schema.json`, and `api.d.ts`. This guide explains semantics; it is not a second hand-maintained type definition.

## API surface that exists now

| Method/path | Success | Failure |
| --- | --- | --- |
| `GET /api/v1/health` | `Health`: status `ok`, service `lapdna-api`, package version | Process availability only; no data claim |
| `GET /api/v1/catalog` | `Catalog`: schema version and prepared comparison summaries; empty list is valid | 503 `artifact_invalid` for corrupt/unreadable catalogue artifact |
| `GET /api/v1/comparisons/{comparison_id}` | One schema-validated `ComparisonArtifact` | 404 unknown; 422 invalid ID; 503 corrupt or quality-blocked |
| `GET /openapi.json` | FastAPI-generated contract | Framework route |
| `GET /docs` | Local interactive API documentation | Framework route |

An ID is 1–100 ASCII letters, digits, underscores or hyphens. File extensions and path separators are not accepted. Files are read only from the configured artifact root; symlinks outside it are refused. Reads have a 20 MiB file-size guard. There is no upload, ingestion, arbitrary URL fetch or calculation endpoint.

Application errors use `{"error":{"code":"comparison_not_found","message":"This comparison has not been prepared."}}`. Other application codes are `invalid_request`, `artifact_invalid` and `quality_blocked`. Unknown framework routes may use FastAPI's default 404 body; clients must tolerate an unsuccessful response without assuming a JSON shape. The frontend scaffold reports HTTP failures and permits retry.

The current store enumerates flat `*.json` artifacts and omits intentionally blocked comparisons. T05 replaces discovery with an atomic reviewed catalogue manifest. Until then, **do not place a `catalog.json` manifest in that directory**: the current reader would correctly reject it as a malformed comparison. Empty/missing data directory returns an empty catalogue. This differs from corrupted data, which fails visibly.

## Schema conventions

- Version is currently the literal `1.0.0`. Contract changes regenerate all outputs together and update client compatibility handling. There are no real published v1 datasets yet. Before the first real publication, settle required fields through T01–T05; do not silently mutate previously published artifacts afterward.
- Unknown properties are forbidden by Python models. Integer fields and booleans are strict. All floating-point values are finite; absent observations are JSON `null`, never NaN/Infinity/zero substitutes.
- Distance is metres, speed km/h, throttle percent, elapsed/delta/official timing milliseconds. Interpolated timings may be fractional milliseconds. Keep precision internally; display rounding belongs in UI formatters.
- Every per-sample array is parallel to one `distance_m` array of 2–5000 strictly increasing points starting at zero. The last distance is the canonical approximate lap length. Segment and sector boundaries are inserted into the grid by T03/T04; spacing is otherwise 5 m, so consumers must not assume index × 5.
- `time_raw_ms` is elapsed time from the official lap-start clock on the normalized distance axis. “Raw” means it is not corrected to match sector times; it has still been interpolated. There is no adjusted-time field or hidden corrected mode.
- `delta_ms[k] = channels_b.time_raw_ms[k] − channels_a.time_raw_ms[k]`. Positive means A has taken less time. `valid[k]` describes elapsed-time comparison support, not blanket validity of all channels. Optional-channel nulls are independent.
- Gear is integer 0–8 (0 is neutral) or null. Brake is true/false/null, not 0–100 pressure. Geometry x/y are metres in a display reference system; null coordinates must occur as pairs.

## Comparison structure

| Field/group | Meaning |
| --- | --- |
| `comparison_id`, `schema_version` | Immutable identity and compatibility |
| `session` | Season, resolved round, conventional Q, phase, supported circuit key, event name |
| `lap_a`, `lap_b` | Different driver numbers; explicit lap IDs/numbers, names/codes, official lap and 3 sector durations, compound, tyre age, track-status string |
| `provenance` | FastF1 version, pipeline version, methodology version, reference/source snapshot hashes, generated UTC, source session, circuit revision, canonical reference lap |
| `distance_m` | Shared approximate-distance coordinate |
| `channels_a`, `channels_b` | Equal-length speed, throttle, gear, brake and raw elapsed-time arrays |
| `geometry` | Reference x/y arrays on the same grid; not either driver's racing line |
| `delta_ms`, `valid` | Pair elapsed difference and support flags |
| `sector_boundaries_m` | Fixed reference estimates for the first two official timing lines; not marshal sectors |
| `quality` | pass/warn/block, warnings, required reconciliation checks, native counts/gaps, integrated lengths and normalization factors |
| `segments` | Ordered additive partition, IDs/labels/kind/group, boundaries, local gain, sensitivity bounds, quality, evidence references |
| `evidence` | Metric values/units/range, differences, sample support and optional transition intervals |
| `observations` | At most three texts with template ID, segment and evidence references |
| `insufficient_evidence_reason` | Required explanatory text when fewer than three findings exist; null when all three exist |

The wire `source` is currently `fastf1`. The tiny test factory uses artificial identifiers and a conspicuous synthetic provenance description solely to exercise this wire shape; it must never be copied into served storage. A future visible synthetic demo needs a distinct source enum/schema path and prominent labeling.

## Reconciliation records

Each record has `driver` A/B/pair, `metric`, `basis`, official/observed/residual milliseconds and severity. Residual equals observed minus official. Pair values may be negative. Missing observed/residual must both be null and cannot pass.

Required set for a usable artifact:

| Subject | Metrics | Basis |
| --- | --- | --- |
| A and B | `sector_sum`, `sliced_duration` | timing record consistency / timing constraint as defined in methodology |
| A and B | `cumulative_sector_1`, `cumulative_sector_2` | cross-lap consistency, or calibration for the reference lap |
| Pair | `cumulative_sector_1`, `cumulative_sector_2` | cross-lap consistency |
| Pair | `lap_gap` | timing constraint |

There are 11 required subject/metric pairs. The schema checks completeness, uniqueness, residual arithmetic, and that overall quality is no lower than individual checks. T04 also computes the severities from versioned thresholds, verifies each official/observed value against its actual source arrays/metadata, enforces basis choices and incorporates non-timing flags. A supplied `pass` string is never enough to establish correctness.

## Segments and evidence

Usable artifacts contain an adjacent partition from 0 to lap length; boundaries occur on the shared grid. Each numeric gain requires full elapsed-time support throughout its range and must equal the endpoint delta difference. A sensitivity interval, if present, contains the unshifted gain. Unsupported gains remain null. Wrapped complexes are two non-wrapping partition pieces with the same `group_id`; additive lists use those pieces once each.

Evidence scalar difference is B−A. For onset intervals `[a0,a1]` and `[b0,b1]`, the difference interval is `[b0−a1,b1−a0]` in the same unit. Do not replace uncertain intervals with an exact braking point. Metrics use a fixed code: segment gain, minimum/entry/exit speed, brake onset, throttle pickup, full-throttle fraction or gear at marker. A segment-gain evidence record represents A/B traversal durations, so its B−A difference equals `gain_ms`.

Schema validation checks references exist and numbers/interval arithmetic are consistent. T05 further checks metric-to-unit compatibility, native support, evidence location relative to its segment, one observation per disjoint interval, template eligibility, text/value correspondence, sensitivity/materiality and publication review. Those are analytical guarantees, not merely shape checks.

## Required pre-publication contract additions

The existing contract is usable for scaffold/API development. These exact additions belong in the responsible ticket before dependent behavior is built; they are already planned, not questions left for implementation brainstorming:

| Ticket | Extension |
| --- | --- |
| T01 | `provenance.source_retrieved_at` timezone-aware UTC distinct from generation; snapshot manifest source URLs/terms/access status |
| T02 | `lap_a/b.lap_start_utc` (nullable only when clock unavailable), `eligibility_summary` with machine-readable flags; retain source values in snapshot even if UI cannot use them |
| T03 | `provenance.circuit_config_sha256`; `geometry.corners` objects `{marker_id,label,distance_m,x,y,label_x,label_y}` in metres after rotation, derived from reviewed reference; store rotation exactly once in profile |
| T04 | `provenance.settings_sha256`; `analysis_settings` with grid step, actual gap/residual/scale/observation thresholds; typed quality reasons for independently missing channels and interval flags |
| T05 | `review` with status `pending/reviewed/rejected`, review timestamp, reviewed dataset ID, official-source URLs and verification scope; `template_version` per observation; catalogue generation/revision and artifact digest fields |

Any source metadata absence must have a documented null/rejection policy. Do not use `generated_at` as import time or fabricate lap-start UTC. Add sample fixtures, model validation, generated schemas and frontend types in the same ticket. Production catalogue promotion requires `reviewed`; the current test scaffold has no editorial review workflow.

## Generate and check

`npm run contracts` runs `scripts/export_contracts.py`, then `openapi-typescript`. The Python interpreter defaults to the root `.venv` (platform-aware) or `python`; `LAPDNA_PYTHON` overrides it. `npm run contracts:check` regenerates and compares all four files, failing on drift. It may leave changed generated files for inspection; CI must commit none of them automatically.

Do not hand-write or copy TypeScript model interfaces. Browser modules import `components['schemas'][...]` from the generated declaration. Unit tests should test meaningful contract invariants and API behavior, not simply assert a field list equals the implementation.
