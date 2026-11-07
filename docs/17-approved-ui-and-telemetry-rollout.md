# Approved interface and verified telemetry rollout

Decision: user selection, 7 November 2026. **A — Sports editorial** is the landing direction. **G1 — Stacked overlays** is the primary graph layout. The user then narrowed detailed telemetry to years with verified data: **2018–2026 is the eligible source range**, replacing the proposed 2014–2026 range. This is a source boundary, not a claim that every event, lap or channel in those years has been imported or verified.

This decision supersedes the earlier three-circuit product limit. Monza, Silverstone and Suzuka remain validation pilots, followed by all source-supported qualifying events/layouts in the eligible years. Preserve recorded qualifying comparisons for older years. R01 remains complete; native telemetry T01–T12 remains unfinished.

U01 is implemented: editorial landing, current-year calendar entry, compact recorded-results studio and the refined labelled G1 synthetic preview. Node tests (17), TypeScript and production build pass. Desktop/tablet/mobile, exact timing/phase selection, keyboard swap/cursor, turn selection and sector-only presentation were inspected. This verifies the interface, not real data ingestion; see [handoff](10-handoff.md) for current limits.

## 1. Capability policy

| Selection | Available output after the relevant import gates pass |
| --- | --- |
| Before 2018 | Recorded phase/session-best comparisons already published. Actual recorded sectors may be added separately; no continuous telemetry graphs. |
| 2018–2026, session not imported | Existing recorded timing comparison, with a short Timing only status. Do not promise or simulate a graph. |
| Imported, eligible timings and sectors, insufficient spatial telemetry | Independently checked sector-only output; discrete boundary deltas, no corner attribution. |
| Imported, timing and speed pass spatial gates | Continuous estimated delta and supported speed traces; other channels are individually available or missing. |
| Native throttle, gear or binary brake verified locally | Include that channel for the driver and intervals actually supported. Keep an available driver's trace when the other is missing. |
| Geometry/turn markers or reviewed profile missing | Keep supported traces and timing; withhold the map or turn/class claims that require that profile. |
| Timing fails eligibility/reconciliation | Withhold the affected comparison tier and show the actual reason. |

No availability follows solely from a year, calendar entry, final classification or plausible numeric values. Driver-specific channel verification requires source presence, native sample counts, missing-data masks, supported intervals and the numerical quality report. Missing values remain null; zero and brake Off are valid observations only when the source supports them.

The source register documents FastF1 detailed timing/car/position coverage from 2018 and OpenF1 historical coverage from 2023. Access and actual event coverage must still be verified by T01. Keep the separate synthetic preview and its four existing channels; it never contributes real availability or evidence.

Access check on 7 November: a bounded unauthenticated request for the pinned adapter's 2024 Monza qualifying `SessionInfo.jsonStream` returned HTTP 401 from the primary archive and 404 from its documented mirror. This is resource-specific evidence, not a complete adapter execution or proof that every stream/session is unavailable. The current local environment has no FastF1/numerical import packages installed. T01 must resolve a separate data dependency lock and test the supported access path; a normal library return is insufficient because individual load failures can be caught internally. Supported sign-in, if actually required after that test, remains an operator action; never request passwords in chat or store tokens in Git. [Pinned request implementation](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/req.py), [parser/source paths](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/_api.py).

## 2. Visual direction

