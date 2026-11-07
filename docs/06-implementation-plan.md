# Implementation tickets

T00 is the runnable scaffold. T01–T12 are implementation work. Take the first unfinished ticket whose prerequisites passed, run its checks and record actual results in the [handoff](10-handoff.md). A ticket may contain multiple small verified features. Commit and push each independently usable change as it passes. The two-week schedule assumes source access and suitable real sessions.

**User priority update, 7 November:** [R01 recorded results first](16-results-first-milestone.md) precedes the telemetry tickets. It imports final phase/session bests, event-specific driver/team records and same-phase comparisons across available years. Individual runs/laps are explicitly deferred to R02, which resumes T01/T02 before numerical telemetry work. Do not mistake classification ingestion for completion of T01.

**Approved follow-up:** [UI and scope decision](17-approved-ui-and-telemetry-rollout.md): A sports-editorial landing, G1 stacked overlays, detailed telemetry limited to verified sessions/channels in 2018–2026, older timing comparisons preserved. The three original circuits are validation pilots before all source-supported events/layouts. U01 is the interface checkpoint; it does not satisfy T01 or real telemetry acceptance.

## Status board

| Ticket | Deliverable | Requires | Day | Status |
| --- | --- | --- | --- | --- |
| T00 | Contracts, local selection boundary, synthetic chart preview and source probe | — | Setup | Complete |
| U01 | Approved landing and compact recorded-results studio | R01 | UI | In progress |
| T01 | Pinned FastF1 session import | T00 | 1 | Not started |
| T02 | Full qualifying roster, actual phase/lap inventory and eligibility | T01 | 2 | Not started |
| T03 | Frozen reference geometry, turn markers and reviewed windows | T02 | 3 | Not started |
| T04 | Offline lap normalization, raw delta and reconciliation | T03 | 4 | Not started |
| T05 | Local pair resolver, two result tiers, findings and cache | T04 | 5 | Not started |
| T06 | Production driver/phase/lap selection | T05 | 5 | Not started |
| T07 | Synchronized real telemetry, turns, minisectors and sector fallback | T06 | 6 | Not started |
| T08 | Performance map linked to shared distance | T07 | 7 | Not started |
| T09 | Category analysis, corner/straight ranking and evidence | T08 | 8 | Not started |
| T10 | Shareable comparisons and PNG/JSON cards | T09 | 8 | Not started |
| T11 | Three pilot inventories, then verified 2018–2026 session/layout expansion | T10 | Pilot day 9; archive separately scoped | Not started |
| T12 | Release packaging and verification | T11 | 10 | Not started |

## T00 — Existing foundation

The API exposes health, sourced year/calendar metadata, session inventory, session laps, prepared artifact catalogue/lookup and a local selection POST. Contract v1.2.0 distinguishes telemetry and sector-only results and requires per-driver native-channel provenance. Calendar navigation starts with the current year, then a real race, then its studio. The selection path validates a request, enforces cross-phase opt-in and finds an existing compatible artifact. A valid uncached selection gets an explicit preparation error. The React workspace reads inventory, selects actual indexed laps/phases and renders supplied cached artifacts through a chart, sector-only view or evidence panels as appropriate. A separate labeled synthetic ECharts preview preserves all four channels and runs without an import. See [contracts](05-contracts.md) for the current routes and shapes.

The [historical source probe](09-sources.md) checked OpenF1 availability for one Monza driver/lap. The first real FastF1 import, pair computation, public-data comparison view, results and exports belong to the tickets below. Synthetic examples and schema checks cannot satisfy real-data acceptance gates.

## T01 — Import one supported session

Read [methodology §§2–4](03-telemetry-methodology.md), the [source register](09-sources.md), [20-source audit](13-data-source-audit.md), [field inventory](15-data-points-and-rollout.md) and [operations](08-operations.md). Implement `ingestion/{adapter,snapshot}.py`, `cli.py`, the data dependency lock and offline adapter tests in the API package.

