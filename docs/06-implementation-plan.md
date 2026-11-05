# Implementation tickets and coding handoff

Execute one ticket at a time. All tickets below are **not started** except T00. Each ends in a working, checked change and a separate pushed commit. Dependencies are gates, not suggestions. A failed data gate stays visible; do not mark it complete because code exists.

## Status board

| ID | Deliverable | Depends on | Target day | Status |
| --- | --- | --- | --- | --- |
| T00 | Blueprint, typed API, empty workspace, CI | — | Setup | Complete |
| T01 | Pinned FastF1 adapter and reproducible import | T00 | 1 | Not started |
| T02 | Qualifying eligibility and selection report | T01 | 2 | Not started |
| T03 | Frozen reference and circuit profile | T02 | 3 | Not started |
| T04 | Alignment, delta and reconciliation | T03 | 4 | Not started |
| T05 | Segments, evidence and artifact promotion | T04 | 5 | Not started |
| T06 | Catalogue selection and comparison state | T05 | 5 | Not started |
| T07 | Synchronized telemetry views | T06 | 6 | Not started |
| T08 | Track map and shared selection | T07 | 7 | Not started |
| T09 | Corner table, findings and quality details | T08 | 8 | Not started |
| T10 | Share links and PNG/JSON export | T09 | 8 | Not started |
| T11 | Three-circuit data and integration pack | T10 | 9 | Not started |
| T12 | Release packaging and final verification | T11 | 10 | Not started |

## T00 — Existing foundation

Implemented: repository configuration, Python package with health/catalog/artifact reads, structural Pydantic validation, generated contracts, strict TypeScript build, live catalogue status in the honest no-data page, source research, CI workflow and this blueprint. Unit fixtures are artificial and isolated from the application. No ingestion CLI, numerical pipeline, plots, observations, export or deployment exists yet.

The schema carries planned analytical fields but does not independently prove analytical validity. T04/T05 introduce the publication validator. A schema-valid JSON is not automatically a reviewed dataset.

## T01 — Import one supported session

**Read:** methodology §§2–4 and sources; operations import conventions. **Files:** `services/api/src/lapdna/ingestion/{adapter,snapshot}.py`, `cli.py`, `services/api/tests/test_ingestion.py`, `services/api/requirements-data.lock`, data documentation.

Implement `load_session(spec: SessionSpec, cache_dir: Path) -> SessionSnapshot` behind a `FastF1Adapter`. `SessionSpec` contains circuit ID, season, resolved event round and `session_type='Q'`. Resolve candidate event name with the source schedule once, then persist numeric round. Do not choose driver pairs yet.

1. Install the optional data dependencies in a controlled environment, resolve compatibility against FastF1 3.9.2, and freeze a separate data lock; preserve the small core lock. Inspect the installed public cache/auth/load APIs. Version 3.9.2 access requirements must be handled explicitly.
2. Implement `python -m lapdna.cli import-session --circuit monza --year 2024 --event "Italian Grand Prix" --session Q`. Command names in this plan are target interfaces; they do not exist in T00.
3. Load laps, native car streams, native position streams, qualifying phase metadata, circuit markers, weather and race-control information. Check source channel presence before processing.
4. Snapshot per-lap metadata and per-driver channels with explicit UTC/session clocks and original row order. Store local parquet tables plus a JSON manifest; add/pin a parquet engine only in this ticket. No pandas object pickle in published artifacts.
5. Manifest includes source/package versions, resolved identity, source field inventory, row counts, timestamps, local file SHA-256 values, authentication result without credentials, and import status. Use temporary output and atomic rename. Avoid re-download when a matching valid snapshot exists; `--refresh` explicitly obtains a new snapshot.
6. Distinguish unsupported event, missing telemetry, upstream unavailable/authentication required, invalid snapshot and filesystem failure. Exit nonzero with an actionable message; redact secret-bearing exceptions.

**Checks:** adapter tests use a fake upstream object with missing-channel/auth-failure cases, not network; one real Monza candidate imports locally or the genuine access blocker is documented. A second import reuses the valid snapshot. Inspect the manifest for secrets and correct version/identity. **Done:** real data access and supported API behavior established; no invented sample substituted. **Commit:** `Add cached qualifying session import`.

