# Data-point inventory and implementation plan

Reviewed 7 November 2026. This is the working inventory for the sources evaluated in [the source audit](13-data-source-audit.md), with a rollout that preserves the existing two-driver, three-circuit scope. A field existing in a provider's schema does not establish availability for every driver, lap or year. This document adds no runtime importer or sensor panels.

## 1. Product decisions

- Preserve the four preview channels: speed, throttle, gear and binary brake. Their synthetic curves stay explicitly labelled.
- Import a complete qualifying session once, rather than downloading data for each chosen pair.
- Retain useful supporting fields even when they do not get their own graph.
- Show a recorded value only with source support. Keep reference annotations, provider processing, interpolation and LapDNA estimates distinguishable.
- Use FastF1 as the first session adapter, separately validate OpenF1, consider TracingInsights for archive/backfill, use Jolpica for calendars/classifications, and FIA reports for external timing review.
- Keep RPM and historical DRS as optional follow-ups. Other available racing data does not automatically expand this qualifying product.
- Default to the highest common eligible qualifying phase; allow deliberate cross-phase comparisons with persistent context warnings.
- No real session has been imported into the current app. Calendar navigation, contracts, prepared-result rendering and the synthetic preview exist; numerical engine tickets remain open.

## 2. What the labels mean

| Label | Meaning |
| --- | --- |
| Recorded | A value reported by the underlying timing/car/weather source. It can still be sparse, delayed or erroneous. |
| Provider-processed | A library/archive normalizes, fills, merges, reconstructs or computes a value. Preserve its processing history; do not call every populated cell a fresh observation. |
| Reference annotation | Authored marker, reviewed analysis window, layout orientation or other reference configuration. |
| Derived estimate | LapDNA computes it from supported inputs using a versioned method. |
| Unavailable | No supported value for that field/range. Use null and a reason, not an invented zero. |
| Synthetic | Constructed preview/test data, isolated from published real comparisons. |

These conceptual labels are richer than the current wire schema. Contract 1.2.0 currently supports measured/missing declarations for the four car channels, plus sample nulls and evidence support counts. Source-specific raw presence, processing and broader context diagnostics belong to T01–T05; add schema fields deliberately rather than pretending all of them are implemented today.

## 3. Native car data

| Data point | Native fields and units | Intended use | Acceptance and scope |
| --- | --- | --- | --- |
| Speed | FastF1 Speed; OpenF1 speed; km/h | Core overlaid trace, speed comparison, distance integration | Require native timestamps and gap diagnostics. Never hide spikes with an undocumented smoother. |
| Throttle | Throttle / throttle; reported percentage | Core overlaid trace; supported pickup/full-throttle evidence | Not torque, engine power or tyre grip. FastF1 documents occasional 104 as invalid/unavailable; mask with a reason rather than clamp to 100. |
| Gear | nGear / n_gear; integer state | Core stepped trace and gear at a fixed reference marker | Preserve neutral 0 and missing independently. Never derive from speed; neutral cannot support a normal corner-gear assertion. |
| Brake applied | Brake / brake; Boolean or documented 0/100 | Core stepped On/Off trace and transition brackets | No pressure, force, pedal travel or brake balance. Missing is not Off. Undocumented raw values require review. |
| Engine speed | RPM / rpm; rev/min | Retain on import; optional RPM trace and supported shift context later | Not a torque or energy-deployment measurement. Requires a contract/renderer extension before public display. |
| Historical DRS state | DRS / drs; source-specific integer codes | Retain raw presence/state; optional historical overlay | Preserve unknown codes. Pinned FastF1 defaults an absent channel to 0 and notes absence in 2026; default 0 is unavailable, not recorded closed. No assumed replacement active-aero channel. |
| Car sample UTC | Date / date; timezone-aware UTC | Clock alignment, source revision matching and sample identity | Preserve precision and source semantics; numerical precision is not a claim of physical measurement accuracy. |
| Session clock | SessionTime and source session time | Slice laps against timing records | Not interchangeable with the slice-relative Time column. |
| Slice-relative clock | Time; duration since slice origin | Debugging/rendering only where appropriate | Do not zero a lap by assuming its first sample is the timing line. |
| Source indication | Source, raw field presence, native/interpolated lineage | Audit and channel support | One row's Source flag does not prove every field in a merged row was natively observed. Preserve car and position streams separately. |