1. Resolve the candidate 2024 Italian Grand Prix conventional qualifying session from the schedule. Persist the actual round, layout and source identity. Implement `load_session(spec, cache_dir) -> SessionSnapshot` and the documented `import-session` command.
2. Verify the installed FastF1 3.9.2 cache configuration, supported authentication flow and load APIs. Pin compatible optional dependencies, including a parquet engine, in a separate data lock. Keep credentials and raw caches outside Git.
3. Load all participants and laps, phase/session status, timing/validity fields, native car and position streams, circuit markers, weather and race-control data. Preserve native clocks, ordering, units and nullable fields.
4. Write an immutable snapshot and manifest atomically. Include source version, resolved event, fields, counts, UTC, digests and sanitized access status. Reuse a valid matching snapshot; an explicit refresh creates a revision. Distinguish authentication, unsupported/missing data, transient service and filesystem errors.
5. Preserve raw field presence and native missing-row masks before accepting library-filled zeros/False. Pinned FastF1 can fill absent car rows and default absent DRS channel 45 to zero; such values are unavailable, not measured off states. Test these cases. Never infer throttle, gear or brake from speed. Populate per-driver channel provenance only after these checks.
6. Preserve weather-field presence and speed-trap update/fill lineage; missing weather can become zero/False and trap fields can be carried forward. Mask documented throttle sentinel 104 instead of clamping it. Verify coordinate units per provider/year, including older seasons. Retain optional source fields without promising a new public graph. If freshness/presence cannot be established, disclose it rather than infer it from plausible values.
7. Preserve the position stream's native missing-row mask: the pinned parser can insert XYZ=0 and Status=OffTrack for absent records. These must not become geometry points or an actual off-track claim. Test the map-origin-jump and default-status cases separately from legitimate source coordinates/statuses.

**Gate.** Offline tests cover success, missing/defaulted car and weather fields, inherited trap values, throttle sentinel, unit handling, auth failure, duplicate import and interrupted write. Perform one real import and inspect its secret-free manifest with actual field coverage. An access failure leaves T01 open with the exact blocker and reproducible command. The OpenF1 availability probe cannot close this gate. Suggested commit `Add cached qualifying session import`.

## T02 — Index drivers, phases and actual laps

Implement `evaluate_laps(snapshot)`, `build_session_lap_index(report)` and a deterministic selector in `selection/`. Write the schema-defined session index and a more detailed operator report. The index includes every participant, including a driver with zero selectable laps. Determine phase from FastF1's supported session split, retaining missing/cancelled phases explicitly in the report. Retain unassignable records in the report with reasons; an ambiguous event phase split prevents publishing that event.

For every known-phase lap, store its immutable ID, driver, Q phase, lap number, recorded lap/sector times, capability and exclusion reasons. Apply methodology §3.2. A timing-ineligible lap is unavailable. A timing-eligible lap with insufficient telemetry can be sector-only. Preserve supporting metadata and native-coverage diagnostics for subsequent stages. Final capability incorporates T03/T04 quality checks. Display eliminated/absent Q phases as having no selectable laps.

Two different drivers must share the imported event/layout. Default to the highest common eligible phase, then fastest eligible lap per driver, breaking ties by lap number. Allow either driver to override to any actual eligible lap in their selected phase. Different phases require explicit opt-in and a warning with both phase labels, lap-start separation and relevant tyre/weather context. If no common phase exists, require deliberate independent selection. Cross-phase opt-in never overrides a validity/conditions rejection.

**Gate.** Verify roster and source counts, repeated laps in one phase, deleted fastest lap, ties, eliminated driver, driver with no eligible lap, unknown phase, cancelled Q3, sector-only capability, same driver/foreign lap rejection and cross-phase allowed/denied. List all laps with `list-laps`; optional phase filter must preserve the full persisted index. Suggested commit `Index qualifying laps by driver and phase`.

## T03 — Freeze the reference and review circuit windows

Implement `prepare_native_lap`, `integrate_distance` and `build_reference` under `alignment/`. Sort eligible candidates once as in methodology §4. Freeze the first reviewed usable reference and record fallback decisions. Bracket timing boundaries with native samples, reject conflicting timestamps and integrate speed on the native clock. Convert position to metres and use ordered marker projection across crossovers. Store reference ID, source/config hashes, length, geometry, rotation, sector crossing estimates and each marker's ID, number, lettered label and distance.