## T02 — Select comparable laps

**Read:** methodology eligibility table. **Files:** `selection/{eligibility,laps}.py`, CLI `list-laps`, tests with explicitly synthetic rows.

Implement `evaluate_laps(snapshot) -> list[LapEligibility]` and `choose_laps(report, phase, driver_numbers) -> dict[str, LapId]`. Retain all rejection reason codes per lap, not just the first. Phase comes from FastF1's supported phase split, not an assumed time window. Required metadata unknown → ineligible. Apply the exact deleted/generated/accuracy/pit/track-status/tyre/weather policy in the methodology. A fastest candidate that fails must not be silently used; choose the next eligible lap and show why.

Add `list-laps --snapshot <manifest> --phase Q3 --output data/reports/...json`. The report includes lap timing, sectors, tyre compound/life, phase, eligibility flags, source sample coverage, rejected reasons and selected fastest lap per driver. Equal times choose lower lap number. Require two different drivers, same event, same phase and compatible dry conditions. Restrict user-facing choices to actual prepared pairs later.

Choose four drivers with complete eligible data in one phase only after inspecting this report. Record the rationale and actual lap IDs in a local seed selection manifest. If Q3 cannot support this, evaluate another common phase or candidate year at the same circuit; document the replacement. The operator must not invent a four-driver set in code before data inspection.

**Checks:** exact eligibility reason coverage, missing/unknown flags, deleted fastest lap fallback, equal-time tie, mixed-phase refusal, missing sectors, pit and generated laps. **Done:** reproducible four-driver selection or explicit reason the seed cannot be used; one intended close pair identified from measured times. **Commit:** `Add qualifying lap eligibility and selection`.

## T03 — Freeze the reference and reviewed circuit profile

**Read:** methodology §§4–6. **Files:** `alignment/{native,reference,distance}.py`, `config/circuits/<id>/<revision>.json`, circuit profile validation tests.

Implement `prepare_native_lap(snapshot, lap_id) -> NativeLap`, `build_reference(native_laps, profile_spec) -> ReferenceProfile`, and `integrate_distance(native_lap) -> DistanceTransform`. Use the methodology's deterministic reference selection, independent of pair A/B ordering. Preserve original channel rows and support intervals. Insert lap boundaries only through bracketing; reject missing coverage and conflicting duplicate timestamps. Integrate speed in m/s against elapsed seconds; use no XY path integration for the analysis axis.

Freeze reference ID, source digest, approximate reference length, coordinate unit conversion, rotation, map arrays, official sector crossing distances and ordered corner marker locations. Convert FastF1 position units to metres. Ordered projection must disambiguate Suzuka's crossover; do not pick nearest XY globally. Version the profile by event/layout/reference and include a digest.

Author a reviewed nonoverlapping partition of corner/complex windows and complementary straights. Store segment IDs, labels, bounds, kinds, optional group IDs, marker mappings and explicit metric subwindows. These boundaries must come from inspection of actual imported geometry/telemetry, not guessed distances. Circuit config is original analytical annotation with source/review notes, not an uncredited raw-data dump.

**Checks:** analytic constant-speed integration, boundary interpolation, conflicting duplicates, long speed gap, absent position stream, rotation/inverse transforms, ordered marker projection and crossing case; partition ordered, starts at 0, ends at L with no gaps/overlap. **Done:** one reviewed Monza profile and reference fingerprint with diagnostic plot/report; every later comparison reuses it. **Commit:** `Add canonical track reference and segment profile`.

## T04 — Align laps and reconcile timing

**Read:** methodology §§4–5 and 7; verification invariant matrix. **Files:** `alignment/{resample,compare}.py`, `analysis/quality.py`, numerical tests.

Implement `align_lap(native_lap, reference, config) -> AlignedLap`, `compare_laps(a, b, reference) -> ComparisonArrays`, and `reconcile(a, b, reference, official_timing) -> QualityReport`. Build the specified grid once; insert important boundaries and endpoint, deduplicate strictly. Use continuous interpolation only for supported continuous channels, previous-value semantics for gear/brake, and null beyond support. Keep raw elapsed time; never integrate `1/speed` from the resampled display grid or stretch time to match timing.

