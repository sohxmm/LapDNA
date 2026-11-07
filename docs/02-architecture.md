# Architecture and decisions

## Ownership and layout

Python computes lap eligibility, reference alignment, delta, mini-sectors, class metrics and findings. React renders those supplied facts. Cursor and zoom operations never request upstream data or recompute scientific metrics.

The [approved interface/scope decision](17-approved-ui-and-telemetry-rollout.md) fixes the sports-editorial landing and G1 stack. Real telemetry is eligible only for verified sessions/channels in 2018–2026; older timing comparisons continue. Three circuits are validation pilots before broader layout coverage. Pilot local storage precedes measured durable archive publication; bulk telemetry never enters the Vercel bundle or Git.

```text
apps/web/src/
  App.tsx                         Home and explicit preview routing
  features/comparison/            Inventory, phase/lap controls and cached-result UI
  features/telemetry/              ECharts adapter, turn ruler, numeric readout
    DesignPreview.tsx             Explicit synthetic example
    design-fixture.json           Offline-generated fictional loop only
    SectorPoints.tsx              Discrete sector-crossing points and table
  features/track/                 T08 real reference map
  features/export/                T10 card and evidence download
services/api/src/lapdna/
  main.py                         Local HTTP API
  models.py                       Analytical wire contracts
  inventory.py                    Roster/lap indexes and selection validation
  store.py                        Validated immutable artifact reads
  ingestion/                      T01 source adapters and snapshots
  selection/                      T02 eligibility and phase inventory
  alignment/                      T03–T04 reference and normalized per-lap arrays
  analysis/                       T05 metrics, class evidence and local engine
packages/contracts/               Generated OpenAPI, JSON Schema, TypeScript
data/sessions/                    Ignored imported roster/lap indexes
data/processed/                   Ignored normalized per-lap arrays
data/artifacts/                   Ignored immutable prepared/cache outputs
config/circuits/                  Versioned profiles and seed candidates
```

Future folders are responsibilities, not empty layers to create pre-emptively. The default application never imports synthetic data; its opt-in preview is code-split.

## Revised comparison lifecycle

1. Resolve a supported event and import its full session offline. Record source versions, access status and file fingerprints.
2. Retain the complete roster and all laps. Each lap has its own phase, timing, eligibility reasons and capability: telemetry, sector_only or unavailable. A missing Q3 lap is absence, not zero.
3. Freeze one event/layout reference independent of the selected pair. Normalize every eligible telemetry lap onto that reference once. Preserve native samples for evidence and supported intervals.
4. Publish the reviewed dataset/index. Review covers source identity, circuit/reference, per-lap checks and method/config; it does not require a human to inspect every combinatorial pair.
5. A user selects two actual lap IDs and requests a result. Validate inventory membership, distinct drivers, eligibility, phase opt-in, capability and current source digest.
6. Return a matching validated cached result. The scaffold currently stops with HTTP 409 on a cache miss; T05 adds calculation from local normalized arrays. A miss never downloads a remote session.
7. T05 executes a bounded local comparison: reuse precomputed alignment, reconcile the pair, build segments/estimated bins/categories/evidence, validate and store an immutable artifact atomically. Blocked results stay in reports.
8. Render the capability-specific result. A telemetry failure may permit a separate sector-only result from trusted recorded timings; never disguise it as a continuous analysis.
9. Export the frozen artifact, current display ordering and its warnings after T10.

## Compute and storage limits

The first implementation uses local files, not a distributed queue. A comparison operates on two prevalidated arrays capped at 5000 grid points. Target <2 s cold local calculation and <500 ms cached response under measured conditions. Set a default capacity of two concurrent calculations per process, deduplicate identical in-flight keys and return a retryable 503 when capacity is exhausted. Do not claim cancellation of CPU work simply because the browser aborts HTTP.

Keep curated publication artifacts read-only and generated cache outputs in a separate writable directory in production. Compute to a temporary file, validate, then rename atomically. Existing immutable IDs never change meaning. T05 introduces a versioned published manifest and updates discovery in the same change; current flat readers must not see a manifest as a comparison JSON.

If measured bounds fail, add an explicit persistent job system in a new decision. Do not silently run unbounded work in a request or introduce an in-memory background task that is presented as durable.

## Identity and reproducibility

