# Data availability by year and what LapDNA can do with it

This guide records the first 63-session batch. [Latest audited archive coverage and confirmed deployment](21-archive-coverage.md) supersedes its import-status counts when a subsequent batch is released; the field semantics below remain applicable.

Updated 10 November 2026. The current audited release batch contains 63 real native session publications. This is a bounded batch while the remaining archive imports continue; [hosting verification](12-hosting.md) records the actual deployed release. The [coverage ledger](../config/telemetry-coverage.json) records each source revision, roster/lap capabilities and comparison checks. A provider supporting a year never proves every event, lap or channel is available.

The batch contains all 21 qualifying rounds in both 2018 and 2019; 17 Q and three SQ sessions in 2024; and Mexico 2026 qualifying with 134 eligible timing-only laps across 22 source drivers. It passed 19,010 fastest-eligible same-phase pairs, each in both input orders: 12,317 telemetry and 6,693 timing-only results. Arbitrary individual lap pairs remain checked when requested. Source agreement and numerical checks do not establish physical corner ground truth or driving causation.

2024 regular qualifying in this batch: Bahrain, Saudi Arabia, Australia, Japan, China, Miami, Emilia Romagna, Monaco, Canada, Spain, Austria, Britain, Hungary, Belgium, Italy, São Paulo and Qatar. SQ: China, Miami and Austria. Remaining Q rounds: Netherlands, Azerbaijan, Singapore, USA, Mexico, Las Vegas and Abu Dhabi. Other actual SQ sessions are also pending. Detailed 2020–2023, 2025 and other completed 2026 imports are still in progress; future sessions are not imported in advance.

## Read the availability labels correctly

- **Audited batch:** digest-checked native publications with tested phase-best pairs. The [hosting record](12-hosting.md) identifies which batch is actually deployed; ongoing local imports do not automatically update the website.
- **Source coverage:** a provider documents the year range and field. A session import still has to establish actual rows, native presence and quality.
- **Derived:** LapDNA calculates an estimate from supported source inputs. It is not a new sensor measurement.
- **Optional context:** useful source fields to retain; their existence does not mean a new graph is implemented.
- **Unavailable:** no usable verified measurement in the selected public feeds. Do not infer or substitute a value.

The current R01 manifest contains **1,168 qualifying classifications, 24 Sprint Qualifying classifications, 27,581 driver-result rows and 27,270 timed eligible rows across 1950–2026**. Some drivers and historical timing fields are genuinely missing. A full event count is not proof that every driver has a recorded time. These counts come from [the committed coverage manifest](../services/api/src/lapdna/classification_snapshots/coverage.json), not from an advertised API range.

## Year coverage