Compute `delta_ms = B − A`. Record native support counts/gaps, scale deviations and channel missingness. Implement timing metadata checks, individual and pair interior checks, endpoint accounting and calibration labels separately. Exact endpoint agreement is not an accuracy pass for the interior. Evaluate all thresholds in a versioned config; overall severity is the worst applicable check. Ensure pair cancellation cannot hide bad individual residuals.

Add a machine-readable and human-readable validation report. Complete required check-set validation (the wire schema alone cannot establish that required checks ran). Numerical code has no HTTP imports and no filesystem writes; the CLI orchestrates it.

**Checks:** identical arrays, known analytical delta, swap sign/reference invariance, native gap contamination, discrete steps, null support, official-sector perturbation, cancellation, reference calibration, threshold boundaries and no time correction. **Done:** inspect one real pair's raw delta and all residuals; any failed guardrail remains visible and blocks publication. **Commit:** `Add distance alignment and timing reconciliation`.

## T05 — Build supported findings and promote an artifact

**Read:** methodology §§6–8; schema; architecture identity rules. **Files:** `analysis/{segments,metrics,evidence,observations,publication}.py`, CLI `build-comparison` and `publish`, tests and fixture manifests.

Implement `summarize_segments(comparison, profile)`, `measure_evidence(native_a, native_b, aligned, profile)`, `generate_observations(evidence, config)` and `validate_for_publication(artifact, review_record)`. Define metric evidence and uncertainty intervals exactly as the methodology. Segment gain is end delta minus start delta; all partition gains telescope to the final raw gap. Boundary sensitivity is a deterministic robustness check, not a statistical confidence interval.

Use the existing three template categories with explicit versioned variants; select at most three distinct eligible intervals. Require the native support, materiality and sensitivity checks. Every number in a sentence must resolve to structured evidence. Published text names actual driver codes/names, not positional A/B slots, so a later display swap leaves the claim true without string substitution. If fewer qualify, emit an insufficient-evidence reason. Do not count warnings as performance observations. Verify generated text against data with exact formatting functions.

Create immutable artifact IDs from the canonical input/settings identity. Add an atomic published manifest under `data/artifacts/catalog.json`, containing summaries and artifact digests; change `ArtifactStore` to use it instead of globbing when this ticket introduces it. Keep artifacts in a dedicated subdirectory or explicitly exclude the manifest from artifact enumeration. Validate all referenced artifacts before replacing the manifest. A failed build/promote must preserve the previous usable catalogue. Blocks stay in reports outside served storage; warnings require a recorded review and visible annotation.

**Checks:** full partition accounting, native-vs-grid support, missing brake, overlapping onset intervals, threshold recovery, sensitivity sign reversal, tie ranking, three/fewer findings, duplicate IDs, deterministic outputs, corrupt artifact rejection and atomic promotion failure. **Done:** one real reviewed comparison served by API, with explicit source and residual report. **Commit:** `Add segment evidence and comparison publication`.

## T06 — Select and load a prepared comparison

**Files:** `apps/web/src/features/comparison/`, `api.ts`, `App.tsx`; add Vitest + React Testing Library as development dependencies and pin lock changes. **Read:** UX states and contracts.

Replace the scaffold hero with the specified analysis workspace once a valid artifact exists. Derive circuit/session/phase/driver/lap controls from catalogue summaries, with dependent controls reset when their parent changes. Offer only combinations that exist. Use a comparison ID as the canonical URL selection (`?comparison=<id>&swap=1`); default to an explicit first prepared catalogue item by documented sort order, not an assumed driver pair. A/B swap is a view transform that negates displayed delta/gain and exchanges channels/metadata while keeping grid and reference fixed.

Implement a central comparison reducer with loading, ready, limited, empty, unavailable and error states. Abort stale requests, ignore late results and preserve useful selection on retry. Keep official timing summary separate from estimated values. Parse the schema version and reject unsupported payloads. Do not duplicate Python domain types; import generated TypeScript. Runtime checks verify API boundary shape without implementing numerical inference in JS.

**Checks:** empty catalogue, invalid URL, unavailable pair, error/retry, request race, same driver disallowed, eligible override only, reload restoration and double swap identity. **Done:** one real comparison loads with metadata and official sectors; absent charts are explicitly pending until next ticket, not fake visual placeholders. **Commit:** `Add prepared comparison selection`.