Sources: [FastF1 channel definitions](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py), [pinned car parser](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/_api.py), [OpenF1 car data](https://openf1.org/docs/#car-data).

OpenF1 describes approximately 3.7 Hz car/location sampling; pinned FastF1 describes usual car intervals near 240 ms. Neither establishes a uniform high-frequency engineering logger. A 5 m drawing grid or smooth-looking chart adds no observations.

## 4. Lap timing, selection and validity

| Data point | Field/example | Intended use and rule |
| --- | --- | --- |
| Driver/lap identity | DriverNumber, Driver, LapNumber; stable LapDNA lap_id | Identify every actual lap and prevent cross-driver/event mismatches. Driver numbers need a season/session identity. |
| Recorded lap duration | LapTime / lap_duration | Headline time, eligible-lap sorting and finish reconciliation. Normalize source seconds to internal milliseconds. |
| Recorded S1/S2/S3 duration | Sector1Time–Sector3Time / duration_sector_1–3 | Recorded sector table and independent timing consistency checks. |
| Sector crossing clocks | Sector1SessionTime–Sector3SessionTime where supplied | Compare raw cumulative telemetry timing at source crossings. Their plotted distance positions are derived. |
| Lap start/end clocks | LapStartTime, LapStartDate, Time; date_start where supplied | Extract native observations and display time-of-day. OpenF1 explicitly calls date_start approximate. |
| Q1/Q2/Q3 membership | Supported qualifying-session splits and status/phase events | Per-lap phase selection; validate phase boundaries rather than derive from best-time classification columns. |
| Official phase bests | Classification Q1, Q2, Q3 | Display/check a phase best; not a list of every lap. Missing phase is absent, never copied from another phase. |
| Personal-best indicator | IsPersonalBest | A useful source flag, not a replacement for valid-lap sorting or later deletion handling. |
| Pit exit / pit entry | PitOutTime, PitInTime; is_pit_out_lap | Reject out/in laps under the initial eligibility policy. Do not treat missing pit fields as proof without source completeness checks. |
| Lap deletion and reason | Deleted, DeletedReason, associated race-control messages | Exclude deleted laps and retain reasons; process reinstatements/corrections as new revisions. |
| Library-generated lap | FastF1Generated | Prevent constructed timing records from becoming selected recorded flying laps. |
| Library accuracy flag | IsAccurate | One input to quality/eligibility; not proof that telemetry is precise or that FIA timing was independently checked. |
| Lap track-status summary | TrackStatus | Eligibility/context. Retain the underlying status timeline, not just a combined string. |
| Final qualifying rank | Classification position | Roster ordering/result context; not a position-coordinate or every-lap rank measurement. |

Sources: [FastF1 lap definitions/processing](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py), [OpenF1 laps](https://openf1.org/docs/#laps), [Jolpica qualifying](https://github.com/jolpica/jolpica-f1/blob/main/docs/endpoints/qualifying.md).

Both selected laps need eligible recorded timing. Source/FIA reconciliation must match the exact driver, lap, phase and document revision. A Q3 classification best cannot verify a slower Q3 lap selected explicitly.

## 5. Speed-trap observations

| Data point | FastF1 / OpenF1 field | Intended use |
| --- | --- | --- |
| First intermediate speed | SpeedI1 / i1_speed; km/h | A recorded spot-speed comparison where fresh support is established. |
| Second intermediate speed | SpeedI2 / i2_speed; km/h | Same, at the second intermediate. |
| Finish-line speed | SpeedFL; km/h where supplied | Context separate from a lap's maximum sampled telemetry speed. |
| Main speed-trap reading | SpeedST / st_speed; km/h | Context at the source's trap, not necessarily the exact maximum anywhere on the lap. |

These are optional context, not core graph dependencies. The pinned FastF1 implementation forward-fills trap values when updates are absent, partly to handle the feed omitting repeated equal values. Keep that processing/freshness distinction: identical values may be legitimate, but a filled cell alone does not prove a fresh measurement for the selected lap. Never reconstruct freshness from a value changing or staying constant. [Pinned processing](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py)

## 6. Tyres and stint context

| Data point | Fields / units | Intended use and limitation |
| --- | --- | --- |
| Compound label | Compound / compound | Comparison badge and context warning; preserve unknown/test labels and year-specific mapping. |
| Tyre age | TyreLife, tyre_age_at_start; laps | Context at the selected lap. Record when age is incremented/calculated from a stint base. Not measured wear or remaining grip. |
| Fresh-tyre flag | FreshTyre; Boolean where available | Source-reported stint context, with unknown kept distinct from false. |
| Stint number | Stint / stint_number | Associate tyre runs with laps. |
| Stint start/end lap | lap_start, lap_end or validated lap grouping | Join compound/age to the correct lap, with coverage checks. |

Retain these for the initial comparison context; no tyre-degradation or tyre-performance causal model is in the MVP. A 2-lap-old soft tyre and a 5-lap-old soft tyre are a comparison qualification, not grounds to subtract a guessed correction. [FastF1 fields](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py), [OpenF1 stints](https://openf1.org/docs/#stints).

## 7. Weather and track/session context

| Data point | Typical field / unit | Intended use and limitation |
| --- | --- | --- |
| Air temperature | AirTemp / air_temperature; °C | Time-matched comparison context. |
| Track temperature | TrackTemp / track_temperature; °C | Asphalt condition context; not tyre temperature. |
| Humidity | Humidity / humidity; % | Retain context. |
| Atmospheric pressure | Pressure / pressure; mbar or hPa per provider | Retain the documented unit; not brake pressure. |
| Rainfall flag | Rainfall / rainfall; documented state | Report actual source state and support; not rainfall intensity or corner-local wetness. |
| Wind speed | WindSpeed / wind_speed; m/s | Context; no automated claim that wind caused a gain. |
| Wind direction | WindDirection / wind_direction; degrees | Same; preserve source bearing convention. |
| Weather sample time | Time / date | Retain sample age and offset from the lap, not a fabricated per-corner weather trace. |
| Track-status events | Time, Status, Message | Green/yellow/red/SC/VSC context and eligibility according to the reviewed source mapping. |
| Session-state events | Started, Aborted, Finished and related timestamps | Establish real phase/session activity, including red flags and restarts. |
| Race-control message | Date/Time, Category, Message | Retain original messages for validity/context review. |
| Affected scope | Flag, Scope, Sector, RacingNumber/driver_number, Lap/lap_number | Match an event to a relevant driver/region/lap. A race-control sector can be a marshal segment, not one of official S1/S2/S3. |
| Qualifying phase on events | qualifying_phase where supplied | An additional phase signal; validate completeness and mapping against session/lap boundaries. |

Weather is generally sampled around once per minute, not once per car sample. Pinned FastF1 weather parsing can substitute zero/False for missing or malformed fields. Preserve raw presence before using a dry/no-rain statement or any numeric value. If this cannot be established, disclose unavailable/freshness-unverified weather rather than default conditions. [Weather/parser definitions](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/_api.py), [OpenF1 weather](https://openf1.org/docs/#weather), [race control](https://openf1.org/docs/#race-control).

The initial green/dry eligibility policy remains as specified in the methodology. Different phase, tyre age/compound and elapsed time between selected laps remain visible qualifications; a weather observation never erases a cross-phase warning.

## 8. Geometry, turn labels and calendar identities

| Data point | Source/type | Intended use and rule |
| --- | --- | --- |
| Car X/Y/Z with native timestamp | Position stream, approximate coordinates | Reference circuit geometry/progress. Not centimetre-accurate lateral placement, precise elevation or a driver-line comparison. |
| OnTrack/OffTrack status | Position status where supplied | Supporting context; not sole authority for track-limit legality. |
| Native position source/clock | Date, Source, raw presence | Associate geometry with the reference clock without repeatedly resampling it. |
| Corner number and optional letter | MultiViewer marker Number, Letter | T1, T2A, T2B labels without dropping lettered turns. |
| Corner marker X/Y | Authored approximate marker coordinates | Reference map annotations, after layout review. |
| Marker angle | Angle; degrees | Visual label-placement direction; not steering angle or road heading. |
| Marker distance | Reference-dependent computed Distance | Turn position on the common axis; validate against frozen reference and crossovers. |
| Map rotation | rotation; degrees | Display orientation only. |
| Marshal-light / marshal-sector markers | Approximate reference annotations | Optional contextual map layer, distinct from official sector clocks. |
| Year, round, event and circuit identity | Jolpica/FastF1/OpenF1 metadata | Calendar selection and source/session matching. Circuit name alone cannot identify an event. |
| Country/locality, race date, scheduled qualifying time, timezone | Calendar/session metadata | Navigation and display; a passed scheduled start is not evidence that qualifying finished. |
| Session name/type/key and actual activity times | Source session metadata/status | Distinguish conventional qualifying from Sprint Qualifying or another session. |
| Driver/team identities and display metadata | Number, name, abbreviation, team, team colour; optional image/country metadata | Complete roster and consistent legends. Media assets need their own permitted-use checks. |

FastF1's car position documentation uses tenths of a metre, while its pinned raw parser specifically describes that convention from 2020 onward. Verify the year/provider unit convention before converting older seasons; OpenF1's approximate coordinates also require source-specific review. No reference coordinate system establishes GPS/lateral precision merely by being numeric. MultiViewer markers are manually authored approximate annotations. [Position parser](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/_api.py), [marker contract](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/mvapi/data.py), [calendar fields](https://github.com/jolpica/jolpica-f1/blob/main/docs/endpoints/races.md).

The position parser can also extend missing rows with XYZ=0 and Status=OffTrack. Preserve the original missing-row mask. Inserted origin points must not distort the map or establish an actual off-track event.

## 9. Quantities LapDNA computes

These are project calculations. They are not additional source sensors. Implement the existing distance-v2 method and configured quality gates; a change to the method requires review/versioning.

| Output | Inputs and method | Product use |
| --- | --- | --- |
| Common track progress | Integrate native speed against the session clock; normalize to a frozen independent reference | Shared distance axis. Store the scale factor and limitations. |
| Reference map/sector/turn distances | Reference position, clocks and reviewed markers/windows | Connect maps, labels and traces; distance markers remain estimates. |
| Raw elapsed-time curves | Invert supported monotonic native distance/time | Build each lap's t(s), never force it to match desired official values. |
| Cumulative delta | delta(s) = tB(s) - tA(s) | Continuous gap-development trace; positive favours A. |
| Recorded sector differences | Recorded sector B minus A | Sector table and discrete cumulative crossing points even without telemetry. |
| Estimated 100 m local gains | delta(end) - delta(start) in separate disjoint bins | Dominance strip; not official minisector timing. |
| Corner/complex/straight contribution | Same endpoint change over the reviewed disjoint analytical partition | Additive ranking and map colour; never double-count overlapping corners. |
| Entry/exit speed comparison | Supported native input at the same reviewed region boundaries | Compare the same places, with interpolation/support disclosed. |
| Minimum/maximum regional speed | Supported native samples inside the specified window | Identify a local speed pattern; a minimum is not automatically the geometric apex. |
| Brake onset bracket | A supported native Off-to-On transition and its last-Off/first-On sample positions | Approximate onset comparison with uncertainty. Already-On at the window edge is censored, not a known onset there. |
| Throttle pickup bracket | A declared threshold and supported native samples | Approximate return to throttle; obey the existing method and gap/dwell checks. |
| Full-throttle fraction | Supported native throttle with declared threshold/weighting | Comparison within a reviewed interval, not inferred from speed. |
| Gear at marker | Supported discrete state at the same fixed reference position | Contextual gear comparison, without fractional interpolation. |
| Stable corner speed class | Frozen reference minimum in reviewed apex neighbourhood; <150 / 150–<250 / >=250 km/h | Low/medium/high labels independent of A/B selection. Mixed complexes/unknowns remain explicit. |
| Class totals | Supported disjoint regions, independent units, gross gains for each driver, net and coverage | Comparison-specific assessment, not a general driver ability or car balance diagnosis. |
| Boundary sensitivity | Repeat supported regional gains with the specified +/-10 m shifts | Robustness range; not a statistical confidence interval. |
| Comparative context | Phase pair, lap-start separation, compound/age and supported weather | Warn about differing conditions; do not adjust times with a guessed correction. |
| Evidence-backed findings | Ranked distinct regions, supported metrics, sensitivity and quality gates | Up to three observations; fewer when the evidence is insufficient. |

Optional later computations include acceleration from speed/time, coasting from both actual brake/throttle, and traffic proximity from a validated reference/time model. They need separate methods and contracts. Derived acceleration is not measured IMU/G-load; traffic proximity does not prove a tow or lost downforce. They are outside the first release.

FastF1's convenience Distance, RelativeDistance, DriverAhead and DistanceToDriverAhead are already computed channels, not independent sensors that validate these calculations. OpenF1's minisector status arrays are categorical; neither should be mistaken for an independently recorded local-time delta.

## 10. Other available data that we will not mix into the qualifying MVP

OpenF1 and other audited sources also expose race lap charts/rank, race intervals/gaps, pit-lane/stationary-stop durations, overtakes, race results/points, grid data, championship standings and some team-radio clips. These can support a later race-analysis product. Availability and definitions are endpoint-specific; OpenF1 intervals are race-only, position means rank, and location means approximate coordinates.

For qualifying, retain relevant classification and pit-in/out context. Do not download/publish radio or add a race dashboard merely because those endpoints exist. This is a scope decision, not removal of current demo features. [OpenF1 endpoint inventory](https://openf1.org/docs/).

TracingInsights additionally publishes compact aliases and processed fields. Map its dictionary into a distinct source adapter only after inspecting files, versions, native clocks and processing. Its acceleration and other derived quantities must not be promoted to native sensor data. [Archive dictionary](https://github.com/TracingInsights/2026/blob/main/DATA_REFERENCE.md).

No verified measured public field has been established for steering angle, brake pressure, brake balance, exact fuel load/flow, car setup, suspension loads, actual tyre temperature/pressure, engine torque, ERS state-of-charge/deployment, 2026 active-aero state or true lateral/longitudinal G sensors in the selected import feeds. Commercial contracts remain unverified. Keep these as unavailable leads until an exact field, units, sample, event coverage and permitted use are established. The synthetic preview retains its existing channels; none of these claims is fabricated from speed.

## 11. Quality/provenance data we must produce

Every import/comparison needs machine-readable audit data, even when it is not a headline chart:

- Exact source/provider/library version, source session, retrieval UTC, response/input hashes, pipeline commit and revision identity.
- Raw field presence, units, source update times, inherited/defaulted/interpolated/generated status and missing reasons.
- Per-driver/channel native sample counts, observed gaps, supported distance coverage, invalid values and timestamp conflicts.
- Exact selected lap IDs/phases and recorded durations; eligibility/exclusion reasons, source corrections and external timing-document revision.
- Canonical reference ID/length, layout/window/config hashes, distance scale factors, class thresholds and method version.
- Individual lap/sector residuals, raw final gap residual and interior pair residuals; retain failure/warning reasons without fixing the curve to fit.
- Per-metric native support, bounds, transition brackets, sensitivity and supporting evidence IDs.
- Dataset review/publication status, comparison capability, source freshness and limitations.
- For optional narration: evidence packet identity, prompt/model/config version, generation mode and supported finding references.

A missing optional pedal/gear channel does not erase otherwise valid timing/speed. A failure of timing eligibility can block both tiers; inadequate detailed telemetry can still permit the recorded-sector tier after its own checks.

## 12. Ordered implementation work

| Stage / existing tickets | Concrete implementation | Completion evidence |
| --- | --- | --- |
| Foundation — already implemented | Year/calendar/race studio, source audit, typed selection/result contracts, four-channel preview, missing-channel renderer and structural evidence gates | Existing local/CI checks and deployed preview. This is not a real import. |
| T01 — whole-session snapshot | First import the actual 2024 Monza conventional qualifying session. Pin source/cache/auth interfaces; preserve participants, laps, native car/position, status, tyres, weather and markers in an immutable source-specific snapshot. Capture optional RPM/DRS/traps when truly present, without new UI promises. | One real full-session import and sanitized manifest; offline tests for auth/outage/partial data, atomicity/reuse, missing car/position/weather fields, inserted position zero/OffTrack states, throttle sentinel and inherited trap values. |
| T02 — actual lap inventory | Index every driver and all actual Q1/Q2/Q3 laps; retain deleted/in/out/inaccurate/unknown-phase exclusions and context. Separate telemetry-capable, sector-only and unavailable laps. | Counts reconcile to source roster/laps. Selection tests cover eliminated driver, cancelled phase, rejected fastest, deliberate slower lap and cross-phase consent. |
| T03 — fixed reference and circuit windows | Freeze a reference independently of A/B. Review actual map, sector/turn mapping, units, layout, corner/complex/straight partition and stable class windows. | Reviewed Monza profile and marker/reference report; no invented boundary distances. |
| T04 — normalization and timing checks | Use native clocks, integrate once, preserve masks, create supported common grid/raw delta and run all lap/sector/interior reconciliation checks. | Raw residuals meet configured gates, swap invariance, truncation/gap rejection, documented independent FIA review where available. |
| T05 — comparison/evidence engine | Resolve any two eligible laps from local normalized inputs. Cache by source/lap/method/config revision. Compute both result tiers, regions, estimated bins, supported native-pattern evidence and class summaries. | Real pair outputs, additive totals, supported 0–3 observations, coverage/sensitivity checks and no channel-dependent claim when data is missing. |
| T06–T09 — production studio | Connect the existing selectors to the computed engine. Render sourced native channels, synced ruler/cursor, coloured real reference map, ranked regions, context/quality/evidence details and saved comparison state. | Desktop/mobile/keyboard checks using real artifacts, including partial channels and the sector-only path. |
| T10 — export | Dedicated PNG card and evidence JSON from the selected immutable comparison | Export retains exact lap/phase identities, source/method, estimated labels and limitations. |
| T11 — repeat on two circuits | Reuse the same engine for Silverstone and Suzuka; review each layout/window profile | Three complete inventories plus representative driver/phase/capability validations; crossover/complex handling reviewed. |
| T12 — recurring hosted publication | Keep imports outside page requests. Publish reviewed immutable datasets/results to durable host storage through a reviewed storage adapter. Keep Vercel as the studio/API delivery layer. | Fresh session can be imported/reviewed/published with the same operator steps; source outage, late correction and rollback paths work. Current function-local files are not durable storage. |
| Optional after T05 — narration | Generate wording from validated evidence, with deterministic fallback; cache by evidence/source/method/prompt/model identity | Unknown evidence/values/causal claims rejected; missing-channel/cross-phase qualifications preserved; no change to numerical facts. |
| Optional after core acceptance | RPM/historical DRS overlays, fresh trap table, richer context, then independently reviewed derived metrics | Per-field provenance, capability/schema changes and native support tests before enabling display. No inference of unavailable sensors. |

Do not close a stage with synthetic data. Keep feature commits small and descriptive, push after the stage's required checks, and update the handoff with actual evidence. Optional items are not prerequisites for the first real four-channel comparison.

## 13. Repeatable post-qualifying workflow

1. Select the exact year/event/session and verify actual session completion/status.
2. Request one whole-session import. Wait/retry within bounds if the provider has not published data; stop on access/unsupported failures.
3. Freeze native inputs and validate channel presence, clocks, phases, validity and context. Reconcile timing and review the reference/profile.
4. Publish a reviewed dataset revision. A later deletion/correction creates a new revision and invalidates dependent cached results.
5. Resolve any eligible two-driver lap selection from local inputs. Derive telemetry analysis only where supported; otherwise use the independently valid sector-only tier.
6. Generate supported text, inspect evidence and export deliberately. Optional LLM wording is never the data-processing engine.
7. Keep the prior valid publication available during upstream failure; expose ready/partial/waiting/unavailable and actual source freshness.

Provider publication delay and access can vary. The audit records expected post-session availability, not a guaranteed instant service. Scheduling an unattended importer is a later explicit operations task; this document does not create one.

## 14. Immediate next deliverable

The next feature remains T01: one reproducible full qualifying-session snapshot with a truthful field-coverage report. Inspect what was actually returned before enabling any additional panel or claim. Then complete one Monza comparison end to end before expanding circuits or optional channels.

Detailed scientific rules remain in [methodology](03-telemetry-methodology.md), wire names in [contracts](05-contracts.md), and exact ticket gates in [implementation plan](06-implementation-plan.md). Optional narrative behavior is in [analysis generation](14-analysis-generation.md).