Review and version the circuit profile under `config/circuits/`: disjoint corner/complex regions, complementary straights, constituent turn-to-region links, lap-wrap group IDs and native reference apex neighborhoods for speed classification. These are authored from the actual source, with inspection notes. Insert turn/sector/region and 100 m bin boundaries into the planned grid in T04.

**Gate.** Compare constant-speed integration with a closed-form answer, test bracketing/gaps, duplicate timestamps, coordinate conversion, ordered crossover projection and full partition coverage. Inspect and sign off Monza geometry, each turn label and apex window. Swapping the two selected laps cannot change the reference. Suggested commit `Add canonical track reference and reviewed turn windows`.

## T04 — Normalize eligible laps offline and reconcile timing

Implement `align_lap(native, reference, settings)`, `compare_laps(a,b)` and `reconcile(a,b,reference,timing)` under `alignment/` and `analysis/quality.py`. Build one canonical grid with endpoints, markers, region/sector boundaries and the second 100 m partition. Normalize every timing-eligible lap with available telemetry once at import/preparation time. Persist content-addressed aligned arrays, native support data/intervals required by T05, selected timing metadata and per-lap diagnostics. Pair-independent preprocessing scales with lap count. Record reduced capabilities and reasons in the inventory.

Use continuous interpolation for supported continuous quantities and previous-value samples for discrete gear/brake. Preserve nulls and raw elapsed time. Compute B−A in ms. Grade both laps' timing consistency, individual and pair interior residuals, reference calibration, endpoint constraint, scale factors and support gaps separately per methodology §§4–5,7. A telemetry failure can still permit sector-only output if the independent timing checks pass. A timing failure blocks both.

**Gate.** Run analytical identity, known delta, A/B sign swap, equality of shared grids, gap, discrete step, perturbed official sector, reference calibration and pair cancellation tests. Inspect one real pair's raw curve and individual residuals. Re-normalizing the same revision reproduces arrays. A pair request after T05 must never call this preparation step. Suggested commits `Normalize qualifying laps on the reference distance grid`, `Reconcile raw telemetry against recorded sector timing`.

## T05 — Resolve any eligible local pair and produce supported findings

Read methodology §§6–8, [contracts](05-contracts.md) and [architecture](02-architecture.md). Implement independent features in `analysis/` plus the existing session/artifact stores and CLI. Keep the signatures pure up to the cache/publication boundary.

1. `summarize_segments(aligned,profile)` and `build_estimated_minisectors(aligned,profile)` produce **two separate partitions**. On each supported interval use end delta minus start delta. Insert each 100 m edge plus L, preserving a shorter final bin, null intervals and source `derived_telemetry`. Never add a bin total to a corner total. Tests cover exact multiples, remainder, gap masking, independent telescoping and slot swap.
2. `classify_reference_corners(profile,native_reference,settings)` runs once per frozen profile during preparation, caching its result. Classify each marker by its supported native minimum in the reviewed apex window: low below 150, medium 150 to below 250, high at least 250 km/h. Use the support/boundary-shift tests in §6.6. Retain unknown/mixed cases explicitly. `aggregate_corner_classes(segments,evidence,classes,settings)` counts linked pieces as one unit, aggregates gross A/B gain, net, coverage, win/neutral counts, sensitivity and evidence IDs. Apply the §6.7 gates before emitting a directional or exclusive pattern. Test exact cutoffs, reference stability under arbitrary A/B and swap, opposing contributions, cancellation, partially supported wrap groups, no class members and limited coverage.
3. `measure_evidence` uses native observations. `generate_observations` ranks distinct supported regions using prescribed sensitivity and materiality checks. Link each fact to source values, bounds and support. Include up to three regional observations plus the separate category analysis. Use the actual driver names, units and contextual warnings. Test 0–3 observations, duplicate regions, unsupported brake events and deterministic wording.
   Optional LLM wording is a later independent extension, specified in [analysis generation](14-analysis-generation.md). It consumes validated evidence, keeps comparison/method/source identity and cannot replace numerical computation or required warnings. The current renderer reads saved text; it does not call a model.