| Years | Published in LapDNA now | Additional documented source data | What we can build after verification |
| --- | --- | --- | --- |
| 1950–1993 | Event calendars, historical driver/team entries and qualifying result/time fields where present; predominantly F1DB whole-event backfill | Historical result archives and individual official documents | Two-driver timing gaps, classification tables and historical formats. No continuous telemetry or corner-time claims. |
| 1994–2005 | Same timing tier; Jolpica archive plus F1DB backfill/corrections | Legacy qualifying records; some separate historical components | Exact source-published component comparisons. Preserve format warnings; first six 2005 events have two components, and a component is not an aggregate result. |
| 2006–2013 | Calendar, event-specific teams/drivers, Q1/Q2/Q3 best times and restrictions where present | Modern three-phase result records | Same-phase best comparison and phase tables. A Q3 best does not identify every Q3 attempt. |
| **2014–2017** | Same modern timing tier | No verified continuous car-channel archive selected for LapDNA | **Timing comparisons only.** Keep the graphs/map/corner analysis unavailable for these years. |
| **2018** | Modern timings and all 21 native Q sessions in the audited batch | FastF1 detailed timing, original car/position streams and session context | Eligible laps support measured channels and approximate distance analysis. Per-lap exclusions remain explicit. |
| **2019** | Modern timings and all 21 native Q sessions in the audited batch | Same primary field family | Includes repaired Monaco and Germany imports; per-lap and pair quality gates remain unchanged. |
| **2020** | Modern timing tier | Same candidate FastF1 field family | Same; source parser explicitly documents position coordinates in tenths of a metre from 2020. |
| **2021–2022** | Modern qualifying results; no separate invented SQ1/SQ2/SQ3 classification | FastF1 detailed data and actual weekend/session formats | Conventional qualifying lap comparison. Sprint weekends must follow their actual format; sprint race results cannot stand in for sprint qualifying. |
| **2023** | Qualifying plus six actual Sprint Qualifying/Shootout classifications | FastF1 and OpenF1 historical car/lap/location/context data | Same supported telemetry features, plus actual SQ phase/lap comparison where the imported session supports it. |
| **2024** | 24 Q/six SQ classifications; audited native batch includes 17 Q/three SQ | Primary FastF1 plus explicitly identified OpenF1/TracingInsights composite | Actual lap selections, synchronized channels, approximate maps, observations and export where the selected pair passes. Other sessions remain pending. |
| **2025** | 24 qualifying and six SQ classifications | FastF1/OpenF1 candidate data | Expand the same verified pipeline; do not imply the archive has already been imported. |
| **2026** | 19 Q/six SQ classifications in the current results snapshot; Mexico native Q is timing-only | Candidate native data for completed published sessions | Mexico's native gaps block detailed curves. Other completed sessions still need import; future data is not invented. Raw DRS channel 45 is absent in the pinned 2026 source definition. |

FastF1 documents detailed timing, session, car and position coverage from 2018, typically arriving 30–120 minutes after a session, with possible archive failures. Its older results coverage is broader. [Pinned FastF1 data reference](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/docs/data_reference/index.rst).

