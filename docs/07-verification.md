# Verification and release gates

The aim is an analysis that remains honest when its inputs are incomplete. A green build proves neither real-data access nor numerical accuracy. Record those conclusions separately.

## Checks that run now

From the root, after the README setup:

```powershell
.venv\Scripts\python -m pytest services/api/tests
npm run contracts:check
npm run typecheck
npm run build
```

The Python tests cover empty/valid/corrupt/unknown artifacts, request IDs, unsafe paths, blocked publication, finite values, discrete channel types, aligned array lengths, arithmetic/references, complete reconciliation records and segment partitions. Test data is an artificial three-point contract fixture; it is not a numerical model of a real lap. Current checks do not contact FastF1.

`requirements.lock` pins the verified core/test environment. A Starlette TestClient deprecation notice about httpx is currently non-fatal; document it rather than suppressing all warnings. Change the dependency only in a separate verified maintenance step if required. CI runs the same tests and web build on Ubuntu/Python 3.11/Node 24.

## Numerical invariants to implement

Use small synthetic arrays with analytically known answers, plus reviewed real sessions outside network-dependent CI. Required cases are enumerated in methodology §9; this is the acceptance interpretation:

1. **Identity:** two equal input laps produce zero delta and gains; no invented findings. Use pure numerical functions for same-driver identity tests; the public two-driver wire contract correctly rejects comparing one driver with themselves.
2. **Orientation:** swapping A/B negates delta/gains and exchanges evidence values without changing reference, grid, geometry, segment bounds or absolute ranking. Swapping twice restores the initial view.
3. **Accounting:** partition gains sum to final minus initial raw delta within `1e-6 ms` numerical tolerance; this tolerance is an arithmetic check, not a claim of physical accuracy.
4. **Sampling:** increasing the display grid density cannot increase native support counts or change eligibility. Constant-speed integration agrees with a closed-form calculation.
5. **Missingness:** a large speed gap invalidates downstream distance integration and blocks the lap. A brake-only hole suppresses brake evidence while retaining supported speed/time. Unknown is never false/zero.
6. **Clock:** elapsed time uses official lap start and bracketing native samples. Missing coverage cannot be repaired by extrapolation. Zero endpoint residual remains labeled as constrained by timing boundaries.
7. **Reconciliation:** perturb only official sector metadata; raw curve must remain unchanged and diagnostic severity change. Large individual errors that cancel in the pair still fail.
8. **Regions:** boundaries lie on the grid, form a partition, and obey wrap/complex grouping rules. Sensitivity sign changes suppress directional claims.
9. **Evidence:** every observation is reproducible from source metrics and threshold settings. Sparse samples, overlapping onset intervals, null metrics and unresolved braking episodes suppress relevant templates.
10. **Reproducibility:** identical source/reference/settings hashes yield identical numeric arrays, segments and observation IDs; exclude operational generation timestamps from deterministic content comparisons.

Use threshold boundary cases just below, at and above each cutoff. Avoid tests that merely duplicate a function's internal formula without an independently constructed expected result.

## Real-session acceptance pack

For each circuit, keep a locally reproducible validation pack with one close pair, one wider-gap control and a rejected lap. Record source event/phase/lap IDs, official classification and detailed timing links, retrieval date, source package version, pipeline commit, profile/config hash, native sample statistics, distance scales, all reconciliation records and review notes. Include raw diagnostic plots and exported cards. Label missing external sector documents as feed-only verification.

At least four eligible drivers and six unordered pairs are prepared per circuit. A successful sample pair does not validate every other pair: run the full publication validator on every artifact. Three showcase pairs (one per circuit) must support three legitimate observations; other pairs can contain fewer findings with a reason. Never lower a cutoff merely to fill a slot.

Review geometry visually with corner numbers and the timing line. Suzuka must pass the crossover association check. Segment windows must correspond to the configured braking/turn/exit regions on the reference; they are approximate analytical windows, not exact official corner timing splits.

## Interaction acceptance

Test desktop 1440×900, tablet 768×1024 and mobile 390×844, plus zoomed text. Requirements after T06–T10:

- Empty catalogue and API failure are distinct; retry works. An obsolete URL does not select a random pair silently.
- Circuit/phase/pair/lap choices only offer prepared combinations. A stale response cannot replace a newer selection.
- Cursor, zoom and segment selection agree across all traces, map, table and observations.
- Null spans are broken traces/hatching; gear/brake remain discrete; legend sign is explicit.
- Shared slider and segment buttons permit keyboard exploration. Focus is visible and returns from dialogs. Color is not the sole driver distinction.
- Official values retain milliseconds; estimated local gains use approximate language and sensible rounding. A warning remains visible during export.
- Long driver names, long segment labels, no findings, missing channels and unusually short/long ranges do not clip the layout.
- Export PNG is 1080×1350, readable at half size, and agrees with companion evidence JSON and current A/B view order.

Browser smoke tests can use a tiny unmistakably synthetic HTTP fixture in tests, never a silent production fallback. Automated screenshot differences do not replace visual inspection of chart semantics and labels.

## Release gates

All of the following are required for the two-week MVP release:

- Clean dependency install, schema drift check, tests, typecheck and production build pass.
- All 18+ artifacts pass schema and analytical publication validation and have a reviewed dataset record.
- Official timing evidence exists and its verification scope is accurately stated.
- All three map configurations and representative cards have been inspected; no unsupported claims appear.
- Independent quality checks remain distinct from timing constraints and calibration.
- No blocked dataset appears as a prepared comparison; warning datasets retain visible warnings.
- No secrets, user credentials, local machine paths or raw upstream caches appear in Git, generated client assets or exports.
- Source distribution scope, package notices and data attribution are recorded before public hosting.
- Production starts without contacting upstream; artifact persistence/restart and previous-manifest recovery work.
- Measured performance and remaining limitations are recorded in the handoff.

Do not broaden a completed ticket's testing endlessly. Run checks proportional to the change, then the required release gates at T12. A new failure or algorithm change justifies more testing; repetition without a new concern does not.