4. Implement `build_sector_result` from eligible recorded timings only. Emit local and cumulative sector gaps, lap metadata, fallback reason, source and pairing context. For `detail_level=auto` use the best eligible **computed** tier, falling back only for real data-quality limits. An explicit telemetry request may fail with the documented capability reason. Test missing timing, telemetry block, exact S1/S2/S3 arithmetic, and the absence of distance, corner and observation fields.
5. Extend `POST /api/v1/compare` to compute a cache miss from the two selected local normalized laps/timings. No source API, downloads or full-session parsing on this path. Resolve exact indexed IDs, opt-in and context first. Use canonical unordered lap identity plus dataset, reference, method, settings and tier; return the existing orientation flag. Bound work by allowed IDs, array length, file sizes, concurrent builds and cache limits. Deduplicate identical in-flight requests; a retry or swap reuses the result. Persist via temporary validated write and atomic rename. Keep persisted shareable artifact IDs resolvable according to the retention policy in [operations](08-operations.md).
6. Validate each newly built artifact's schema, analytical provenance, quality and evidence references before serving it. Publish reviewed session revisions and curated artifacts through an atomic manifest switch. Keep blocked results in operator reports, show warnings in browsable results and review designated shareable examples. An errored or changed source revision cannot replace the last usable published session.

**Gate.** Start with a real normalized session and two eligible laps absent from the cache. Offline, the first request yields the correct result, repeated/concurrent/reversed requests reuse it, a different actual pair computes independently, and invalid requests perform no build. Exercise sector-only, no eligible timing, interrupted write, revision-key change, capacity limit and restart. Inspect one real candidate's curve, regional/category evidence and residual report. Suggested commits `Calculate local gains and estimated minisectors`, `Summarize supported corner speed patterns`, `Generate evidence-backed lap observations`, `Resolve qualifying comparisons from local session data`.

## T06 — Wire production session and lap selection

Read [UX](04-experience.md) and contracts. Extend the existing `apps/web/src/features/comparison/` inventory browser, selector and result adapter. Its session/laps GETs and selection POST already use exact IDs and the generated contracts. Connect them to T05's cold-build and bounded-load responses. Validate existing fastest-common-phase defaults, independent phase controls, overrides, reduced capabilities and contextual warnings against the full real inventory. Reserve the preview for its explicitly labeled entry point.

Use a reducer for selection, loading, ready telemetry, sector-only, insufficient/unavailable data and transport error. Abort stale fetches and reject late responses. Route returned immutable comparison IDs with orientation and optional segment. Respect the returned `swapped` flag before rendering signed values. Preserve the reader's selection on retry and URL reload.

**Gate.** Test eliminated Q3, no shared eligible phase, cross-phase confirm/cancel, explicit slower eligible lap, invalid/deep-linked IDs, empty index, stale response, retry and double swap. Open one real result of each available capability through the normal selection path. Suggested commit `Connect the analysis workspace to qualifying lap selection`.

## T07 — Synchronize the production trace board

Reuse `features/telemetry/{TraceBoard,SectorPoints,view}` and the comparison result adapter. Validate the existing cached-artifact rendering against T05 results. Use one Apache ECharts Canvas instance with linked distance grids. Verify the derived 100 m dominance strip, S1/S2/S3 guides, numbered/lettered turns on the same x ruler, speed, throttle, gear steps, brake On/Off and B−A delta panel with zero baseline. Finish turn visibility and selection through zoom, reflow and label collisions. Show the actual ruler location and linked selectable turn list even when labels are thinned.

Keep cursor/pin/zoom in shared React state. Use one keyboard distance control, text readout, resize handling and clickable turn/region controls. Gaps stay empty; retain A/B stroke distinctions and axis units. Sector-only results go to `SectorPoints` and a values table with three discrete official boundary comparisons; hide every spatial plot/turn-local claim in this tier.

**Gate.** Verify all grid guides align on desktop and mobile, pointer/keyboard readouts agree after resize/zoom, zero and unknown bins differ, brake stays binary and sector-only has no interpolated line. Profile cursor interaction on a real artifact. Suggested commit `Render synchronized qualifying telemetry and turn deltas`.

## T08 — Link the local-performance map

Render frozen reference geometry in SVG at equal scale with rotation, start/finish and numbered corners. Default to reviewed corner/straight region gains, offer the separately labeled estimated-minisector layer. Distinguish unknown, neutral and both gain directions, with actual numeric tooltips. Use the known distance range for branch-safe picking at Suzuka. The shared cursor, pinned turn and region zoom update map, chart and list; offer keyboard equivalents. Hide the performance map for sector-only comparisons.

