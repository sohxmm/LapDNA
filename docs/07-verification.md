# Verification and release gates

Report separately what was tested with synthetic data, observed in a historical source response, verified against an independent official document and inspected on a real prepared comparison.

## Current scaffold checks

After installing the README prerequisites, run from the repository root:

```powershell
.venv\Scripts\python -m pytest services/api/tests
node --test apps/web/src/features/comparison/selection.test.mjs
npm run contracts:check
npm run typecheck
npm run build
```

The Python suite checks API behavior, schema discrimination, safe local paths/IDs, result arithmetic, session/lap inventory and bounded prepared selection. Synthetic fixtures exercise valid and invalid results. The TypeScript/build checks verify generated API shapes and browser compilation. Open the explicitly labeled chart preview for interaction and visual checks. The [source probe](09-sources.md) is an optional online availability check; CI and the normal app do not depend on it. Record actual commands/results in [handoff](10-handoff.md).

## Numerical and contract regression matrix

Use small independent, analytically constructed inputs. Exercise values below, exactly at and above each cutoff. See the [methodology](03-telemetry-methodology.md) for formulas, units and source policy.

| Case | Expected result |
| --- | --- |
| Constant speed and identity | Closed-form integral, zero like-for-like delta, no invented observations. Use two different drivers at the public API boundary. |
| Reversed A/B | Delta and both local partitions negate. Gross A/B and win counts exchange, net/sensitivity reverse orientation. Frozen geometry, grid, labels, reference classes and ranking stay fixed. Double swap restores the full view. |
| Clock and calibration | Lap edges require bracketing samples. Constrained endpoint and reference-derived interior timing are labeled. Perturb official sectors without moving the raw curve. Large individual errors cannot cancel into a passing result. |
| Missingness | A speed gap can invalidate alignment; missing brake suppresses brake evidence only. Unknown core timing blocks both tiers. A denser display grid cannot increase native support. |
| Discrete channels | Gear stays integer and brake stays boolean with previous-sample behavior, bounded support and null gaps. Values are never inferred across an unsupported gap. |
| Two distance partitions | Each partition separately covers 0…L once and telescopes to final minus initial delta within 1e-6 ms for a complete synthetic lap. Verify independent accounting on an exact 100 m multiple and a short final bin. An unsupported interior span nulls the bin even with supported endpoints. |
| Stable reference class | 149.99/150/249.99/250 km/h give low/medium/medium/high. Three native samples plus gap and boundary stability checks are required. Missing or unstable support becomes unknown. Changing the compared laps cannot change a classified marker. |
| Grouping | Mixed-class complex stays mixed, unresolved region stays unknown, straights stay outside corner totals. A wrap group counts once; if one piece fails, exclude the group and retain its full expected length. |
| Gross, net and coverage | Use an explicit opposing-gains example. A positive net cannot imply every unit favored A. Test 0/partial/full coverage, empty class returning null values and disjoint expected/included membership. |
| Interpretation | Test the exact §6.7 materiality, independent-win, coverage and sensitivity boundaries. A supported high/medium-gain and low-loss pattern names the appropriate driver on swap. One contrary material unit or excluded class member prevents an exclusivity claim. Flat/noisy/insufficient evidence yields an appropriately qualified result. |
| Evidence | Each observation's number and language reproduce from native metrics, declared thresholds, region and template. Reject unsupported or overlapping brake-on brackets, duplicate regions and unstable gain direction. Return 0–3 findings plus a reason where required. |
| Sector-only | For sector gaps [25, −40, 12] ms expect cumulative [25, −15, −3] ms. The payload has no distance arrays, map, turns, minisectors or local analysis. Explicit telemetry requests and auto fallback respect the actual capability. |
| Identity and retry | Identical revision, unordered lap IDs, tier and settings yield the same ID/values. A new reference/method/source revision changes identity. Repeated, reversed and concurrent POSTs resolve to one valid result or an explicit bounded-load outcome. |

## Real-session acceptance pack

Build one pack for each imported Monza, Silverstone and Suzuka qualifying session. Preserve the source/retrieval identity, FastF1 version, complete roster, number of indexed/rejected/unknown-phase laps, eligibility reasons and phase counts per driver. Account for every source lap once, including exclusions in the operator report. Verify the session reference, every marker/window, lap-wrap attribution, source-projected sector positions and Suzuka's crossover. Reconcile all supported individual lap records automatically before enabling selection.

Select a bounded **representative matrix** following these minimum rules. Store the exact chosen IDs, phases and branch of the selection policy exercised. Reuse a pair across rows only when it genuinely covers both cases.