## T07 — Synchronize five telemetry panels

**Files:** `features/telemetry/{TelemetryStack,TracePanel,CursorReadout,scales,paths}.tsx|ts`, shared `comparison/view-state.ts`. **Read:** detailed UX cursor/zoom/null behavior.

Use a shared distance domain, dimensions and cursor in one provider/reducer. Draw delta, speed, throttle, gear and boolean brake in SVG; A solid/cyan, B dashed/orange. Break paths at nulls, use steps for gear/brake and label brake on/off. The delta baseline is zero with explicit B−A meaning. Render official sector markers on the same distance scale; label spatial positions approximate.

Pointer movement maps to canonical distance and nearest supported readout; mouse leave behavior follows UX without clearing a pinned segment. Keyboard focus on a distance control changes the same cursor. A region click sets the shared domain with specified padding; reset returns full lap. Use ResizeObserver rather than fixed viewport widths. Keep raw arrays intact; any path simplification is display-only and must preserve gaps/extrema.

**Checks:** shared cursor coordinate on all panels, same distance under resize, null gaps, integer gears, binary brake, pointer/keyboard parity, zoom/reset, axis units and official-vs-estimated wording. Profile one real artifact; avoid one React element per sample. **Done:** all five readable traces at 1440 px and 390 px. **Commit:** `Add synchronized distance telemetry views`.

## T08 — Add the relative-performance track map

**Files:** `features/track/{TrackMap,geometry,picking}.tsx|ts`. **Read:** methodology map coloring and UX selection.

Render frozen reference geometry in SVG with equal x/y aspect ratio, configured rotation and corner labels. Color by partition `gain_ms` using the same neutral threshold and scale as the table; show saturation legend with actual tooltip values. Unknown geometry or unsupported segments have a distinct pattern, not a neutral-performance color. Never color by cumulative delta.

Use segment paths with accessible labels and forgiving hit areas. Clicking a map region pins/selects its canonical interval and updates the telemetry domain. Cursor movement in traces puts a marker at the corresponding reference index. A map hover resolves along its segment's known distance range so Suzuka's crossing cannot select an unrelated branch. Keyboard segment traversal provides the same behavior. Preserve reference after A/B swap; swap colors/sign only.

**Checks:** aspect ratio, orientation, cross-over picking, segment path boundaries, endpoint closure, swap invariance, keyboard selection and missing geometry state. **Done:** selection is synchronized across map/trace and all three layouts are structurally supported. **Commit:** `Add local-performance track map`.

## T09 — Surface the evidence

**Files:** `features/evidence/{SegmentTable,ObservationList,EvidenceDrawer,QualityPanel}.tsx`. **Read:** product truth levels and UX sorting/selection/quality.

Show partition segments in distance order by default with optional absolute-gain ranking. Every row has estimated gain, direction, quality and supported metrics; null is a dash with an explanation. Selecting an observation/table row sets the same pinned segment used by the map and charts. The evidence drawer exposes exact metric definition, values, support and sensitivity; it is not only a repeated prose claim.

Show up to three observation cards with the insufficient-evidence panel when needed. Implement quality details with timing metadata, individual and pair residuals, calibration labels and endpoint constraint explanation. Reconciliation errors must remain unchanged when users swap drivers; relabel and sign-transform only where appropriate. Warn state stays visible throughout. Blocked artifacts are withheld: the browser shows unavailable/reason with no findings/export; the operator report retains official metadata.

**Checks:** all evidence refs resolve, selection round-trip, sorting ties, no duplicate wrapped-complex counting, fewer-findings state, keyboard table access, focus-return from drawer, warn/block behaviors. **Done:** reader can verify every displayed sentence against its interval and metric. **Commit:** `Add corner summaries and evidence details`.

## T10 — Export a reviewable analysis card

**Files:** `features/export/{AnalysisCard,renderSvg,download,serialize}.tsx|ts`. **Read:** UX export layout.

Build a dedicated 1080×1350 card from the frozen loaded artifact and view order. Include event/phase, driver and lap IDs, official times/gap, local-gain map/legend, the three supported observations or explicit fewer-findings message, quality warning, source credit, method/version and short comparison identity. Draw SVG text/shapes from templates and rasterize to PNG via a canvas. Use local/system fonts and wait for font readiness; avoid remote assets and screenshotting the live browser DOM. Provide JSON evidence/provenance export separately with original raw A/B order plus view-order metadata.