The landing borrows the hierarchy of [Podium](https://podium.global/) and the restrained focal composition of [Lax Space](https://www.laxspace.co/). The studio borrows the compact hierarchy of [Linear](https://linear.app/). These are composition references, not assets to copy. Graph behavior follows the user's supplied telemetry reference and the existing [experience specification](04-experience.md).

### Landing

- Off-white surface, near-black type, generous negative space and large condensed headline.
- Compact LapDNA wordmark/navigation; one primary **Open Studio** action and a secondary **View demo** link.
- Main copy: **Where did the lap time go?** Avoid a paragraph explaining every field.
- One original circuit-line graphic. A decorative or schematic line is not identified as a measured real circuit. If real geometry is used later, name its dataset and source.
- A concise preview can show the product's comparison pattern only when clearly synthetic; no invented real driver time, endorsement or usage statistic.
- Footer offers the project/methodology link. No account, newsletter, loading gate or scroll-dependent entry.
- Motion is optional and decorative. Honor reduced motion, keep the CTA immediately usable and reserve graphic dimensions to avoid layout movement.

### Studio

- Charcoal analytical surface, quiet borders, tabular numbers and persistent A cyan solid / B orange dashed encodings.
- Primary content: event, year/race/session/phase controls, two driver choices, recorded times/gap, supported visual output and concise findings.
- Keep phase, DSQ/DNS, missing values, synthetic status, Timing only and blocking/warning context visible where they affect interpretation.
- Put source retrieval times, coverage inventories, raw quality diagnostics and methodology explanations in **Data details**. Source attribution/licence remains accessible and attached to the result.
- Avoid repeated instructions, future-work paragraphs, implementation terms and empty speculative feature panels in the main flow.
- Existing direct comparison links, swap, refresh/back navigation, event-specific teams and exact phase times must survive the redesign.

## 3. Entry flow and routes

```text
/                                  Landing
/?view=calendar                    Current-year calendar (year selector first)
/?year=2024                        Selected-year calendar
/?year=2024&race=2024-16&view=studio Selected event studio
...&session=<id>&phase=Q3&a=<id>&b=<id>
                                   Recorded-result selection, unchanged
/?preview=1                        Explicit synthetic telemetry demo
```

Open Studio enters the calendar using the server-provided current year; do not hard-code 2026 into the ordinary CTA. Selecting a new year clears the selected race/session/drivers. Selecting a race opens its studio. Only actual available Qualifying/Sprint Qualifying sessions appear. Historical Sprint Shootout labels map to the source's actual SQ phases; sprint race results never stand in for qualifying.

R01 phase-best comparison remains the first useful real view. T02 later links a classification best to an actual eligible lap using driver/session/phase identity and exact timing evidence; it must not create a lap from a duration alone. All drivers appear, with eligibility reasons. Individual lap/run overrides remain R02: preparation/out/in laps and unequal attempt counts prevent guessing Run 1/Run 2 labels.

## 4. G1 graph contract

Desktop primary order:

```text
Event / session / phase                     Data details
A driver · actual lap · time    B driver · actual lap · time
Recorded gap / context / capability
Estimated local-gain strip                   same distance scale
Sector boundaries and T-number ruler         actual marker distances
Speed (km/h)                                tallest row
Throttle (%)
Gear                                        integer steps
Brake A / Brake B                           separate binary lanes
Cumulative B−A delta (s)                     zero baseline
Shared distance ticks / numeric cursor / full-lap reset
Track map + ranked corners/straights
Low / medium / high profile + up to three evidence-backed observations
```

Use the existing single ECharts Canvas multi-grid adapter. Do not replace it with separate unlinked charts. One distance domain, canonical cursor and zoom selection drive every row, turn rail, map and evidence inspector. Python supplies the analytical arrays and facts; browser state never changes the numerical result.

- Align plot margins and marker guides through every visible row, including delta.
- Gear is previous-value sampled; brake is measured On/Off/Unavailable, with separate A/B lanes. No smoothing or speed-derived pedals.
- Native-supported null gaps break traces. A cursor in a gap reports Unavailable rather than jumping to a distant sample.
- Sector labels refer to recorded timing; their reference-distance positions are estimates. Local 100 m bins are estimated mini-sectors, never official measured splits.
- Turn numbers use reviewed projected source markers, not equal spacing. Dense full-lap labels group/stagger without moving data coordinates; every turn remains selectable in the companion list.
- Selecting a turn or observation opens its interval with context. Full-lap reset is always reachable. Map selection and keyboard distance exploration use the same state.
- Category classes and reference geometry do not change on A/B swap. Signs and driver encodings do.
- Mobile keeps the delta and shared distance context available. Channel visibility controls may reduce density; do not add independent per-row zoom. Primary touch targets are at least 44 px and no page-level horizontal overflow is permitted.
- Real corner observations are emitted only after evidence gates pass. Display fewer than three when appropriate. Neither final times nor sector-only deltas can fill those slots.

G3 corner inspection is an interaction within G1 rather than a second main layout. G2 map-first and an unrelated cinematic landing are outside the chosen direction. The detailed thresholds, local support and uncertainty rules remain in [methodology](03-telemetry-methodology.md).

## 5. Implementation sequence and completion evidence

Each row is a bounded implementation checkpoint; continue the existing T01–T12 tickets rather than introducing an alternative numerical pipeline.

| Checkpoint | Implementation | Required evidence before proceeding |
| --- | --- | --- |
| U01 | Landing, compact calendar/results UI, approved G1 visual language | Desktop/mobile and keyboard inspection; R01 times/DSQ/URL regression; no false real telemetry claims. |
| T01 | One complete 2024 Monza qualifying snapshot using a pinned source adapter | Actual full-session roster/laps/car/position access; raw masks, provenance, units, immutable manifest, repeat import, offline tests and sanitized source report. |
| T02 | Full driver/phase/lap inventory and eligibility | Actual Q1/Q2/Q3 identity, deleted/incomplete laps, absent phases, all event-specific teams; no duration-only lap identity. |
| T03–T04 | Frozen reference, reviewed Monza layout, per-lap alignment and reconciliation | Complete distance/region partitions, native support and timing residuals; swap invariance; official timing cross-checks. |
| T05 | Local comparison, supported metrics, evidence and immutable results | Cold pair from normalized arrays, no upstream request, sector fallback, gross/net class evidence, bounded concurrency and deterministic identity. |
| T06–T10 | Connect real selectors/G1/map/evidence/export | Newly selected eligible pair works end to end; cursor/zoom/turns linked; card and JSON preserve source, phases and warnings. |
| T11a | Silverstone and Suzuka pilots | The same pipeline handles different track speeds, dense turns and a crossover; independent profile and reconciliation checks. |
| T11b | Expand by layout/season across 2018–2026 | Coverage manifest records every attempted session and capability; no hidden event/driver curation; each new/changed layout passes its profile gates. |
| T12 | Durable publication and hosted release | Vercel reads published data without raw downloads/import credentials; restart/rollback/shared-link checks and measured serving bounds pass. |

The new year scope does not turn T01–T05 into completed work. The first source request is a pilot, not verification of nine complete seasons. Earlier three-circuit acceptance remains a useful test matrix, not the new product coverage ceiling.

## 6. Archive acquisition and coverage ledger

The archive planner enumerates **completed, actual qualifying sessions** from sourced event metadata for 2018–2026. Track year/round plus the source's stable event and session identities. Include conventional qualifying and actual sprint qualifying formats; a calendar date or sprint race endpoint is insufficient. Do not import cancelled/upcoming sessions as results.

Implement a resumable ledger at T01/T11b with one record per session revision:

- year, round, source event/session IDs, actual session type, scheduled/actual timestamps and explicit completion evidence;
- layout key and revision (year-specific changes matter: different configurations cannot share a reference just because the venue name matches);
- source/library/parser version, retrieval UTC, content hashes, terms/attribution and sanitized access status;
- attempt state: pending, imported, verified, missing, blocked or published; machine-readable reason and last-attempt UTC;
- full roster/lap counts, phase assignment counts, per-driver/channel native coverage, timing/sector support and excluded/unknown records;
- snapshot/reference/profile/method/schema revisions and promoted capability; a discovered year is never a verified capability;
- retry classification and retained prior publication, so a transient source outage cannot replace a working dataset with an empty one.

Acquire one session at a time with bounded retries, disk limits and cache reuse. Start with 2024 Monza; after its source gate, sample the earliest year, a recent year, a real SQ weekend and layouts with revisions before launching the full queue. Reuse valid snapshots and normalize each lap once. Do not precompute every driver/lap pair; normalize O(laps), then compare selected pairs on demand.

Record absent channels explicitly. Do not silently splice timing from one source with another provider's resampled car/position traces. A fallback source requires its own reviewed adapter and a new revision with documented clocks/lineage. The existing classification source remains distinct from native lap telemetry.

## 7. Storage and hosting boundary

Continue serving R01 on Vercel. Import and preparation are offline operator/worker tasks; neither calendar browsing nor Compare downloads a source session. Raw streams and caches stay outside Git and the Vercel function bundle.

For the first verified pilot, use the existing ignored local data directories and immutable manifests. Measure raw, normalized and per-comparison sizes before selecting the archive host. The initial serving interface should read a publication by immutable key from a local directory, with a later HTTP/object-store implementation of the same interface. Do not wire a specific paid service into the UI or claim durable hosted telemetry before its storage is provisioned and tested.

Before broad public telemetry, store normalized session data and immutable shared comparisons in durable storage; use a disposable bounded cache separately. Keep only compact indexes/coverage metadata in the serving bundle. Publish revisions atomically and retain the preceding complete publication for rollback. A runtime filesystem cache alone cannot back durable share links on Vercel.

## 8. Checks and handoff

U01 checks: existing Node selection/navigation regressions, TypeScript, production build; inspect landing/calendar/results/demo at 1440×900, 768×1024 and 390×844. Check keyboard entry, source details, exact Mexico Q3/Q2 values, Lawson DSQ, older timing-only flow, synthetic labelling, reduced motion and browser back/refresh.

T01 onward uses the existing ticket-specific Python/contract/numerical gates. CI must remain independent of live source access. Record actual source request outcomes separately from offline test results.

Update [handoff](10-handoff.md) after each checkpoint with actual work completed and limitations. Commit/push checked small features using descriptive subjects. The next coding session reads this decision alongside its selected ticket; it does not brainstorm a new renderer, sign convention or data inference method.