**Gate.** Test both map modes, closure, geometry gaps, crossover picking, zoom/reset and swap without moving the geometry. Inspect at all three viewport sizes. Suggested commit `Link the performance map to telemetry distance`.

## T09 — Show comparison-specific analysis and evidence

Extend the existing class/observation display with region ranking, linked evidence drawer and quality details in `features/evidence/`. Keep the disjoint region table in distance order with sortable absolute gain. Render low/medium/high rows with thresholds, included/expected units, distance coverage, both gross values, net, assessment, members and evidence links. Surface mixed/unknown complexes, absent classes, opposing units and cross-phase context. Render the Python-authored tailored interpretation and up to three local observations. Provide a reason when fewer qualify. Avoid deriving patterns in JavaScript.

**Gate.** Test default, sparse and contradictory member patterns, linked wrap, missing member, no findings, drawer focus, warning visibility and correct A/B interpretation. Selecting a member or local observation must open its measured region in the map/traces. Sector-only keeps only official timing analysis. Suggested commit `Add corner class analysis and regional evidence details`.

## T10 — Export and restore a comparison

Build a dedicated 1080 × 1350 PNG card from the loaded artifact plus view order, with a separate JSON download preserving original A/B and evidence. Show event, both driver/phase/lap identities, official times/gap, source and methodology version, quality/context warnings and ID. A telemetry card includes local-performance visual, supported category pattern and qualifying observations. A sector-only card identifies its tier and uses the three official boundary values. Use local fonts and deterministic SVG-to-canvas export. Link to the immutable comparison ID, orientation and optional region. Expose a selectable URL on clipboard failure.

**Gate.** Download and inspect at full and half size. Test sector-only, cross-phase warning, 0–3 findings, long labels, swapped view, unavailable export, JSON round-trip and copied URL restoring exact laps. Suggested commit `Export shareable qualifying analysis cards`.

## T11 — Validate three complete session inventories

Repeat T01–T05 for Silverstone and Suzuka. Validate the entire source roster, phase availability and every actual known-phase lap's capability/reasons. Use the common engine and reviewed layout profiles. Run automated integrity checks for every imported lap and every returned comparison. Do not precompute or manually review the Cartesian product of laps.

Build the [representative acceptance matrix](07-verification.md) across the three real sessions. Cover close/wide controls, default and overridden lap selections, phase elimination, cross-phase opt-in, tier failures and cache-miss behavior. Verify selected real lap/sector values against the correct FIA rows. Choose one curated telemetry comparison per circuit with three legitimate distinct observations when supported. If data cannot support an advertised case, record the missing case and use another real qualifying event at that circuit or keep the release gate open. Synthetic rejection tests can cover unavailable edge cases if explicitly identified.

**Gate.** Three actual complete inventories load, all roster/lap counts reconcile, repeat selections hit cache and new valid pairs compute locally, validated examples resolve to evidence and reviewed turn geometry, and no published tier overstates verification. Commit each completed circuit profile/validation increment separately.

## T12 — Package and release

Implement same-origin Vite/static and FastAPI serving, health, read-only session input mount and bounded writable result/cache storage. Permit GET and the validated local comparison POST. Separate operator imports, reviewed manifests and web process. Keep upstream credentials out of the serving environment. Test warm/cold access, network-disabled operation, cache limits, concurrent requests, restart, previous-manifest recovery and immutable published share links.

**Gate.** Run every [release check](07-verification.md) on clean installs, record performance and responsive/keyboard/export evidence, source distribution scope and known limitations, then document the actual deployment target. Suggested commit `Package the first LapDNA release`.

## Later experiment

After release, evaluate clustering of normalized corner profiles against the fixed reference-speed categories. Keep feature definitions, comparable windows and stability evaluation in a separate ticket. A cluster describes an observed profile shape.

## Implementation handoff

Use the [handoff](10-handoff.md) and the selected ticket as the work order. Include the inputs, outputs, tests, gate, source limitations and separate commits for each completed feature. When upstream access or validation fails, retain the evidence and report the precise blocker.
