# Architecture and decision record

## Structure and ownership

The application has one analytical source of truth: Python emits immutable comparison artifacts; the browser displays them. A user changing cursor position must never trigger numerical re-analysis or a remote FastF1 request. The API exposes only validated prepared results.

```text
LapDNA/
  apps/web/src/
    api.ts                       HTTP boundary (exists)
    App.tsx                      Honest no-data workspace (exists)
    styles.css                   Foundation styling (exists)
    features/comparison/         T06 selection and URL state
    features/telemetry/          T07 scales, traces, synchronized cursor
    features/track/              T08 geometry and segment picking
    features/evidence/           T09 summaries and evidence drawer
    features/export/             T10 deterministic SVG/card export
  services/api/src/lapdna/
    main.py                      Read-only HTTP application (exists)
    models.py                    Authoritative wire contracts (exists)
    store.py                     Artifact discovery/validation (exists)
    ingestion/                   T01 FastF1 adapter + snapshots
    selection/                   T02 lap/phase eligibility
    alignment/                   T03–T04 reference, distance, resampling
    analysis/                    T05 segments, metrics, evidence
    cli.py                       T01 onward; offline operator commands
  packages/contracts/            Generated JSON Schema/OpenAPI/TS
  config/circuits/                Seed manifest now; versioned profiles T03
  data/cache/                    Ignored FastF1 cache
  data/raw/                      Ignored adapter snapshots/manifests
  data/processed/                Ignored normalized lap arrays
  data/artifacts/                Ignored served comparison JSON
  data/reports/                  Ignored eligibility/quality diagnostics
  docs/                          This specification
```

Folders marked Txx are future responsibilities, not empty abstraction layers to create in advance. Prefer a few cohesive modules until behavior warrants splitting them.

## Data lifecycle

1. **Resolve** a supported circuit/session specification. Record season, event round, session identifier, source availability and adapter version. Never resolve by mutable display name alone.
2. **Acquire** once into FastF1's supported local cache. Keep credentials out of configuration files and Git. Copy only the normalized fields needed for reproducible analysis into a versioned snapshot after access/terms review.
3. **Select** qualifying phase and eligible laps, preserving rejection reasons. Candidate four-driver seeds are selected after inspecting data, not hard-coded by presumed finishing order.
4. **Freeze** a canonical reference and circuit profile for that exact event/layout. Store its reference lap ID and fingerprint. Changing the reference invalidates every comparison using it.
5. **Normalize** native channels into SI-compatible numeric arrays, preserving timestamp provenance and unsupported intervals. Keep finite numeric milliseconds at the API boundary, including fractional interpolated values. Round only for display.
6. **Compare** two explicitly identified laps; deterministic artifact identity includes the ordered lap IDs, reference fingerprint, circuit revision, methodology version and schema version. Compute in a consistent base ordering; a UI swap is a sign/label transform, not a new alignment.
7. **Validate** the entire artifact through Pydantic plus the stronger analytical checks. Reject blocked analyses from the catalogue. Record diagnostics separately so rejected comparisons remain inspectable by the operator.
8. **Publish locally** by writing a temporary file in the artifact directory, flushing and renaming atomically only after validation. Keep previous content-addressed files; never overwrite a published ID with different numbers.
9. **Serve** read-only from the allowlisted artifact directory. Unknown ID → 404; invalid request → 422; corrupt stored artifact → safe service error without file paths.
10. **Render/export** all claims from the same loaded artifact. Record comparison ID and methodology version in shared output.

## Reference and cache identity

Recommended ID format is `cmp_<24 lowercase hex chars>` from SHA-256 of canonical sorted JSON containing `lap_a_id`, `lap_b_id`, `reference_sha256`, `circuit_revision`, `methodology_version`, `schema_version` and normalized analysis settings. This is a naming decision for T05; the current service accepts safe alphanumeric/underscore/hyphen IDs for fixture compatibility.

Normalized source snapshots have their own content digest. Artifact files can use a sidecar `.sha256`; do not place a digest of the entire artifact inside itself. Pipeline version and generated UTC timestamp provide provenance but must not cause an otherwise identical comparison to receive a different identity. Re-running identical inputs must yield the same numbers and observation IDs; generated-at metadata may differ only in a newly built unpublished file.

