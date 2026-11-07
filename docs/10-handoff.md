# Current handoff

Updated 7 November 2026 · Revision 5. **R01 recorded qualifying-results import/comparison and U01 approved interface are implemented. Native telemetry remains T01–T12 work.** The user has selected A sports-editorial landing and G1 stacked overlays, with detailed telemetry limited to verified sessions/channels in 2018–2026; older years retain timing comparisons. See [the approved decision and rollout](17-approved-ui-and-telemetry-rollout.md).

Hosted on Vercel at [lapdna.vercel.app](https://lapdna.vercel.app). The explicit user acceptance case is [2026 Mexico qualifying](https://lapdna.vercel.app/?year=2026&race=2026-19&view=studio). Published classifications cover 1,168 qualifying events from 1950–2026 plus 24 Sprint Qualifying sessions from 2023–2026, with 27,581 driver-result rows. The detailed lap/telemetry catalogues remain empty. The [synthetic demo](https://lapdna.vercel.app/?preview=1) stays separate. [R01 scope and future run selection](16-results-first-milestone.md); [hosting](12-hosting.md).

## Working folder

Use the Desktop LapDNA checkout selected by the user. It has the original Git history and the remote https://github.com/sohxmm/LapDNA.git. The original Documents checkout is retained as an earlier copy; continue work in the Desktop checkout.

## Implemented and checked

- U01: sports-editorial landing at `/`, Open Studio enters `?view=calendar` using the current-year default, existing year/race/comparison deep links preserved. Compact dark calendar/results studio; expandable full classification and Data details retain source/licence, coverage and retrieval metadata, while Timing only, DSQ/partial/historical warnings stay visible. G1 demo has a taller speed row, stepped gear, separate binary brake lanes and symmetric delta scale. Its underlying synthetic fixture is unchanged. No real telemetry importer or derived real comparison was added by U01.

- Real classification acquisition, normalization, publication and typed API. Jolpica supplies phase bests; F1DB backfills 631 missing historical events and preserves native exclusions in 23 complete replacement classifications; OpenF1 supplies 24 Sprint Qualifying classifications. Sources are kept distinct by complete event/session, not per-driver data splicing. All 77 source-stamped calendars are bundled.
- Recorded-results studio: session → exact phase → two eligible event-specific drivers; historical teams, no-time/DSQ/DNS states, phase tables, signed gaps, gap bars, source/coverage labels, URL restoration/back and swap. No continuous telemetry or corner attribution is inferred from phase bests.
- Pydantic/OpenAPI/TypeScript comparison/inventory contract 1.2.0, with per-lap Q1/Q2/Q3 identity, explicit cross-phase context, telemetry and sector-only result variants, and required native channel provenance per driver. Missing channels stay null. Channel-backed claims require positive native sample counts and local displayed support; these structural checks do not prove the native-data computation.
- Separate 1.0.0 calendar and classification contracts, with bounded calendar cache/timeouts/backoff and source-stamped 1950–2026 snapshots. Recent bundled calendars share the six-hour cache window on cold starts. Current year first, actual race next, then the selected race's studio.
- Session roster and lap inventory endpoints, strict local selection validation, cached compare POST, canonical storage ordering and swapped view indication. Cache misses return an honest 409.
- Session browser with full imported roster, phase/lap choices, fastest eligible common-phase defaults, excluded-lap reasons, explicit cross-phase opt-in, aborted stale requests, result invalidation on changed selection and cached result rendering.
- Lazy-loaded ECharts Canvas trace stack: speed, throttle, gear, binary brake and raw cumulative delta; aligned sector/turn rails, estimated mini-sector strip, turn-window selection and shared numeric cursor.
- Actual result adapter for stored telemetry, class summaries and observations; recorded sector table and separate boundary delta points for both tiers.
- Opt-in synthetic design preview at `?preview=1`, using a fictional loop and Sample A/B. It demonstrates a high/medium-gain versus low-speed-loss profile. It remains separate from the real recorded-results studio.
- Source availability probe, research, revised numerical methodology, full implementation tickets, verification/operations guides and GPT-6.1 Sol workflow.
- [20-source audit](13-data-source-audit.md) plus a machine-readable registry. Actual native speed, throttle, gear and binary brake are verified, so no demo channel was removed. Trace rows/readouts follow per-driver source availability, with synthetic provenance for all four unchanged preview channels.
- [Analysis generation specification](14-analysis-generation.md). Current preview prose is fixed; cached real results render saved evidence text. Optional fresh LLM wording is specified after the numerical evidence engine, with no configured provider or runtime model calls today.
- [Field-by-field inventory and rollout](15-data-points-and-rollout.md), reviewed 7 November. It distinguishes recorded inputs, provider processing, reference annotations, derived estimates and optional fields. T01 now explicitly checks defaulted weather, inherited trap values, throttle 104 and provider/year coordinate units. No new runtime panels or importer were added by this planning update.

## Verification

| Check | Recorded result |
| --- | --- |
| Python API/contract/selection/calendar/classification suite | 144 passed, 1 Windows symlink test skipped; one upstream TestClient deprecation warning |
| `npm run test:web` | U01: 17 passed, including landing/calendar entry and existing deep links, lap/channel support and recorded timing/phase/URL/history logic |
| `npm run contracts:check` | Passed |
| `npm run typecheck` | Passed |
| `npm run build` | Passed; lazy chart chunk produces a non-fatal size advisory |
| Browser preview | U01 inspected at 1440×900, 768×1024 and 390×844: landing → current-year calendar, Mexican Q3/Q2 exact timings, keyboard swap/browser back/refresh, historical 2005 format warnings, actual China SQ phases, synthetic turn selection/shared keyboard cursor/brake lanes and discrete sector-only mode. No page-level horizontal overflow observed. 200% text zoom remains a later accessibility acceptance check; the preview browser did not change zoom on the tested shortcut. |
| Isolated UI fixture | Full roster, unavailable phase/driver, cached sector-only output, swap, cross-phase warning and cache miss checked |
| Detailed lap/telemetry folders | No native lap/telemetry sessions imported; classifications are published separately and synthetic QA stays isolated |
| GitHub CI on deployed code 4fcdc86 | [Passed on Ubuntu](https://github.com/sohxmm/LapDNA/actions/runs/42367418088), including 145 Python tests and contract checks |

Local preview used port 5273 because 5173 was unavailable. Override with `npm run dev --workspace @lapdna/web -- --port 5273` when needed; same-origin proxy behavior is unchanged.

The narrowly scoped OpenF1 probe retrieved one historical sample and complete recorded sectors; see the source register. No FastF1 session import, reference geometry, aligned real comparison, official-document reconciliation, valid real corner-class finding or export has been completed.

## Decisions to preserve

1. Whole-session import and per-lap normalization offline; bounded local comparison on demand after T05. No upstream download on the compare request path.
2. All imported drivers and eligible laps, per-lap phases, same-phase default and explicit cross-phase context.
3. Fixed reference independent of A/B; raw delta B−A, positive favors A.
4. Local bins and corner windows are separate partitions. Mini-sector colors/status codes cannot supply duration differences.
5. Corner classes derive from reviewed reference apex windows with configurable 150/250 km/h thresholds. Retain mixed/unknown, gross gains/losses, coverage, independent units and sensitivity.
6. Sector-only results provide recorded timing and discrete cumulative boundary deltas. They cannot support turn-level or class findings.
7. Python generates supported facts and driver-identity-based text. React/ECharts renders them; the synthetic fixture generator is isolated.
8. Telemetry targets verified qualifying sessions in 2018–2026. Monza/Silverstone/Suzuka are validation pilots before all supported layouts, not a permanent three-circuit limit. No fixed four-driver or artifact cap remains. Validate complete per-lap accounting and representative pair/phase matrices. Earlier years keep recorded timing comparisons.
9. Source audit precedes dropping a feature. Preserve the labelled demo; production data needs the actual native channel. FastF1's inserted numeric zero/brake False and absent 2026 DRS defaults are missing-data hazards, not measured states. T01 must retain raw masks and per-source presence before normalization.

## Next implementation gate

The user will check **R01**, explicitly using 2026 Mexican GP qualifying. Hamilton Q3 is 1:16.514, Leclerc Q3 is 1:16.633, B−A is +0.119 s. Q2 reverses the advantage: Leclerc 1:16.944 vs Hamilton 1:16.953. Lawson's source DSQ is visible and blocks selection. Historical 1950 driver/team data, actual SQ sessions, 2005 components, missing phases and restored links have separate checks.

Individual runs/laps are deferred to **R02**, documented in [the results-first milestone](16-results-first-milestone.md). Its first source gate remains **T01**; R01 does not satisfy it. Start GPT-6.1 Sol at High; use Extra High for T03–T05 numerical work. [Workflow and copyable prompts](11-implementation-workflow.md).

U01 is complete against the approved A/G1 decision; the next feature is T01. A bounded unauthenticated 2024 Monza qualifying SessionInfo request returned primary HTTP 401 and mirror HTTP 404; the full installed adapter/access path has not been tested. Do not call the whole archive blocked or verified from that probe. No source credentials were requested or changed. The import environment still needs its separate pinned numerical/data dependency lock; Vercel's lightweight serving environment stays unchanged.

T01 must create a reproducible full-session source adapter/snapshot with actual access behavior, provenance and failure handling. The OpenF1 availability probe does not replace it. FastF1 3.9.2 access/cache interfaces require installed-release verification. Never invent source data to bypass an access issue.

## Remaining work

T01–T05 implement source import, real eligibility/reference/alignment, timing reconciliation, estimated mini-sectors, evidence/classes and local cold comparison calculation. T06–T09 extend the existing scaffold with immutable URL restoration, production shared chart/map selection, dense-label handling, complete quality/evidence details and real circuit maps. T10 implements export. T11/T12 complete three-circuit acceptance and release packaging.

The flat artifact/session readers are current scaffold behavior. T05 must introduce reviewed dataset/publication manifests and writable result-cache separation without feeding manifest files to flat artifact enumeration. Required metadata additions are listed in the contract guide.

Run ticket checks, update this handoff and the status board, then commit and push each bounded completed feature with a descriptive message. Keep credentials, raw caches and local QA material out of Git.
