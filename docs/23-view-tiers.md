# Owner decision: telemetry view tiers

Approved 10 November 2026. This is an explicit owner-approved change to the
previous alignment/coverage restrictions, limited to the scope below. It takes
precedence over the older "never relax gates to increase coverage" and "do not
redesign the alignment method" instructions for Tier 0/Tier 1 implementation.
The gates for Tier 2 corner observations remain byte-for-byte unchanged.

## Current stop point

**Step 0 is complete: measurement/report only; stopped for owner review.**
No Step 1–6 implementation may start before the owner reviews the
report and instructs continuation. The active application remains v5/contract
1.4.0. A diagnostic continuation in the audit is not an accepted graph or a v6
estimator.

The report is [23-gate-attribution.md](23-gate-attribution.md). Its versioned
receipt is in [the coverage ledger](../config/telemetry-coverage.json), with a
compressed JSON-lines companion containing per-lap derived diagnostics. Raw
source samples and credentials remain ignored/private. Runtime file hashes and
Tier 2 function-body hashes in the receipt protect this measurement checkpoint.

## Product goal

Any two timing-eligible actual laps in the same qualifying session must be
inspectable in stacked telemetry graphs. Q1/Q2/Q3 and actual SQ1/SQ2/SQ3 retain
their source identities. Distinct laps from the same driver are allowed in the
planned selection update. Cross-phase comparisons retain the existing explicit
opt-in and persistent conditions context.

The baseline denominator is the current v5 timing-eligible cohort. Preserve it
for before/after coverage comparisons rather than changing the denominator to
reach a target. Deleted, yellow/non-green and other flagged recorded laps must
also be listed with visible source flags and per-lap reasons in the planned
selection update; visibility does not make them eligible for Tier 2 claims.

## Approved sequence

| Step | Required work | Current status |
| --- | --- | --- |
| 0 | Attribute first and all failing gates for every telemetry failure; per-year histograms, native gaps and sample-spacing distributions; separate lap, reference and pair context | Complete: 217 sessions, 66,125 indexed laps; stopped before Step 1 |
| 1 | Add `telemetry_view`, `aligned_delta`, `analysis` tiers to Pydantic-owned contracts; keep `detail_level` compatible; regenerate contracts; introduce `distance-v6-*` | Pending report review |
| 2 | Tier 0: when native car samples bracket both timing edges, publish actual available measured channels with null gaps and explicit `bridged`/`gap` masks; no claims or observations | Pending |
| 3 | Tier 1: bridge 0.75–2.0 s speed gaps using monotone interpolation, flag those spans, exclude them from Tier 2; add X/Y relative-progress projection onto a frozen reference polyline without coordinate-unit assumptions; expose estimator disagreement as a delta uncertainty band | Pending |
| 4 | Allow same-driver distinct-lap selection in API and `selection.ts`; list flagged laps instead of filtering by `capability !== 'unavailable'`; show per-lap reasons | Pending |
| 5 | Keep existing ECharts stack; show tier badge, shaded bridged spans, distance/elapsed toggle and RPM where measured source values exist | Pending |
| 6 | Gap-bridging tests, passing-v5 regressions and per-year/per-session coverage re-audit; at least 90% of eligible laps at Tier 0 per year unless genuine source car-data absence is documented | Pending |

## Invariants retained

- Python owns alignment, delta, masks, quality and evidence. The browser renders
  supplied values, flags and uncertainty.
- Missing data stays null, never zero. No channel is inferred from another
  channel. Brake is measured on/off, not pressure; gear/brake remain discrete.
- Bridged values are derived estimates, never newly measured source samples.
  They must not inflate native sample counts or qualify as Tier 2 support.
- Elapsed time is never rescaled to official sectors. Recorded sector/lap
  checks and raw residuals remain visible; no independent validation is claimed.
- Estimator disagreement describes a discrepancy band, not a calibrated
  probability interval or surveyed ground truth.
- Existing v5 results that pass today must remain byte-identical, including
  their original IDs, source/method identity and serialized payloads. Preserve
  legacy v5 regeneration; adding a v6 envelope must not rewrite v5 artifacts.
- Tier 2 corner-observation support, materiality, boundary sensitivity, class
  thresholds and source-validity gates remain unchanged. New bridge/gap masks
  can exclude evidence; they cannot create support for an observation.
- Keep event-specific source team colours, A solid/B dashed, B−A sign,
  source-specific drivers/teams and explicit cross-phase warnings.
- Do not silently substitute another lap to produce a graph. No synthetic
  production data, demos, fake fallbacks, credentials or raw caches enter Git.
- One commit per completed step; push normally without force. Step 0 does not
  deploy a behaviour change. Subsequent checks include `pytest`,
  `npm run contracts:check`, `npm run typecheck`, `npm run test:web`, and
  `npm run build`, plus visual/keyboard evidence for actual UI changes.

## Measurement interpretation

The audit keeps the actual first failure separate from conditional downstream
probes. It uses unchanged v5 integration equations on the recorded samples to
measure later checks where a frozen reference exists; it does not insert
samples or accept gaps. Where a reference or native edge support is absent,
later gates are not evaluated rather than marked passing.

Car-edge feasibility in this v5 audit uses its existing ±1 s crop. A failed
bracketing check is not automatically proof that the entire source lacks car
data; the nearest outside-edge sample might lie beyond that crop. Tier 0's
eventual coverage must be measured after implementation, not inferred from
these feasibility counts.

Pair-gap failures depend on two selected laps and belong in pair context. An
individual lap must not be globally labelled bad because one peer comparison
fails. Entirely missing optional channels are availability findings, not a
new whole-lap gate. The importer also has an earlier 5 ms timing-consistency
check before the later 20 ms publication checks; attribution must retain both
stages instead of hiding the earlier gate under a generic exclusion label.

## Step 0 verification receipt

The baseline contains 25,271 timing-eligible laps: 10,431 have v5 telemetry and
14,840 do not. The gap gate is first for 13,393 failures (90.25%). All eligible
laps have in-lap car observations; 25,232 bracket both edges inside the existing
crop. The report includes all overlapping numeric/dependency failures and
explicit unknown downstream checks. Per-lap peer context distinguishes actual
pair checks, conditional diagnostics and the current same-driver rejection.

Original coverage fields compare exactly with the prior committed ledger.
Seven runtime files and ten Tier 2 function bodies match their baseline byte
hashes. Reconstructed time arrays match every currently published passing lap.
The 66,125-record derived companion, per-year histograms, bin totals and pair
counter totals were independently reconciled. No raw sample arrays are committed.

Checks passed: Python suite (one Windows symlink skip), nine new audit checks,
31 client tests, `npm run contracts:check`, `npm run typecheck`,
`npm run test:web`, and `npm run build`. The existing chart-size advisory and
upstream TestClient deprecation warning remain non-fatal. No API/UI behaviour,
selection permission, accepted lap, methodology version or observation gate
changed. Nothing from Steps 1–6 has been deployed.