OpenF1 documents unauthenticated historical access from 2023; this establishes a source range, not a completeness guarantee. [OpenF1 introduction](https://openf1.org/docs/#introduction). F1DB covers historical seasons/results, while Jolpica's qualifying response provides result and Q-field records rather than every qualifying lap. [F1DB scope](https://github.com/f1db/f1db), [Jolpica qualifying contract](https://github.com/jolpica/jolpica-f1/blob/main/docs/endpoints/qualifying.md).

### Existing classification counts for the requested modern years

| Year | Qualifying sessions published | Separate SQ sessions published | Detailed telemetry status |
| --- | ---: | ---: | --- |
| 2014 | 19 | 0 | Outside selected telemetry range |
| 2015 | 19 | 0 | Outside selected telemetry range |
| 2016 | 21 | 0 | Outside selected telemetry range |
| 2017 | 20 | 0 | Outside selected telemetry range |
| 2018 | 21 | 0 | All 21 native Q publications audited; per-lap exclusions apply |
| 2019 | 21 | 0 | All 21 native Q publications audited; per-lap exclusions apply |
| 2020 | 17 | 0 | Source-supported candidate; not an imported archive |
| 2021 | 22 | 0 | Source-supported candidate; actual weekend format required |
| 2022 | 22 | 0 | Source-supported candidate; actual weekend format required |
| 2023 | 22 | 6 | Source-supported candidate; not an imported archive |
| 2024 | 24 | 6 | 17 Q/three SQ native sessions in the audited batch |
| 2025 | 24 | 6 | Source-supported candidate; not an imported archive |
| 2026 | 19 | 6 | Mexico native Q timing-only; other detailed imports pending |

Counts are the current publication, not a prediction of future sessions or a minimum service guarantee. An SQ count of zero before 2023 does not assert that sprint weekends did not exist.

## Detailed data points

In the following tables, **F18** means FastF1's documented detailed-data range beginning in 2018, and **O23** means OpenF1's documented historical range beginning in 2023. Every F18/O23 entry remains conditional on the actual imported event, driver, lap, source presence and quality. Source field spellings below are examples for an adapter, not an assertion that the browser exposes all of them.

### Timing, identities and lap selection

| Data point | Source/year family and representation | What it enables | Important limit |
| --- | --- | --- | --- |
| Year, round, event/circuit identity, calendar dates | Published 1950–2026 metadata | Year → race flow and exact source matching | Scheduled start is not session-completion evidence. |
| Session ID/type/name and activity times | Published classifications plus F18/O23 metadata | Select actual Qualifying or SQ; avoid sprint-race confusion | Session keys/round numbers are different identifiers. |
| Driver ID, number, name, code, team | Published event-specific entries | Any two drivers with historically correct teams | A number/current roster alone cannot identify a historical driver. |
| Classification position and status | Published result rows | Full classification, native DSQ/DNS restrictions | Position is not reconstructed from the minimum across phases. |
| Q1/Q2/Q3 or SQ1/SQ2/SQ3 best | Published source durations, internal integer milliseconds | Phase tables and exact same-phase gaps | A missing later phase stays null; a duration alone is not an actual lap ID. |
| Actual lap number and identity | F18/O23 lap records | Independent real-lap selection, slower-lap overrides | Out/preparation/push laps mean “Run 1” cannot be guessed from lap number. |
| Lap duration | F18/O23 seconds/duration, normalized to ms | Recorded lap time, sorting and finish reconciliation | Match the exact driver/session/phase/lap and latest validity revision. |
| S1/S2/S3 durations | F18/O23 recorded splits | Sector table and discrete cumulative crossing deltas | No loss can be located inside a sector from three splits alone. |
| Lap start/end and sector crossing clocks | F18; O23 has approximate lap start | Native sample slicing and timing checks | Preserve clock origin/uncertainty; do not assume first sample equals the timing line. |
| Phase membership and session-state events | F18 split/status data; O23 phase-bearing race-control/context where present | Q1/Q2/Q3 and actual SQ membership | Classification Q columns cannot assign every lap's phase. |
| Deletion/reinstatement, pit in/out, generated/accuracy flags | F18 native/provider flags; O23 partial lap/race-control context | Reject or qualify ineligible laps with reasons | Provider flags need lineage; absent fields do not establish validity. |

The distinction between final results and individual laps is part of [R01/R02](16-results-first-milestone.md). Timing-field definitions and source-processing notes are in [the detailed inventory](15-data-points-and-rollout.md#4-lap-timing-selection-and-validity).

### Car channels and native clocks

| Data point | Source/year family; unit | Product use | What it cannot establish |
| --- | --- | --- | --- |
| Speed (`Speed` / `speed`) | F18/O23; km/h | Overlaid speed, supported extrema and distance integration | Car setup, grip or precise cause of a loss. |
| Throttle (`Throttle` / `throttle`) | F18/O23; reported percent | Actual throttle trace and supported pickup/full-throttle patterns | Torque, measured engine output or traction limit. |
| Gear (`nGear` / `n_gear`) | F18/O23; integer state | Stepped gear trace and state at a fixed marker | A fractional gear or speed-inferred shift. Neutral and unknown differ. |
| Brake (`Brake` / `brake`) | F18 Boolean; O23 documented 0/100 switch | Separate binary A/B lanes and approximate onset brackets | Brake pressure, force, pedal travel or brake balance. |
| Engine RPM | F18/O23; revolutions/minute | Optional graph and supported shift context | Engine torque or energy deployment. |
| DRS state | F18/O23 raw state code where present; special 2026 absence hazard | Optional historical DRS context | Unknown/default codes cannot become a measured open/closed state; no inferred active-aero replacement. |
| Native sample UTC and session clock | F18/O23 timestamps | Match source samples to actual laps and retain order/gaps | Timestamp precision is not physical positional accuracy. |
| Native row/channel presence and interpolation lineage | Adapter audit sidecars | Per-driver availability and evidence support | A merged row labelled `car` does not prove its position values are native. |

FastF1 distinguishes original car/position channels from computed distance and interpolated rows; it documents invalid throttle value 104 and Boolean brake. [Pinned channel definitions](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py). OpenF1's car sample cadence is approximately 3.7 Hz, so it is public sampled telemetry rather than a team engineering logger. [OpenF1 car data](https://openf1.org/docs/#car-data).

### Geometry and annotations

| Data point | Source/year family | What it enables | Limit |
| --- | --- | --- | --- |
| Timestamped X/Y/Z | F18/O23 approximate position streams | Frozen reference track shape and progress | Not a precise racing-line, centimetre-level lateral position or reliable elevation comparison. |
| OnTrack/OffTrack/source status | F18 where present | Context and data diagnostics | Not sole authority for a sporting track-limits decision. |
| Coordinate units | Provider/year-specific metadata | Correct reference geometry conversion | Verify 2018–2019; the pinned parser only explicitly states tenths-of-a-metre coordinates from 2020. |
| Turn number/letter and approximate X/Y | MultiViewer/reference annotations where available | T1/T2/... labels and marker selection | Manually authored approximate points, not measured apex sensors. |
| Marker distance/angle, map rotation | Reference-dependent calculations/annotations | Shared graph ruler and readable map | Marker angle is label placement, not steering angle. |
| Layout identity and revision | Reviewed metadata/profile | Correct Monza/year-specific regions | Venue name alone cannot identify every historical layout. |

The marker adapter explicitly identifies its annotations as manual and approximate, with distance depending on the reference lap. [FastF1/MultiViewer marker contract](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/mvapi/data.py). The pinned parser describes coordinate units and inserted missing-position defaults. [Position/parser implementation](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/_api.py).

### Context retained with the selected laps

| Data point | Candidate coverage and units | Useful output |
| --- | --- | --- |
| Compound, stint, tyre age, fresh/used flag | F18/O23 where present; labels/laps/Boolean | Actual tyre badges, run association and comparability qualifications. Age is context, not measured wear or a time correction. |
| Air/track temperature | F18/O23; °C | Time-matched conditions; track temperature is not tyre temperature. |
| Humidity and atmospheric pressure | F18/O23; % and documented hPa/mbar | Conditions panel; atmospheric pressure is unrelated to brake pressure. |
| Rainfall state, wind speed/direction | F18/O23; source state, m/s, degrees | Dry/wet and wind context with sample age; no corner-local rainfall intensity or causal claim. |
| Weather sample time | F18/O23; weather usually around one sample/minute | Show age/separation from each selected lap rather than a fabricated high-rate weather curve. |
| Flags, session status and race-control messages | F18/O23 where present; timestamps/text/scope | Yellow/red/SC/VSC context, phase activity and deletion review. Marshal sectors are not automatically official S1/S2/S3. |
| I1/I2, finish-line and main speed-trap observations | F18/O23 fields vary; km/h | Spot-speed context when fresh per-lap support is established. A carried-forward trap value is not proven fresh, and a trap is not necessarily lap maximum speed. |
| Team radio links, pit events, race positions/gaps | Mainly O23/F18 optional services; endpoint-dependent | Potential later contextual features; not required for the two-lap qualifying product. Race-only endpoints do not become qualifying measurements. |

Context field semantics and missing/default hazards are specified in [the context inventory](15-data-points-and-rollout.md#6-tyres-and-stint-context). The data should be retained without automatically expanding the UI into strategy, radio playback or weather analysis.

## Derived outputs and the claims they support

These are possible only after their input gates pass. They are never advertised as additional recorded telemetry channels.

| Derived output | Required input | What the reader can learn |
| --- | --- | --- |
| Signed final/phase gap | Two eligible recorded durations | Which selected recorded time is faster and by how much; B−A positive favours A. |
| Recorded sector gaps | Matched S1/S2/S3 records | Which official sector contributed to the gap, using discrete crossing totals. |
| Common reference distance and continuous delta | Valid native speed/clocks, independent frozen reference, support/reconciliation | Approximately where along track distance the estimated gap develops. |
| Estimated 100 m mini-sectors | Supported distance/time curves | Local traversal advantage at the chosen bin resolution; not official timing-loop splits. |
| Corner/complex/straight contributions and performance map | Same curves plus reviewed disjoint layout regions | Which supported regions contribute the largest estimated gains/losses. The map and bin partition describe the same lap; totals are not added together. |
| Entry/minimum/exit speeds, throttle/gear/brake patterns | Actual native channel support at declared positions/windows | Observable associated patterns, with sample/gap uncertainty. They do not establish why the driver lost time. |
| Low/medium/high profile | Reviewed frozen reference apex windows and versioned thresholds | Comparison-specific corner-speed pattern; preserve gross opposing gains, coverage, mixed/unknown units and sensitivity. |
| Up to three observations | Distinct supported regions and reproducible evidence | Concise findings scoped to the selected laps. Fewer observations are better than fabricated filler. |
| Share/export card and evidence JSON | Immutable validated comparison and provenance | Reproducible selected laps, displayed order, inputs, method and warnings. |

The numerical rules are fixed in [the methodology](03-telemetry-methodology.md). Deterministic comparison text is generated from validated facts; optional LLM wording can rephrase those facts later but cannot supply missing channels or causal proof. [Analysis generation](14-analysis-generation.md).

## Data we do not have as verified public measurements

Do not display invented steering angle, brake pressure, pedal force/travel, brake balance, fuel mass/flow, suspension travel, car setup, aerodynamic load, tyre surface/carcass temperature, grip, torque, measured G-load, battery state or detailed electrical-energy deployment. Other private data agreements may exist; no usable native entitlement/schema for these has been verified for LapDNA.

We also do not have true official mini-sector durations from the selected segment arrays. OpenF1 lists categorical mini-sector colour/status codes. Those can describe a status, but cannot be subtracted into seconds. A mathematically differentiated speed signal may yield an estimated longitudinal acceleration; it is not a measured IMU/G channel and remains outside the core pilot.

## Monza 2024 verification ledger

**Current live pilot:** 20 event-specific drivers, 276 actual laps (Q1 123 / Q2 94 / Q3 59), 79 timing-eligible laps, 40 telemetry and 39 eligible sector-only laps; 197 ineligible records retain reasons. The source snapshot contains 348,120 native car records, 364,780 position records, 79 weather records and 11 markers. The generated normalized publication is about 2.67 MB plain / 985 KB compressed; approximately 104.3 MB of raw source records remain ignored. Full source/version/hash details, selected FIA timing checks and preparation commands are in [the pilot guide](19-monza-2024-pilot.md).

The working UI provides actual phase/lap selection, four core channels and raw delta, shared cursor/turn/map inspection, separate corner and estimated-mini-sector partitions, class/gross-net evidence, up to three observations and themed PNG/JSON export. Dark/light preference persists. RPM/DRS graphs, inferred Run 1/Run 2 labels and runtime LLM prose are not implemented. Other events/years still need their own publication. Final hosted/mobile/dark-card acceptance is recorded separately, not assumed from local source counts.

Retain these checks and provenance in every pilot revision:

1. Actual qualifying identity/year/round/date, source session keys, complete event roster and per-driver team mapping.
2. All actual laps, phase assignment evidence, recorded durations/sectors, native/provider validity flags, inclusion/exclusion reasons and unavailable drivers/phases.
3. Per-driver native speed/throttle/gear/brake counts, timestamp ranges, invalid/missing masks and maximum support gaps; optional RPM/DRS coverage separately.
4. Car/position clock origins and unit conventions; frozen reference ID, geometry digest, marker source and reviewed layout/window revision.
5. Per-lap timing consistency, scale factors, raw finish/interior sector residuals, supported intervals and promoted telemetry/sector-only capability.
6. Comparison IDs/settings, evidence counts and supported/excluded class units, with source/library/parser/method versions and retrieval/hash metadata.
7. Exact official timing/document comparisons used for external reconciliation; a second community mirror is not automatically an independent measurement.

If a composite source uses **OpenF1 car/lap records plus a TracingInsights archive for phase/validity/geometry context**, declare that composition explicitly. Keep each field's provider, native/processed status, key and hash. Validate driver/lap/phase identity and clock mappings before joining. A provider-derived `Source` label or resampled distance does not independently prove native field presence. Never use a convenient archive column to erase missing OpenF1 measurements or describe a composite as one untouched raw feed.

Blocked channels or unsupported local claims stay unavailable even if other Monza features work. Source-range marketing, a plausible plotted line and schema-valid JSON cannot close those gates.