Share URL serialization includes comparison ID, swap flag and optional selected segment. Clipboard failure displays a selectable URL; no silent success. Export failure keeps the workspace usable and displays a retry. A blocked comparison cannot export a performance card. Never regenerate analysis while rendering an image.

**Checks:** image dimensions, long driver/segment labels, line wrapping, warning footer, 0/1/2/3 observations, swapped order correctness, no clipping at 100% image inspection, no network/font dependency, JSON round-trip and clipboard failure. **Done:** downloaded PNG matches the shown evidence and companion JSON. **Commit:** `Add analysis card and evidence export`.

## T11 — Validate all three circuits

**Files:** remaining circuit configs, reviewed dataset manifests, non-bundled acceptance corpus, browser integration tests. **Read:** verification release checklist.

Repeat import/reference/selection for Silverstone and Suzuka, inspecting layout/version and source availability each time. Prepare at least four drivers and all six pairs per circuit in one eligible phase (18 minimum total). Reuse the same engine; no circuit-name branches in numerical code. Circuit-specific differences belong in versioned profiles. Choose one showcase pair per circuit that supports three distinct observations; document quality limitations for every pair.

Build the validation pack: close pair, wider-gap control pair and rejected-lap example per circuit, official classification/sector source links, native sample/gap summaries, all residuals, profile inspection and evidence review. Add exact known numerical regression assertions from reviewed local results with clear source provenance, but do not commit raw upstream data without resolving distribution terms. CI continues using synthetic tests; real acceptance is a separately documented command and locally available corpus.

**Checks:** all 18 artifacts schema + analytical validation; official timing cross-checks; all observation numbers reviewed; Suzuka branch mapping; circuit switches; public export source labeling; no mixed phase/weather pair. **Done:** three circuit datasets are actually validated, not merely listed in a dropdown. **Commit per circuit:** `Add validated Silverstone circuit profile` / `Add validated Suzuka circuit profile`, then `Add three-circuit acceptance checks`.

## T12 — Package and release

**Files:** Dockerfile/runtime config, operations notes, CI browser job if added, final handoff. Implement same-origin static serving and `/api` routing, readonly artifact volume, process health, safe errors, bounded reads, compression/cache headers, immutable artifact caching and catalogue revalidation. Keep port/API/paths configurable. Test restart with existing artifacts and no upstream network.

Run the final checks in verification on clean install. Capture responsive and keyboard QA, download/inspect exports, measure target budgets with named conditions, and record source distribution scope. Confirm empty/corrupt catalogue behavior in the deployment image. Keep any source/account secrets in the runtime secret mechanism, never the browser bundle or Docker layers. Publish only when release checks are fulfilled and record the actual deployed URL in operations; no deployment is part of T00.

**Done:** reproducible documented build, usable release with three circuits and export, known limitations visible, no failing required checks. **Commit:** `Package the first LapDNA release`.

## Later extension: corner-profile clustering

Do not start before T12. Proposed experiment: normalize speed/throttle/gear/brake profiles within reviewed corner windows, retain duration/length separately, scale features using training data only, cluster comparable corner types and inspect stability across sampling/parameter choices. Avoid presenting a cluster as a driver skill label or causal diagnosis. The evaluation question is whether clusters reveal repeatable observable shapes beyond simple corner-speed bins. This is an experiment with its own acceptance plan, not an unfinished MVP requirement.

## Copyable implementation prompt

> Work in the LapDNA repository. Read AGENTS.md and docs/10-handoff.md. Implement only ticket T01 from docs/06-implementation-plan.md and its named dependencies/specifications. Keep the architecture and methodology fixed. Run the listed checks, update ticket status and handoff with evidence, then commit and push the bounded feature to the configured GitHub branch using a descriptive imperative message. If an upstream assumption fails, record the exact issue and the smallest required decision; do not fabricate data or silently redesign the project.

Replace `T01` with the next uncompleted ticket for later sessions. The implementation model should not infer completion from this prompt; the status board and recorded checks govern.