Cache keys are scoped by source and adapter versions, event round and season, session and snapshot fingerprint. Intermediate alignment is keyed by lap, reference and method settings. Never reuse a circuit profile merely because its name matches across years.

## Why these technologies

React/TypeScript with Vite is appropriate for an interactive client with no MVP server rendering requirement. FastAPI and Pydantic keep the Python analysis and JSON contract adjacent. The initial service uses only those core dependencies; FastF1/NumPy/pandas/SciPy are optional analysis dependencies until T01. Package lockfiles record the verified scaffold environment; dependency updates are separate checked commits.

Use NumPy arrays internally and a narrow Pydantic serialization boundary. Avoid large DataFrames leaking into routes or UI schemas. Build custom SVG telemetry paths over one scale utility in T07; the grid has roughly 1,000–1,300 points for these circuit lengths, so this is manageable without a chart framework. Use SVG for the map, canvas only for PNG export. Add a chart dependency only after measuring a specific need and documenting its accessibility behavior.

No database, Redis, distributed job queue, authentication system, LLM API, live websocket or serverless numerical worker is needed for the curated release. If later users request arbitrary comparisons, introduce a bounded job API with explicit states and a persistent worker; do not execute a remote download in an HTTP request or rely on a process-local background task surviving deployment.

## Frontend state boundaries

- **Remote state:** catalogue and one immutable comparison. Abort a previous fetch when the comparison changes. Ignore late responses. Runtime validation/version checks belong at this boundary.
- **Selection state:** catalogue-derived session/phase/lap pair encoded by comparison ID in the URL; never arbitrary unvalidated filesystem paths.
- **View state:** A/B order, distance domain, cursor distance, pinned segment, visible channels, open evidence. One provider/reducer owns shared distance state; no independent cursors inside charts.
- **Derived display state:** sign/labels, sorted segment ranking, selected observation and formatted units. These transformations may not change analytical numbers.
- **Export state:** idle → preparing → ready/error. Snapshot the current comparison and selection before generating an image so user interaction cannot change the output mid-export.

Start with React state/context and a reducer. Do not add a global store or routing framework for one workspace. URL encoding must be versioned and parse unknown values safely. Never persist a complete telemetry artifact into localStorage.

## Service and deployment boundaries

Development runs Vite on loopback port 5173 and FastAPI on loopback 8000. Vite proxies `/api`, so the browser uses a same-origin path. Explicit development CORS remains useful for a separately hosted client. The production target is one Linux Python container or VM, with the built frontend served by a reverse proxy/static mount and `/api` forwarded to Uvicorn. Artifacts are mounted read-only; import jobs run separately with upstream access. A filesystem-backed single service is the MVP baseline; a static catalogue/object-store architecture is a later alternative if it removes operational cost without breaking contracts.

T12 supplies a Dockerfile and exact production command after the data size and serving behavior are measured. Avoid pretending the scaffold is deployment-ready: static routing, caching, compression, limits and health probes remain release work.

## Operational budgets (targets to measure)

| Operation | MVP target | Measurement |
| --- | --- | --- |
| Warm catalogue | <200 ms server time | Local representative 18-artifact corpus |
| Warm comparison fetch | <500 ms server time | Read/validate one real artifact |
| Compressed artifact | <1 MB | Inspect representative JSON gzip size |
| Initial workspace | <2 s on ordinary broadband after warm service | Browser measurement with named test conditions |
| Cursor interaction | <16 ms median update; no sustained visible stutter | Profile full comparison on documented device |
| Export | <3 s | 1080×1350 PNG with loaded local fonts |

These are product targets, not measured scaffold performance. If repeated schema validation makes the service slow, cache validated objects by path/mtime/size with bounded capacity, or load a validated manifest at startup. Measure first. Never weaken validation to improve a benchmark.

## Scope-change rules

An architectural change needs an explicit note here containing the trigger, selected change, rejected alternative, migration and impacted tickets. A numerical change also updates methodology/version and test corpus. This stops implementation from drifting when handed between coding sessions.
