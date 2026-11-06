# Current handoff

Updated 7 November 2026 · Revision 3 with source audit and calendar navigation. **Blueprint and expanded scaffold complete; real-data implementation starts at T01.**

Hosted on Vercel at [lapdna.vercel.app](https://lapdna.vercel.app), with the [synthetic demo](https://lapdna.vercel.app/?preview=1) and the existing FastAPI scaffold under `/api/v1`. Real session and comparison catalogues remain empty. See [hosting and limitations](12-hosting.md). This deployment is a preview milestone, not completion of T01–T12.

## Working folder

Use the Desktop LapDNA checkout selected by the user. It has the original Git history and the remote https://github.com/sohxmm/LapDNA.git. The original Documents checkout is retained as an earlier copy; continue work in the Desktop checkout.

## Implemented and checked

- Pydantic/OpenAPI/TypeScript comparison/inventory contract 1.2.0, with per-lap Q1/Q2/Q3 identity, explicit cross-phase context, telemetry and sector-only result variants, and required native channel provenance per driver. Missing channels stay null. Channel-backed claims require positive native sample counts and local displayed support; these structural checks do not prove the native-data computation.
- Separate 1.0.0 calendar contract, Jolpica adapter with bounded cache/timeouts/backoff, and source-stamped 2024/2026 fallback snapshots. Current year first, actual race calendar next, then the selected race's studio; URL/back/refresh support and exact year/round session filtering.
- Session roster and lap inventory endpoints, strict local selection validation, cached compare POST, canonical storage ordering and swapped view indication. Cache misses return an honest 409.
- Session browser with full imported roster, phase/lap choices, fastest eligible common-phase defaults, excluded-lap reasons, explicit cross-phase opt-in, aborted stale requests, result invalidation on changed selection and cached result rendering.
- Lazy-loaded ECharts Canvas trace stack: speed, throttle, gear, binary brake and raw cumulative delta; aligned sector/turn rails, estimated mini-sector strip, turn-window selection and shared numeric cursor.
- Actual result adapter for stored telemetry, class summaries and observations; recorded sector table and separate boundary delta points for both tiers.
- Opt-in synthetic design preview at `?preview=1`, using a fictional loop and Sample A/B. It demonstrates a high/medium-gain versus low-speed-loss profile. The default application remains empty until a real dataset is imported.
- Source availability probe, research, revised numerical methodology, full implementation tickets, verification/operations guides and GPT-6.1 Sol workflow.
- [20-source audit](13-data-source-audit.md) plus a machine-readable registry. Actual native speed, throttle, gear and binary brake are verified, so no demo channel was removed. Trace rows/readouts follow per-driver source availability, with synthetic provenance for all four unchanged preview channels.
- [Analysis generation specification](14-analysis-generation.md). Current preview prose is fixed; cached real results render saved evidence text. Optional fresh LLM wording is specified after the numerical evidence engine, with no configured provider or runtime model calls today.

## Verification

| Check | Recorded result |
| --- | --- |
| Python API/contract/selection/calendar suite | 89 passed; one upstream TestClient deprecation warning |
| `npm run test:web` | 8 passed: selection/orientation/channel support and year/race route validation |
| `npm run contracts:check` | Passed |
| `npm run typecheck` | Passed |
| `npm run build` | Passed; lazy chart chunk produces a non-fatal size advisory |
| Browser preview | Desktop/mobile inspected; year default, historical calendar, race studio/refresh, turn selection, keyboard cursor, source labels and sector-only mode checked |
| Isolated UI fixture | Full roster, unavailable phase/driver, cached sector-only output, swap, cross-phase warning and cache miss checked |
| Empty production-data folders | No sessions imported; synthetic QA indexes remain outside default data paths |
| GitHub CI on deployed code 5e6e7d1 | [Passed on Ubuntu](https://github.com/sohxmm/LapDNA/actions/runs/42279132624) |

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
8. Three circuits remain the target; no fixed four-driver or 18-artifact cap remains. Validate complete per-lap accounting and representative pair/phase matrices.
9. Source audit precedes dropping a feature. Preserve the labelled demo; production data needs the actual native channel. FastF1's inserted numeric zero/brake False and absent 2026 DRS defaults are missing-data hazards, not measured states. T01 must retain raw masks and per-source presence before normalization.

## Next implementation gate

Implement **T01** from the updated plan. Start GPT-6.1 Sol at High; use Extra High for T03–T05 numerical work. Use Ultra for independently owned parallel work after interfaces are fixed. [Workflow and copyable prompts](11-implementation-workflow.md).

T01 must create a reproducible full-session source adapter/snapshot with actual access behavior, provenance and failure handling. The OpenF1 availability probe does not replace it. FastF1 3.9.2 access/cache interfaces require installed-release verification. Never invent source data to bypass an access issue.

## Remaining work

T01–T05 implement source import, real eligibility/reference/alignment, timing reconciliation, estimated mini-sectors, evidence/classes and local cold comparison calculation. T06–T09 extend the existing scaffold with immutable URL restoration, production shared chart/map selection, dense-label handling, complete quality/evidence details and real circuit maps. T10 implements export. T11/T12 complete three-circuit acceptance and release packaging.

The flat artifact/session readers are current scaffold behavior. T05 must introduce reviewed dataset/publication manifests and writable result-cache separation without feeding manifest files to flat artifact enumeration. Required metadata additions are listed in the contract guide.

Run ticket checks, update this handoff and the status board, then commit and push each bounded completed feature with a descriptive message. Keep credentials, raw caches and local QA material out of Git.
