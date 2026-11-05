# Local operation, preparation and release

## Current scaffold

Use the [README](../README.md) setup for Node 24, Python 3.11, the root virtual environment and locked dependencies. From the repository root, start the API and client in separate terminals:

```powershell
.venv\Scripts\python -m uvicorn lapdna.main:app --host 127.0.0.1 --port 8000
```

```powershell
npm run dev
```

Vite serves the client at `http://127.0.0.1:5173` and proxies `/api` to port 8000. Ctrl+C stops either foreground process. The normal workspace displays imported data availability. Its explicitly labeled synthetic design preview demonstrates chart interactions. The optional standard-library source probe in [sources](09-sources.md) checks historical OpenF1 availability; it saves no session or comparison.

| Current setting | Behavior |
| --- | --- |
| `LAPDNA_ARTIFACT_DIR` | Defaults to `data/artifacts` under the repository. Holds locally prepared comparison JSON. |
| `LAPDNA_SESSION_DIR` | Defaults to the `sessions` sibling of the selected artifact directory. Holds local session lap indexes. |
| `LAPDNA_CORS_ORIGINS` | Comma-separated allowed origins. Local defaults include localhost and 127.0.0.1 on port 5173. |

Prefer absolute override paths. Relative values use the API process working directory. The example environment file documents settings; set PowerShell variables explicitly when needed. Never place credentials in the repository.

Current GET routes expose health, session inventory, session laps, prepared catalogue and immutable result lookup. `POST /api/v1/compare` validates a request and can return a compatible prepared result, with a swap flag for reverse order. A new uncached selection currently returns `comparison_not_prepared`. A missing selected import returns `data_not_imported`. [The contract](05-contracts.md) distinguishes capability, bad identity and transport failures. T05 replaces the prepared-only miss behavior with bounded local computation.

## Planned operator interfaces

The CLI below is the target for T01–T05. Implement via `argparse`, with help, configurable local paths, a concise summary, JSON report path and nonzero exit on failure.

```text
python -m lapdna.cli import-session --circuit monza --year 2024 --event "Italian Grand Prix" --session Q
python -m lapdna.cli list-laps --snapshot <manifest> --output <report>
python -m lapdna.cli build-reference --snapshot <manifest> --profile <profile>
python -m lapdna.cli normalize-session --snapshot <manifest> --reference <reference> --output <revision-directory>
python -m lapdna.cli build-comparison --session-revision <revision> --lap-a <id> --lap-b <id> --detail-level auto
python -m lapdna.cli validate --artifact <artifact> --review <review-record>
python -m lapdna.cli publish --session-revision <revision> --review <review-record>
```

Only `import-session` contacts upstream. It uses a project-local cache, an explicitly resolved event, bounded retries for transient source failures, a sanitized manifest and atomic snapshot writes. Authentication and input errors fail immediately. A repeat import reuses a matching valid immutable snapshot; `--refresh` obtains a new revision. `list-laps` may take an optional phase filter for inspection; all participants/laps remain in the stored inventory. `build-comparison` takes `--allow-cross-phase` when the supplied phases differ. It exercises the same local selection/resolver/validator used by the API.

## Preparing a qualifying session

1. Verify the completed conventional qualifying event and layout against the supported schedule. Resolve the upstream identity through the pinned FastF1 adapter and supported account flow. Capture retrieval UTC, versions, source coverage, counts and digests.
2. Inspect the complete source roster and each driver's actual Q1/Q2/Q3 laps. Record timing/telemetry capabilities, eligibility reasons, known dry context and missing phases. Retain rejected rows or unknown-phase diagnostics for reconciliation. An eliminated driver's absent later phases stay unavailable.
3. Review the versioned circuit reference, turn labels and distance mapping, including branch order at a crossover. Confirm disjoint region windows, native reference apex supports and the frozen 150/250 km/h bands. Preserve rejected/unstable classes as unknown. A changed profile, source snapshot or methodology starts a new revision.
4. Normalize each eligible lap **once offline** to the canonical grid with 100 m bin edges and region/sector/turn markers. Save aligned arrays, the native evidence inputs T05 needs, masks and diagnostics alongside the session index under separate data paths. Keep sector-only eligible records even when spatial normalization fails. Run required individual timing checks before promotion.
5. Build the representative matrix in [verification](07-verification.md), including new local cache misses, reversed selections, two phase contexts and reduced capability. Validate appropriate tiers independently. For promoted editorial examples, match actual lap rows to official documents, review all warnings and verify every selected claim.
6. Atomically promote a validated **session revision** with its manifest and optional highlighted examples. This turns on all indexed eligible selections, including pairs with no existing result. Preserve the old complete revision for rollback. No pairwise cartesian prebuild is required.
7. Open a newly computed real comparison, inspect its turn ruler, category analysis and both export formats. Publish analysis cards through a deliberate editorial action. The application generates exports locally.

