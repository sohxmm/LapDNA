# Current handoff

Prefinal update, 9 November 2026: [verified telemetry release](20-verified-telemetry-release.md) supersedes the former single-Monza/synthetic-preview scope and fixed A/B colours. The publication catalogue now supports independently checked sessions; exact live counts are recorded at release.
Updated 8 November 2026 · Revision 6. **R01 historical recorded results and the real Monza 2024 telemetry pilot are implemented and verified live.** Shared editorial styling supports persistent blue dark and off-white light modes. The broader telemetry range remains verified sessions/channels in 2018–2026; older years keep timing comparisons. [Pilot and source decision](19-monza-2024-pilot.md); [year/field coverage](18-data-availability-by-year.md); [rollout](17-approved-ui-and-telemetry-rollout.md).

The existing hosted app is [lapdna.vercel.app](https://lapdna.vercel.app). See [hosting](12-hosting.md) for the actually deployed commit and QA, rather than assuming local changes are live. R01 remains 1,168 qualifying and 24 Sprint Qualifying classifications across 1950–2026, with 27,581 driver-result rows. Its historical formats, event-specific teams and source restrictions are unchanged. The prefinal release removes the synthetic demo.

## Working folder

Use `C:/Users/soham/OneDrive/Desktop/LapDNA`, remote https://github.com/sohxmm/LapDNA.git. The original Documents checkout is an earlier copy. Keep source caches, credentials, raw telemetry and generated pilot data out of Git.

## Implemented locally

- Sports-editorial landing → current-year calendar → actual race/session/phase/driver selection. Shared dark/light preference persists across navigation and reload; source/status/context information stays attached to the result.
- Monza 2024 conventional qualifying, round 16 / OpenF1 session 9586: 20 event-specific drivers, 276 actual laps (Q1 123 / Q2 94 / Q3 59). All source identities and available lap/sector durations match the pinned archive. Eligibility retains 79 laps: 40 telemetry and 39 sector-only; 197 unavailable records retain reasons. Every driver has a timing-eligible lap somewhere, but a particular phase can remain unavailable.
- Explicit composite: native OpenF1 car/location plus identity-matched pinned TracingInsights/FastF1 timing clocks, phases and validity flags. Original archive library version stays unknown. This is not a completed direct FastF1 account adapter. Source keys, offsets, URLs, hashes and attribution are in doc 19.
- Native speed, throttle, gear and binary brake, with missing/sentinel masking. Frozen Norris Q3 source lap 11 reference, approximately 5755.17 m integrated length, eleven projected approximate turn markers and a disjoint reviewed Monza corner/straight profile. Geometry retains explicit source units; no surveyed-position claim.
- Offline per-lap normalization and bounded local cold comparison. Raw B−A time curves, independent lap/pair reconciliation, estimated 100 m mini-sectors, regional sensitivity, supported gross/net class totals and up to three evidence-backed observations. Timing failures cannot become a successful fallback; unsupported explicit telemetry requests fail.
- Actual-lap selectors, same-phase defaults, explicit cross-phase opt-in, unavailable reasons and share-link restoration. Fastest timing-eligible laps are preserved. The separate action **Compare fastest telemetry-supported laps** makes a switch to different supported laps explicit; no silent slower-lap replacement.
- G1 synchronized traces, discrete gear/brake, shared keyboard cursor, linked map/turn/region inspection, reset/zoom, ranked gains, evidence/context/quality details and recorded sector points. Sector-only output contains no false continuous distance or corner claims.
- PNG analysis cards, evidence JSON and exact selected-lap links. Shared links retain comparison ID, actual lap IDs, source hash and tier; automatic restoration refuses a changed method/result identity rather than silently displaying another result. A deliberate manual Compare can request a new result. Cards preserve theme, phases/laps, orientation, source revision and warnings. There is no runtime LLM call.
- Comparison/inventory contract 1.3.0 with explicit composite lineage and geometry units; legacy 1.2.0 reads remain accepted. Calendar/classification contracts remain 1.0.0. Regenerate Pydantic-owned schemas with `npm run contracts`.

## Data, publication and serving

The reviewed source snapshot is `work/monza2024/snapshots/20ffd525c5a06e19d51d41d5/snapshot.json`; raw records are approximately 104.3 MB and stay ignored. The compact generated `services/api/src/lapdna/pilot_data/` publication contains a digest manifest, full roster index, approximately 985 KB compressed normalized arrays and the operator report. It is generated before deployment, intentionally not committed, and contains no upstream credentials. A clean checkout must prepare it using doc 19 before it can serve the real pilot; CI remains independent of live source access.

Compare reads frozen local normalized records only; no upstream download, full-session parse or per-lap normalization occurs on requests. Two concurrent builders, duplicate-request sharing, bounded memory cache and file/array limits bound work. Canonical content-derived result IDs can regenerate after a process restart while this exact publication is retained. This single-pilot bundle is not durable multi-revision archive storage. A changed dataset must not silently replace a linked selection.

## Verification recorded so far

| Check | Result |
| --- | --- |
| Python API/contract/import/alignment/selection suite | 183 passed, one Windows symlink test skipped; upstream TestClient deprecation warning |
| `npm run test:web` | 25 passed, including theme persistence/storage failures, routes, exact selection/revision support, native channel views and dense turn grouping |
| `npm run contracts:check` | Passed |
| `npm run typecheck` | Passed |
| `npm run build` | Passed; approximately 520.20 KB lazy ECharts chunk has a non-fatal size advisory |
| Source integrity and identities | All 70 source-file hashes checked; 276 driver/lap identities and available lap/sector durations reconciled |
| Real phase-best comparison matrix | 321 pairs plus reversals: 84 telemetry results with three observations, 237 sector-only results; canonical reverse identity preserved |
| Independent numerical/API review | No forced sector/time fit; large individual residuals cannot hide through pair cancellation. Offline API comparison/cold immutable lookup pass; same-driver, missing cross-phase consent and traversal IDs reject |
| Local browser checks completed | Theme persistence across reload, full 20-driver roster, default NOR/PIA fastest eligible timing fallback, explicit telemetry-supported-lap switch, NOR lap 11 / PIA lap 18 traces with three observations, linked map/turn zoom, light 1080×1350 card inspected |
| Final hosted/browser checks | Actual 1440×900 and 390×844 CSS viewports, no page-level horizontal overflow, dark/light persistence, exact link reload, swap −0.113 s and browser Back, map/graph inspection, inspected dark/light PNGs and full evidence JSON. Live Monza POST returns schema 1.3.0, 1155 points and three observations; Mexico HAM/LEC/LAW source facts remain correct. |
| Deployed code / CI | `3361e03`, deployment `dpl_2jjmf7tAenA18DRBVZYQfMDk7CYt`; [Ubuntu CI passed](https://github.com/sohxmm/LapDNA/actions/runs/42406657115), 184 Python and 25 client tests |

U01's earlier landing/calendar/results interface was also inspected at 768×1024. The current pilot was checked at desktop and phone sizes above; 200% enlarged-text acceptance remains outstanding.

## Acceptance examples

- Norris Q3 source lap 11: 1:19.327; Piastri Q3 source lap 15: 1:19.436, recorded gap +0.109 s. Piastri's genuine 1.119 s native speed gap blocks this lap's telemetry. Keep the honest sector fallback.
- Explicitly selecting telemetry-supported laps uses Piastri source lap 18, 1:19.661, so the selected-lap gap is +0.334 s. Do not present it as the phase-best gap.
- Norris Q3 lap 11 versus Russell Q3 lap 17 (1:19.440) gives +0.113 s. Maximum individual/pair interior residual is approximately 43.37 ms.
- Selected timing triples were matched to the linked FIA Monza qualifying sector report; FIA report row ordinals and provider lap IDs are not identical. This is external timing reconciliation, not precise corner ground truth.
- Preserve R01 regression cases: Mexico 2026 HAM/LEC Q3 +0.119 s, Q2 reversal by 0.009 s, Lawson DSQ, historical 1950 teams/format, 2005 components and actual SQ sessions.

## Decisions to preserve

1. Python owns selection, distance, quality, classes and evidence; React renders supplied facts. Native fields and interpolation lineage remain distinguishable.
2. Fixed reference independent of A/B; positive B−A favours A. Swap changes view signs/labels, never geometry or class assignment.
3. Corner/straight and 100 m partitions are separate accounting views; status colours are not mini-sector durations.
4. Native support, raw timing residuals, sensitivity, gross opposing gains and mixed/unknown classes govern every local claim. Show fewer observations when evidence is insufficient.
5. No speed-derived throttle/brake/gear, brake-pressure/steering placeholders, forced timing repair or causal driver/car conclusions.
6. Keep real recorded timings useful when a session/channel is absent; no synthetic fallback.
7. Pilot method `distance-v3-openf1-native-composite`, pipeline `monza-pilot-1`. A numerical/source/profile change creates a new reviewed method/input revision and immutable identity.

## Next gates and limitations

Monza T01–T10 functionality and the single-pilot hosted release are verified under the explicit composite source decision. T11 remains open for Silverstone/Suzuka and later verified 2018–2026 session/layout expansion. T12 retains broader durable archive/release work; do not mark the complete programme finished from one pilot. Preserve the live acceptance examples while the user checks them.

The direct supported FastF1 authentication/import adapter, all other native telemetry sessions, durable multi-revision retention/object storage, additional reviewed layouts, optional RPM/DRS graph rows, actual Run 1/Run 2 labelling and LLM rewriting are not complete. The current native-lap contract covers conventional Q; broader SQ lap telemetry remains a separate reviewed extension. Source rights and annotation redistribution remain distinct from software licensing; do not describe combined upstream inputs as unrestricted.

Use the existing implementation rather than rebuilding the scaffold. Update this handoff and the ticket board after checked increments, then commit/push descriptive small features. No source cache or secret belongs in a commit.

## 9 November primary-source increment

The authenticated FastF1 raw-presence adapter is implemented in `ingestion/fastf1_native.py`, exposed by `scripts/import_fastf1.py`. Real Monza 2018 import and all 271 fastest eligible pair/reversal checks pass (76 native telemetry laps, one sector-only). This supersedes the earlier statement that no primary adapter exists. Real verification remains per session/year, with source gaps/unknown flags and dry eligibility preserved. Native compressed frames are decoded before any library fill. Source method/fields/quality wording remain distinct from OpenF1/TracingInsights. Authentication was completed locally by the user; no credentials belong in the repository, server bundle or artifacts. The operator batch respects library limits and stops on access/rate failures. The 2018 and 2024 batches are in progress, so only the activated digest-checked catalogue establishes coverage. Full coverage auditing and hosted release verification remain outstanding.