A result ID is `cmp_<24 lowercase hex characters>`, derived from canonical JSON including sorted lap IDs, source snapshot SHA-256, reference SHA-256, circuit revision, methodology version, schema version, result tier and analysis-settings hash. Sorting defines stable storage order; `CompareResponse.swapped` preserves requested A/B orientation without recomputing the reference.

Generation UTC is provenance, not a cache key. Full artifact hashes use external sidecars/manifests, not a self-referential digest field. Reimports with changed upstream flags produce a new snapshot and results. All file paths remain operator configuration, never user-supplied route paths.

## Why React and ECharts

React manages forms, state, evidence panels and navigation. Graph quality comes from the plotting layer. The selected layer is **Apache ECharts**, imported directly without an additional React wrapper.

| Option | Fit and decision |
| --- | --- |
| React + ECharts | Selected: linked multi-grid axes, Canvas rendering, annotations and controlled updates fit the reference-style telemetry stack |
| React + uPlot | Strong lean time-series alternative; custom turn/category rails and annotations would require more plugin work for this scope |
| Plotly | Useful scientific explorer; its wider charting surface is unnecessary for this focused workspace |
| Custom SVG traces | Maximum control, but more interaction/axis/accessibility code for an implementation-focused handoff |
| Streamlit/Dash | Useful internal analysis tools; the bespoke responsive two-driver workspace is better served by the existing browser stack |

This is a project fit decision, not a benchmark claim that React or one renderer is universally faster. ECharts supports Canvas and SVG; the scaffold uses Canvas for the trace stack, with a separate SVG map and card renderer. [ECharts renderer guidance](https://echarts.apache.org/handbook/en/best-practices/canvas-vs-svg/), [axis guidance](https://echarts.apache.org/handbook/en/concepts/axis/), [uPlot project](https://github.com/leeoniya/uPlot), [Plotly documentation](https://plotly.com/javascript/).

One ECharts instance contains up to five grids. Every x-axis shares the same distance domain and margins; axis pointers are linked. The turn ruler and local-gain strip use the same transform. Keep a source-supported trace if either driver has that channel; omit a row only when neither has it, and retain the availability reasons. The labelled synthetic preview keeps all four channels. The scaffold implements turn-window/full-lap controls; T07 adds production shared zoom/map/selection state and resolves label collisions for dense circuits. Use previous-value steps for gear/brake and break paths at nulls. No chart smoothing or display interpolation can create evidence.

Initialize once in a React effect, observe size, update options on data/domain changes and dispose on unmount. Do not put every sample into React state. Import only the necessary ECharts components. Lazy-load the chart so the empty session workspace remains light.

## State boundaries

- Remote: session inventory, one lap index, and one immutable result.
- Selection: session, two driver IDs, independently chosen phases/laps, cross-phase opt-in and requested tier.
- View: requested A/B order, distance domain/cursor, selected turn/segment, channel visibility and evidence drawer.
- Derived presentation: pixels, units, labels, sign transforms and category column orientation. Python owns the underlying numbers.
- Export: frozen result plus view metadata, progressing idle → preparing → ready/error.

Abort obsolete reads and ignore late responses. Selection changes invalidate the old result. Keep default selection deterministic: fastest eligible laps within the highest common phase for the chosen two drivers, then explicit overrides. The roster includes eliminated/unavailable drivers with reasons. No browser localStorage telemetry cache.

## HTTP and deployment

Development: Vite on 127.0.0.1:5173 proxies /api to FastAPI on 127.0.0.1:8000. Production: one Python service plus static browser assets, reviewed datasets mounted read-only, a separate writable result cache, and no upstream source credentials on ordinary serving paths.

Current endpoints are health, catalogue, artifact read, session inventory, lap index and cached compare POST. The POST only selects local validated results now; the numerical engine remains T05. No public upload, arbitrary URL fetch, account, live timing stream, or scheduling service is part of this scope.

Targets to measure: catalogue/index <200 ms server time; cached comparison <500 ms; local cold comparison <2 s; compressed artifact <1 MB; cursor update <16 ms median on a documented test device; 1080×1350 export <3 s. These are acceptance targets, not scaffold measurements.

## Revision record

Revision 2 implements the user's expanded request. It replaces the four-driver/prepared-pair limit with full-session inventory and local on-demand comparison, adds independent qualifying phases, two capability tiers, turn rails, estimated mini-sectors, class analysis, and ECharts. It preserves official timing authority, raw delta, reference symmetry and supported evidence. All T01–T12 dependencies remain explicit in the implementation plan.