## Serving a new pair after T05

The service reads the selected session revision, validates exact driver/lap/phase identities and cross-phase opt-in, then checks the content-addressed result index. When the result is absent it computes from the two local normalized records/native-support sidecars, runs the quality gates and atomically persists the result. Do not start a source import, fetch source lap data or build an entire session on an HTTP request.

Canonicalize A/B for cache identity and use the order flag on return. Include method/config, source revision, profile/reference, selected IDs and output tier in the key. A changed input creates a different ID. Concurrent requests for one key share one builder. Bound simultaneous different-key builders, queued work, file sizes and disposable cache capacity using the documented runtime limits; shed excess load explicitly. A request interrupted before promotion leaves either the previous valid file or no file.

Distinguish disposable decoded-array/hot-result caches from immutable shared results. Persist a successful result/identity on durable storage before emitting a share URL. Evicting a hot cache entry must still allow exact lookup or deterministic regeneration under its retained immutable revision. Keep published examples and shared-result provenance across restarts and dataset rollovers. If durable capacity is exhausted, fail new promotion explicitly and preserve existing shared results; expand/archive storage through an operator action. Avoid silently changing an ID's inputs or returning a different selection.

## Failure and recovery

| Failure | Behavior |
| --- | --- |
| Authentication or source change during import | Report resolved event, pinned release and sanitized reason. Leave the previous revision active. |
| Timing/validity missing | Record exclusion and disable actual lap/phase as applicable. Operator inspects source evidence. |
| Telemetry absent, alignment or interior check blocked | For auto selection, use independently eligible recorded sector timing with the fallback reason. Explicit telemetry requires eligible telemetry. Never fill a spatial gap from sector ends. |
| Timing also fails | Withhold both tiers, return the failure and retain diagnostics. |
| Unknown session, foreign/unknown lap, same driver or cross-phase disabled | Return the corresponding selection error before doing numerical work. Preserve the reader's selection for correction. |
| Local builder busy, crashed or disk full | Report retryable capacity/failure as appropriate. Remove only owned temporary files, keep last complete revision/IDs and permit a safe retry. |
| Invalid artifact, revision or manifest | Reject corrupted data, log IDs/digests and restore a checked previous revision; never substitute an unrelated comparison. |
| Missing immutable link | Explain the missing result. Preserve the original ID and return a recovery path to session selection. |

Log request/revision IDs, lap phases, chosen tier, cache hit/miss, build time and safe reason codes. Keep credentials, auth headers, raw source samples and local filesystem paths outside public responses.

## Production target for T12

Serve the Vite bundle and FastAPI under one origin. Provide read-only validated session indexes/prealigned data, a durable writable result store and a bounded disposable cache as distinct responsibilities. Permit the documented GET endpoints and `POST /api/v1/compare` only; operator revision promotion uses offline local commands. Keep import dependencies/credentials out of the serving image wherever possible. Health checks, compression, immutable result caching, short inventory revalidation, bounds and clear error handling belong to packaging.

Verify startup and cold pair resolution with upstream networking disabled. Verify concurrent builders, restarts, corrupt-data rejection, independent rollback and shared-link persistence. Record actual environment, measurements and URL only after a release has passed [verification](07-verification.md).

## Commits and handoff

Push checked, small completed feature commits to the configured branch of [sohxmm/LapDNA](https://github.com/sohxmm/LapDNA). Use existing Git identity, factual imperative subjects and reviewed staged files. Preserve existing history. Exclude credentials, environments, dependency directories, local caches, bulk source telemetry, machine-specific paths and transient exports from Git.

After each increment update the [ticket board](06-implementation-plan.md) and [handoff](10-handoff.md) with scope, verification commands/results, blockers and next step. Record any changed numerical assumption and its evidence in the methodology, rerun its regression gate and version affected results.