| Required coverage | Evidence |
| --- | --- |
| Each circuit, two ordinary telemetry comparisons | One close pair (smallest positive official gap among comparable eligible laps) and one wider control (choose a distinctly larger recorded gap and record why). Include one curated comparison with three supported regional findings per circuit. Record both individual/pair residuals, scale factors, native sample support, sensitivity, local/category evidence and an exported card. |
| Each circuit, complete selection inventory | Compare source participants with served roster. Every known-phase lap gets a row/capability. Check the fastest eligible defaults, an override to another recorded eligible lap when available, a rejected lap and a driver absent from a later phase. Show eliminated or unavailable phases with the actual reason. |
| Across the pack, Q1/Q2/Q3 | Exercise each actually available phase, at least one Q1-only driver, and explicit Q1↔Q3 (or closest available real cross-phase pair) with reject-by-default and opt-in results. Give both phase labels, timestamps/context and warnings in the interface and exported card. Record any missing availability. |
| Across the pack, capability boundaries | Test available sector-only and unavailable-timing cases. Use a clearly labeled deterministic test variant if real data lacks a degraded case; retain all original source quality flags. A synthetic case never becomes a reviewed real result. |
| Each circuit, new versus existing pair | Begin with one local result absent, compute with outbound access disabled, then repeat, reverse and reload its ID. Exercise an additional valid pair from different roster selections. Coverage is the full eligible inventory, with automatic validation on every result; manual review is representative. |

For each externally checked pair, identify the exact per-lap FIA sector-analysis rows, timing/classification links and source values. A final classification can document a phase best but cannot verify an arbitrary slower lap. Capture signed residuals and roundoff tolerances; if only the source feed supports a value, label it feed-only. Review low/medium/high assignments and all curated claims against their source intervals. Do not lower thresholds to manufacture a three-observation card.

## Browser acceptance

Inspect 1440×900, 768×1024, 390×844 and 200% text zoom. Exercise a real telemetry result, real or clearly labeled fixture sector-only result, a cross-phase pair, number/letter turns at high density, missing channels and mixed category contributions.

- Choose both drivers, independent actual laps and phases. Verify default highest common phase, disabled absent laps, explicit cross-phase confirmation and context through reload/export. A stale response cannot replace newer selection. Empty inventory, unavailable selection, unsupported result, busy service and source/backend failure must be distinguishable.
- In telemetry mode, test shared cursor/zoom/selection across the five ECharts panes, sector guides, turn ruler, colored 100 m strip, map, table and findings. After resize and zoom select a hidden-by-thinning turn via the accessible turn list and check its distance/readout. Distinguish hatched unknown bins, neutral bins, A and B gains. Gear/brake remain steps and unsupported channels have gaps.
- With keyboard alone, select laps, explore distance, choose a turn, open its evidence, return focus and reset zoom. Verify driver distinction without color, legible narrow labels and accessible text for Canvas data.
- In sector-only mode, check the three categorical end points and exact sector table. No connecting curve or colored map appears. Sector-only cards distinguish official splits from absent local estimates.
- Verify local findings link to correct windows and class member lists show opposing contributions and support. Signed values reverse correctly. Long labels/names, few findings, no class members and partial quality warnings fit without clipping.
- Download the 1080 × 1350 PNG and JSON, inspect at native/half size and restore a shared immutable ID. Check both phases, orientation, source, methodology, reduced detail/quality notices and exact selected laps. Test clipboard/export failure and retry.

## Release gates

1. Clean core and data installs, offline tests, schema drift check, typecheck and production build pass; optional real-data acceptance runs are documented with inputs.
2. T01's supported FastF1 access gate passed. Three complete imported session inventories and reviewed references exist. The representative matrix has evidence and limitations, and each actual computation passes the applicable analytical validator.
3. Sector-only fallback is independently eligible. Telemetry blocks cannot publish local claims. Reviewed warning results carry the warning from response through export.
4. Every curated claim has evidence; source coverage, validation independence, uncertainties, correct units, attribution and distribution scope are documented.
5. Restart and recovery preserve immutable results and the last good dataset revision. Verify bounded cold-build, cache hit, simultaneous same-key and different-key requests and no upstream request on any serving route. Measure [architecture budgets](02-architecture.md) under recorded hardware/dataset/load conditions.
6. Responsive, keyboard and export inspection passed. Secrets, raw caches, local paths and test-only synthetic results stay outside released data. Record meaningful limitations and the tested release revision in the handoff.
