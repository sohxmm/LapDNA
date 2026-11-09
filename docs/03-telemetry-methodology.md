# Telemetry methodology

Current prefinal decision: [verified native release and conditions policy](20-verified-telemetry-release.md) supersedes dry-only eligibility. Measured wet telemetry is supported with explicit conditions context; native/missing masks, fixed reference and raw numerical quality gates are unchanged.
The original implementation specification uses method identifier `distance-v2`. The implemented Monza pilot uses **`distance-v3-openf1-native-composite`**, preserving the numerical thresholds, sign convention and quality fallbacks below. It has been exercised on real qualifying comparisons; this does not establish precise corner ground truth or validation for every circuit.

### Implemented provider decision — 8 November 2026

Native OpenF1 car/position streams are joined only after identity/timing checks to original TracingInsights/FastF1 lap clocks, phases and validity flags. Unknown flags, native masks and every raw timing residual are preserved; no time or sector fitting is introduced. OpenF1 geometry retains explicit source units rather than an assumed metre conversion; the analytical distance axis remains integrated speed. Schema 1.3.0 records component URLs/hashes/licences and actual native provider field names while accepting legacy 1.2.0 results. Earlier FastF1-only adapter descriptions below remain the direct-adapter specification, not a claim that this composite was downloaded through FastF1. [Exact source/quality decision and pilot limits](19-monza-2024-pilot.md).

The prior user milestone [R01](16-results-first-milestone.md) now serves recorded qualifying classifications and same-phase duration differences. It does not run distance-v2 or establish any corner/telemetry evidence. Historical and SQ classification fields live in separate contracts; future native SQ/lap support needs explicit per-lap contract and eligibility review.

## 1. What the product can claim

The official recorded lap gap answers **how much** time separated the laps. LapDNA estimates **where** that gap developed and shows simultaneous channel patterns. A channel difference is evidence of an observed pattern, not proof of its cause. Fuel load, setup, wind, traffic, grip, electrical deployment and line choice remain uncontrolled.

Use these phrases consistently:

- **Official lap/sector time:** recorded timing value delivered through FastF1; store source provenance. The release validation pack separately checks selected examples against the event's published classification/timing documents.
- **Estimated local gain:** difference between two elapsed-time curves across the same canonical distance interval.
- **Approximate track distance:** a normalized integrated-speed coordinate; it is not a surveyed centerline or an exact common physical location for both cars.
- **Observed braking onset:** a transition in an on/off signal, reported as an interval between samples.
- **Data checks passed:** the checks in this document passed; it does not mean the intermediate curve is accurate to the displayed millisecond.

FastF1 provides native car and position streams, including speed, throttle, gear, RPM, DRS and brake on/off. Its listed channels do not provide steering angle or brake pressure. Position coordinates use tenths of a metre. Prefer native streams over merged convenience telemetry for computation. The supplied broadcast image is an interaction/layout reference, not proof that every illustrated channel is available. [Pinned FastF1 channel definitions](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py)

### 1.1 Data tiers and honest fallback

The numerical result is one of two explicit capabilities:

- **Telemetry comparison:** both laps support the aligned raw-time curve. It can show distance traces, turn labels, derived minisectors, segment gains and supported corner-class findings. Individual optional channels can still be missing.
- **Sector-only comparison:** eligible recorded lap/sector timing exists, but telemetry is unavailable or cannot pass the alignment gates. It shows official sector durations, sector gaps and cumulative gap at the timing boundaries only. It cannot show a continuous distance delta, a colored performance map, per-corner gains, estimated minisectors or corner-class performance conclusions.

For sector-only mode calculate `sector_delta_ms[k] = sector_B_ms[k] - sector_A_ms[k]` and `cumulative_delta_ms[k] = sum(sector_delta_ms[0:k+1])` for zero-based sector index k. Show the recorded lap gap, sector-sum residual and `fallback_reason`. Plot discrete points labeled S1, S2 and Finish on a categorical axis. Do not spread a sector gap evenly over distance, connect it with a curve suggesting measured interior values, or manufacture turn positions from it. The MVP sector-only result omits spatial data entirely.

FastF1 remains the first adapter. OpenF1 is an investigated optional source for sector timing, with its own source provenance and eligibility mapping before use. Its `segments_sector_*` arrays are mini-sector status/color codes, not durations; they cannot supply numeric head-to-head delta. Do not convert green/purple into a guessed number of milliseconds. [OpenF1 lap definitions](https://openf1.org/docs/#laps)

If neither valid timing nor valid telemetry is available, return unavailable with the actual reason. A fallback is a lower capability, not repaired telemetry. There is no verified public source for the exact higher-frequency steering/brake-pressure dataset shown in the reference image within this project.

## 2. Fixed scope and identifiers

MVP imports completed conventional qualifying (`Q`) for Monza, Silverstone and Suzuka. Begin validation with each circuit's 2024 qualifying event; these are candidate datasets, not promises of availability or suitable pairs. The importer resolves the event through the schedule and records the round and circuit key. Never hardcode an unverified round from memory.

Keys must distinguish season, round, session, circuit layout/version, driver number and lap number. Use driver number as a string; display abbreviation is metadata, not a stable database identity. A comparison contains exactly two different drivers from the same qualifying event and layout. All imported participants and all eligible laps are selectable; no fixed four-driver or six-pair restriction remains. No sprint, race, wet/dry mixing, cross-year lap comparison or cross-layout comparison is in this release.

Default to the highest phase common to the chosen drivers with eligible laps, then the fastest eligible lap for each in that phase. Each lap stores its own phase. Allow explicit lap selection and independent Q1/Q2/Q3 controls for A and B. Selecting different phases requires `allow_cross_phase=true`; retain a persistent warning that track evolution and conditions differ. Never silently replace a requested phase with another or invent a Q3 lap for an eliminated driver. If there is no common phase, explain this and offer explicit cross-phase selection rather than auto-mixing. Equal `LapTime` ties use lower lap number.

Pair context records same-phase versus cross-phase, both phases, lap-start UTC when available, time separation, compound/tyre age and material weather/track warnings. Cross-phase numeric comparison is allowed when both laps independently pass eligibility, but its language is limited to **these selected laps**. Do not infer that the resulting pattern establishes an enduring driver/car strength. A weather mismatch or otherwise blocked lap cannot be bypassed by the cross-phase opt-in.

## 3. Import, eligibility and provenance

### 3.1 Import sequence

1. Resolve an allowlisted season/event/session to an exact upstream identifier.
2. Open a project-local FastF1 cache. Load timing, telemetry, weather, session status and race control messages through the installed public API. Record the exact FastF1 version and import timestamp.
3. Obtain Q1/Q2/Q3 membership with `split_qualifying_sessions()`. If phase membership is unavailable or ambiguous, stop publication of that session rather than infer phases from lap order.
4. Retain a lap index for every participant and all Q1/Q2/Q3 laps, with timing eligibility, telemetry eligibility and machine-readable exclusion reasons, including rejected laps.
5. Validate car data and position data separately. Preserve native timestamp/value records as the audit inputs outside Git.
6. Freeze one session geometry/reference version and normalize each eligible lap once. Publish the full imported inventory; a missing phase/lap remains visibly unavailable.
7. The request path compares explicitly selected normalized local laps with bounded computation and caches immutable results by the complete inputs/method identity. It must never contact upstream to fulfill a comparison. Previously prepared artifacts remain useful as examples/cache entries, not the limit on allowed pairs.
8. Validate session inventory and derived results before promotion. A failed import leaves the previous usable session revision intact. Distinguish session-not-imported, lap-unavailable, computation-not-implemented and genuine data-quality failures.

Race control data is necessary to evaluate deleted laps, and `IsAccurate` is a timing integrity flag rather than a blanket telemetry-accuracy guarantee. [Timing reference](https://github.com/theOehrly/Fast-F1/blob/main/docs/api_reference/timing_data.rst) Phase splitting also depends on session status. [FastF1 phase implementation](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/core.py)

### 3.2 Publication eligibility

The timing eligibility checks apply to both result tiers; native coverage and speed/time checks additionally gate the telemetry tier:

| Check | Required outcome | Failure behavior |
| --- | --- | --- |
| Recorded lap and all three sectors | Finite, positive durations | Exclude lap |
| `Deleted` | Explicitly false, with race control loaded | Unknown is not false; exclude |
| `FastF1Generated` | Explicitly false | Exclude |
| `IsAccurate` | Explicitly true | Exclude; retain reason |
| Pit in/out | Both absent | Exclude |
| Phase | One known Q phase | Exclude |
| Track status | Green throughout for the initial release | Exclude other/unknown states |
| Tyre | Known dry compound | Exclude wet/intermediate/unknown |
| Native car coverage | Brackets both timing boundaries, acceptable gaps | Exclude from aligned telemetry |
| Speed/time integrity | Satisfies section 5 | Exclude from alignment |
| Timing consistency | Satisfies applicable section 7 checks | Warn or block the affected tier as specified |

Same phase does not mean same conditions. Display compound, tyre age, lap start UTC/time-of-day, and elapsed time between the laps. Different dry compounds or tyre ages are a visible comparison-context warning, not an automatic claim about tyre performance. Cross-phase requests always add that context warning even if sampled weather appears similar. Do not infer wetness from a dry compound alone; rain/weather/track context can also trigger review.

No silent fallback from a rejected fastest lap: label the chosen result **fastest eligible lap** and retain a reason if it differs from the official phase best. Classification order and lap availability are separate concepts.

### 3.3 Provenance record

Store the source identifier, source session identifier, import UTC, FastF1 version, pipeline commit, methodology version, circuit-config hash, canonical-reference lap ID, native-input hash, output hash, units, all thresholds, and dataset review status. The served-artifact contract currently accepts only `provenance.source = fastf1`; a future browser demo fixture would need an explicit synthetic source value and prominent UI labelling. Keep software and input versions independent. Reimports may change upstream lap validity; publish a new revision rather than mutating an old comparison.

Unit tests use artificial inputs and UI examples must display their synthetic status. The live historical-source availability probe is recorded separately in the [source register](09-sources.md). Its sampled response is evidence of data availability only. The real comparison pipeline still requires a complete validated session import.

## 4. Canonical distance and time conventions

### 4.1 Freeze a reference independently of A/B selection

After eligibility and coverage checks, sort all session laps by official lap time, driver number, then lap number. Freeze the first lap with usable position geometry as `reference_lap_id`. Record its integrated length `L` and map geometry. The selection is made once for a dataset revision, not whenever the user changes or swaps drivers. If it fails geometry review, choose the next lap and record why.

`L` is this method's reference length in metres. Display approximately rounded distances; do not relabel it as the officially published circuit length. Publish changes to the reference as a new geometry version. A/B swapping must preserve x positions, windows and segments exactly.

### 4.2 Use the session clock explicitly

For lap `i`, define `start_i = LapStartTime` and `end_i = Time` from its timing record. Native elapsed timestamps are `tau_i = car.SessionTime - start_i`. Do not zero the first telemetry sample: it can lie before or after the timing line. Keep UTC metadata separately.

FastF1's time documentation distinguishes a session-relative clock from the slice-dependent telemetry `Time` column. [Time definitions](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/time_explanation.rst)

### 4.3 Integrate once on native samples

Retrieve car data with one native sample of padding on each side. Do not request a high-frequency merged stream. After the integrity rules below, compute cumulative distance in float64:

```text
v_j = speed_kph_j / 3.6
D_0 = 0
D_j = D_(j-1) + (v_(j-1) + v_j) / 2 * (tau_j - tau_(j-1))
```

Evaluate `D(start_i)` and `D(end_i)` within their bracketing native intervals by integrating the interval's linearly interpolated speed, not by extrapolation. This avoids integrating artificial full-grid samples. Define:

```text
length_i = D(end_i) - D(start_i)
distance_i(t) = L * (D(t) - D(start_i)) / length_i
```

This total-length normalization is an explicit approximation: different paths and integrated-speed errors are compressed into one shared progress axis. Store `length_i` and scale factor `L/length_i`. Warn when the scale differs from 1 by more than 1%; block above 3% pending review. These are engineering guardrails, not track-length accuracy bounds.

Only add the exact timing-edge samples after computing the native integral. They contain estimated speed/channel values and elapsed time `0` or `end_i-start_i`. Preserve the fact that the timing edges were imposed. If either edge lacks native bracketing data, the lap is ineligible; never pad a truncated lap by copying its final sample.

FastF1 cautions that sparse, jittery data, repeated interpolation and integration introduce errors. LapDNA's distance normalization is a deliberately limited approximation, checked against timing and tested for sensitivity. [Calculation guidance](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/howto_accurate_calculations.rst)

### 4.4 Shared grid and channel interpolation

Create `distance_m = sorted(unique([0, 5, 10, ..., floor(L/5)*5, L, segment boundaries, sector boundaries, minisector boundaries, reviewed turn markers]))`. Record a nominal spacing of 5 m. The final interval and explicitly inserted boundaries may be shorter. The native sampling rate still determines measurement support.

Invert the monotone native `distance_i(t)` with piecewise linear interpolation to get `time_ms_i(s)`. This mathematical notation maps to each driver's wire field `time_raw_ms`; there is no adjusted-time series. No cubic splines. Evaluate continuous channels at the same distance using their native support. Use the same transformations for both drivers.

| Channel | Unit/output | Resampling rule |
| --- | --- | --- |
| Elapsed time | milliseconds, float64 internally | Linear on monotone distance; invalid outside support |
| Speed | km/h | Linear; never smooth for numerical evidence |
| Throttle | percent | Linear; invalid out-of-range source values become missing |
| Gear | integer or null | Previous native observation, zero-order hold |
| Brake | boolean or null | Previous native observation, zero-order hold |
| Map X/Y | metres after unit conversion | Separate position stream, interpolated for drawing only |

Step channels must not show fractional gears or fractional brake application. Unknown brake is not `false`. To make transition ambiguity visible, retain original bracketing sample times/distances for event extraction even when a step trace is drawn.

### 4.5 Sign convention

```text
delta_ms(s) = time_ms_B(s) - time_ms_A(s)
official_gap_ms = official_lap_ms_B - official_lap_ms_A
gain_ms([a,b]) = delta_ms(b) - delta_ms(a)
```

Positive delta means A is ahead at that distance. Positive segment gain means A gained time through that interval. Negative values mean B. A driver may gain in a segment while still behind on cumulative time. Put this wording on legends and use it in tests.

Swap A/B by swapping displayed lap metadata and channel series and negating delta, official gap and gains. Generated observation text must name actual driver codes or names, never positional `A`/`B` placeholders, so the same supported claim remains correct after a view swap. Keep that identity-based text unchanged; swap evidence readout columns and colors. Never edit prose by string substitution. Ranking by absolute gain remains unchanged.

## 5. Missing data, gaps and physical sanity

Implement checks before interpolation:

1. Require finite native timestamps. Sort chronologically, retain exact duplicate rows once, and fail a lap with conflicting values at the same timestamp. Record the original order anomaly.
2. Accept finite speed in `[0, 400]` km/h as a broad sanity range; an invalid value is not clamped. If a missing/invalid sample can be omitted while the remaining bracketing span is at most 0.75 s, integrate across that span and flag it. A longer span blocks the entire lap alignment because the distance error would persist downstream.
3. Require at least two native samples and positive integrated length. Reject any non-increasing distance after duplicate-time handling; a stationary plateau in a supposed clean qualifying lap needs review, not a numerical epsilon.
4. Track each original gap. A resampled point bracketed by a span above 0.50 s is low-support, even if alignment remains possible. Such an interval cannot support a corner observation.
5. Treat invalid throttle, missing brake, and unsupported gear independently. Mask the affected channel across a gap rather than erasing good speed/time data. Gear 0 may be represented as neutral but cannot support a normal corner-gear claim.
6. Do not silently repair spikes with a smoother. Keep a review flag for implausible isolated jumps, frozen multi-channel runs or geometry discontinuities. Detection thresholds must be recorded and covered by synthetic cases; channel constancy alone is not a failure because full throttle and top gear can be legitimately constant.

JSON uses `null` for missing values, never NaN/Infinity. A point/interval support mask accompanies each evidence channel internally; the serialized schema may carry null arrays plus interval warnings. Validity must be visible as trace gaps and map hatching. No interpolation across an invalid interval and no unbroken SVG path through a null.

## 6. Circuit geometry, corners and straight summaries

### 6.1 Geometry

Interpolate the reference lap's *position stream* onto reference native session times only to associate geometry with canonical distance; this is for drawing, not for recomputing speed or timing. Convert X/Y to metres once, apply the circuit rotation once, center and scale in the client while preserving aspect ratio. Geometry must close visually at the start/finish line without drawing a long artificial final chord; review closure distance and mark an invalid map if necessary.

Project corner marker positions onto this reference polyline in known corner order, resolving self-crossings using local distance neighborhoods. Use supplied marker numbers and letter suffixes as labels. Do not blindly trust their precomputed distance against a different reference lap. Suzuka's crossing is a specific test case: nearest X/Y alone can select the wrong branch.

Store marker number, label and canonical distance independently of performance segments. These exact marker distances label the shared telemetry ruler and all panels, including delta; do not space turn numbers uniformly or attach them to each driver's separate speed minimum. Label collision handling changes text placement only, not the underlying distance. Selecting T7 may highlight a containing T6–T7 complex; report the complex's supported gain rather than pretending it belongs uniquely to T7.

The marker dataset is intended for annotation and is manually constructed, with approximate rather than survey-grade placement. It includes corner and marshal markers; marker distances are computed from a reference lap. [CircuitInfo source](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/mvapi/data.py)

### 6.2 Versioned segment configuration

For each supported circuit/layout, add a reviewed segment configuration after seeing its imported map. Every segment has stable ID, label, type (`corner`, `complex`, `straight`), start/end distance, associated marker IDs, and optional entry/apex/exit subwindows. Do not invent numeric boundaries during scaffolding.

The required **summary partition** covers `[0,L]` exactly once with adjacent non-overlapping intervals. Half-open intervals own samples `[a,b)`; the final interval includes `L`. This makes gains additive without double-counting. Nearby corners can be grouped into a complex when their braking and acceleration zones overlap. Do not claim their total gain independently for each constituent corner.

Create a proposed initial partition using corner groups, then review on the reference traces. Corner windows must include braking approach and the agreed exit region; straight windows fill the complement. Keep any deeper overlapping inspection windows out of the additive ranking. Store their relationship to the partition explicitly.

For a lap-wrap complex, split it into `[0,b]` and `[a,L]` partition segments linked by a `group_id`; aggregate their gains only once in an optional group summary. All API ranges remain non-wrapping.

### 6.3 Segment metrics

For each segment, calculate elapsed time of A/B, local gain, speed at entry and exit boundaries, minimum native-supported speed, maximum speed, observed brake-on distance, full-throttle recovery distance, and gear at a defined marker. Calculate metrics on unrounded values; round only for display. A missing required subwindow produces null, not a fallback fabricated apex.

Entry and exit speed samples require valid support for both drivers at the same boundary. “Minimum speed” is a minimum within the configured interval, not necessarily a geometric apex. A gear comparison uses a fixed marker position, not each driver's separate minimum-speed point.

Boundary movement sensitivity: recalculate each segment gain for allowed boundary shifts of -10/0/+10 m, clipped so the segment remains valid. Retain min/max values. These are a robustness check, not statistical confidence intervals.

### 6.4 Map colour

The primary map colours each reviewed partition segment by `gain_ms`, with a diverging A/neutral/B scale and textual legend. This exactly matches the corner/straight ranking. Saturate colour at a documented display limit, show actual values in the tooltip, and retain a neutral band for gains below the observation floor. Unknown is hatched, never neutral.

Do not colour by cumulative delta: a driver who gained earlier would otherwise appear faster on a later section where they are losing time. A separate **Estimated 100 m minisectors** strip/map mode is part of this revision, using the non-overlapping bins below. The selected mode and legend must distinguish it from corner/straight summaries.

### 6.5 Estimated minisectors

Build a second, independent partition with edges `0,100,200,...,floor(L/100)*100,L`, removing a duplicate endpoint. Insert these edges into the grid. For bin `[a,b]`, return `gain_ms=delta_ms(b)-delta_ms(a)` only with full valid elapsed-time support across that bin. Otherwise return null and retain the reason in the quality report. The `estimated_minisectors` wire entries contain `start_m`, `end_m`, `gain_ms` and `source=derived_telemetry`. A/B traversal durations are recoverable from the existing elapsed-time arrays at the same edges. The last bin may be shorter. The v1.1 contract fixes this project-defined bin width at 100 m. A future change requires a method/schema revision.

The local-dominance strip colors bins by sign and magnitude of that local gain, with unknown hatching and a labeled neutral threshold. Use a 10 ms neutral display band initially; this is visual suppression of tiny estimates, not the 30 ms evidence floor. A visible bin is not automatically eligible for a written claim. Provide numeric tooltip and overlap turn labels, but do not assign a bin's full gain to every turn it touches.

For a fully supported lap, the minisector partition telescopes to the raw final delta. The corner/straight partition independently telescopes to the same value. Never add both partitions together. A continuous curve must come from aligned telemetry, not interpolation of these bin totals or official sector endpoints. Optional source mini-sector status colors, if ever displayed, require a separate labeled view; they are not this dominance strip.

### 6.6 Stable corner-speed classification

Classify the circuit profile once using the frozen reference lap. Store `classification_rule=reference_apex_minimum_v1`, config version, reference lap ID and speed evidence. Selecting a slower lap or swapping A/B must preserve each corner's category.

Each reviewed corner marker has an apex-neighborhood interval inside its analysis region. The scalar `reference_speed_kph` is the minimum valid **native reference** speed in that interval, not an interpolated minimum on the 5 m grid and not necessarily the geometric apex speed. Require at least three native speed samples and no supporting timestamp span above 0.50 s. Evaluate the same window with its boundaries shifted by -10/0/+10 m within the profile limits; if the category changes, or the window lacks support, use `unknown` and record the reason.

The initial project thresholds are:

| Class | Reference window minimum |
| --- | --- |
| Low speed | `<150 km/h` |
| Medium speed | `>=150 and <250 km/h` |
| High speed | `>=250 km/h` |
| Unknown | Missing/unstable classification support |

These are configurable editorial categories, not FIA standards or proof of aerodynamic/mechanical behavior. Show the thresholds in the analysis details. Do not re-tune them for an individual comparison. A profile revision that changes thresholds or windows invalidates category summaries and cache identity.

Attach each additive corner segment to one class. A complex whose constituent corner markers all share one supported class may use that class. A complex containing different classes is `mixed`; an unresolved/missing constituent is `unknown`. Do not split an overlapping complex just to force a neat speed-category result. Straights have no corner-speed class. Linked pieces of a lap-wrap complex form one independent analysis unit with combined gain, sensitivity and support; include their metres once each and count the unit once.

### 6.7 Category aggregates and comparison-specific interpretation

`classify_reference_corners(profile, native_reference, settings)` produces frozen corner classes; `aggregate_corner_classes(segments, evidence, classes, settings)` produces the comparison summary. These functions are separate: only the second depends on A/B.

For each low/medium/high category, expected units are the disjoint corner/complex analysis units assigned that class. A unit is supported if all its component segments have valid elapsed-time support, known gain and sensitivity, at least five native car observations per driver, and maximum supporting span <=0.50 s. Excluded units remain in expected counts/length; never discard them from the denominator to inflate coverage.

For supported unit gains `g_j` in the established A-favoring convention:

```text
gains_a_ms = sum(max(g_j, 0))
gains_b_ms = sum(max(-g_j, 0))
net_gain_ms = gains_a_ms - gains_b_ms
coverage_fraction = supported_expected_length / total_expected_length
```

In `analysis.categories`, emit `included_segment_ids`, `excluded_segment_ids`, `independent_units`, `distance_coverage`, `a_wins`, `b_wins`, `neutral_units`, gross gains in both directions, net gain, `sensitivity`, `assessment` and `evidence_ids`. Derive expected and excluded unit counts by grouping the ID lists by `group_id` (or segment ID for ungrouped segments). Sum component lengths for expected and covered distance. If any linked group member fails support, exclude the entire group. Sensitivity lower/upper bounds are sums of unit minima/maxima. Their width describes variation under the prescribed boundary shifts. Unit neutral/material classification uses its own `max(30 ms,2*unit_sensitivity_spread)` threshold and stable sign. `gains_a_ms`/`gains_b_ms` include all supported numeric gains, including neutral ones, so arithmetic still reconciles.

An empty selection returns `insufficient` with null performance totals and sensitivity. When the expected length is zero the wire coverage is 0 and the table reads “No corners in this class.” For partial coverage show both supported and expected counts. A directional `a_advantage` or `b_advantage` assessment requires >=80% expected distance coverage, a stable aggregate sign, `abs(net_gain_ms)>=max(30 ms,2*aggregate_sensitivity_spread)`, at least two independent material wins for that driver and at least two-thirds of material units favoring that direction. Describe any material opposite-sign units as exceptions. With adequate coverage and support, use `balanced` when all units are neutral and `mixed` for offsetting wins/losses without a qualifying directional pattern. Use `insufficient` when missing support, sample count or sensitivity prevents classification.

Scope prose to the selected laps, e.g. “Across the {n}/{expected} supported high-speed corner regions, {driver} gained an estimated {net}. The low-speed regions favored {other_driver} by {loss}.” Link both rows and their contributing segments. Include gross gained/lost values when cancellation hides mixed behavior. Emit `pattern=high_medium_gain_low_loss` for `pattern_driver=A` or `B` only with complete coverage of all three classes, at least two independent material wins in the required direction per class, stable net gains in high/medium, stable net loss in low, and zero opposite material units in every asserted class. The wording always refers to classified, supported corner regions. Report mixed/unknown regions separately. A circuit-wide exclusivity claim additionally needs every corner unit classified and supported.

The category analysis is a separate structured section from the three local observations. It does not consume three slots by restating one aggregate. It is deterministic metric interpretation, tailored to the selected laps; no runtime language model is needed to decide the facts. It must never conclude “better aerodynamics,” “poor mechanical grip,” “braver driver,” or a persistent driver trait from a single pair. Cross-phase analysis includes the phase/time/conditions warning in the section and export.

## 7. Reconciliation without circular validation

### 7.1 Keep three checks separate

**Timing-record consistency.** For each lap compare `sum(Sector1Time..Sector3Time)` with `LapTime`, and `Time-LapStartTime` with `LapTime`. The first tests integrity of the timing metadata; the second tests consistency of the clock used to slice telemetry. Neither independently establishes corner accuracy.

**Interior common-distance consistency.** From the frozen reference lap, map `Sector1SessionTime` and `Sector2SessionTime` through its distance transform to get fixed canonical `s1` and `s2`. These are estimated spatial positions of official timing crossings. They are not the `marshal_sectors` markers. If a sector timestamp is absent, mark the interior check unavailable and block curated publication until resolved.

For each compared lap `i`, record:

```text
official_cumulative_i(k) = sum(official_sector_i[1:k])
residual_i(k) = time_ms_i(s_k) - official_cumulative_i(k)
pair_residual(k) = delta_ms(s_k)
                  - (official_cumulative_B(k) - official_cumulative_A(k))
```

Evaluate individual and pair residuals: large individual errors must not cancel into a misleading small pair error. A reference-lap residual uses a location derived from itself; tag its basis `calibration`, not independent validation. Non-reference laps provide cross-lap consistency evidence, still limited by the estimated sector locations.

**Endpoint accounting.** At `L`, time equals the timing-sliced duration by construction. Store the residual against official lap gap, but label its basis `timing_constraint`. A zero final residual does not validate the curve between the endpoints. Do not rescale elapsed time, pin sector values, or distribute residuals invisibly. The official headline and estimated curve remain distinct.

### 7.2 Initial severity policy

These telemetry-tier defaults must be checked on the three real validation datasets before release. Changing them requires a methodology/config version, before/after evidence and updated fixtures. Sector-only results apply timing-record consistency checks and explicitly lack the interior-distance checks; unavailable telemetry checks must not be reported as passed.

| Metric | `pass` | `warn` | `block` |
| --- | --- | --- | --- |
| Absolute sector-sum versus official lap | <=3 ms | >3 and <=20 ms | >20 ms or missing |
| Absolute sliced duration versus official lap | <=3 ms | >3 and <=20 ms | >20 ms or missing |
| Max absolute interior individual/pair residual | <=50 ms | >50 and <=150 ms | >150 ms or unavailable |
| Absolute distance scale deviation | <=1% | >1 and <=3% | >3% |
| Native speed/time gap | <=0.50 s | >0.50 and <=0.75 s | >0.75 s |

Take the worst applicable severity within the selected capability. `pass` means the applicable checks passed, not an accuracy guarantee. `warn` may be browsed with a persistent explanation and residual table; shared publication includes that warning and requires dataset review. A telemetry-tier `block` suppresses all local claims. If timing separately remains eligible, return an explicit sector-only result; otherwise keep the rejected result in the operator report and show unavailable. Never downgrade a timing-integrity failure into an apparently successful fallback.

Keep thresholds separate from output precision. Official values can display 0.001 s; local gains ordinarily display about 0.01 s and the word **estimated**. Never advertise “millisecond-accurate corners.”

### 7.3 External validation pack

For each seed event choose at least one close pair and one wider-gap control pair, plus a deliberately rejected lap. Record official lap and sector values, event document URLs, source retrieval date, chosen lap/phase IDs, all residuals, boundary-sensitivity results, native sample spacings and screenshots. A race-result page alone does not validate sectors. If only classification is available, mark the sector cross-check as feed-only, not independently verified.

No chosen candidate pair is “validated” until this pack exists and a human has inspected its map/markers and three observations. Do not widen thresholds merely to force a demonstration through a gate.

## 8. Three evidence-backed observations

### 8.1 Deterministic evidence, not a language-model inference

Generate observations in Python from metrics. Every sentence must be reproducible from structured evidence: segment ID/range, metric name, A/B values, signed difference, native support count, data flags, and a template version. Clicking an observation selects exactly that interval in map, table and charts.

Require full valid elapsed-time support across its segment, at least five native car samples per driver within it, no support span above 0.50 s, and a robust gain. Initial material-gain rule:

```text
abs(gain_ms) >= max(30 ms, 2 * boundary_shift_spread_ms)
```

Here `boundary_shift_spread_ms` is maximum minus minimum gain under the specified shifts. This is a conservative selection rule, not a probability model. Suppress direction statements when sensitivity variants change sign.

Rank eligible segments by absolute gain, ties by start distance. Select at most one observation from each disjoint partition segment. Prefer one corner/complex, one straight and then the next largest independent segment; if either category has no supported finding, fill from the remaining ranked segments. Never fabricate a “different” third claim by restating the same segment.

### 8.2 Supported templates

| Template | Required evidence | Allowed wording |
| --- | --- | --- |
| Segment gain and minimum speed | Robust local gain, native-supported minima | “A gained an estimated 0.08 s through T1–T2; the minimum recorded speed was 4 km/h higher.” |
| Exit and following straight | Segment gain, common exit boundary and straight-end speed | “A gained an estimated 0.06 s on the following straight, with a 3 km/h advantage at the configured exit point.” |
| Braking timing pattern | One sustained off-to-on transition per driver in same approach, bracket intervals | “A's observed brake-on interval occurred about 15–25 m later; A gained an estimated 0.04 s across this segment.” |
| Throttle recovery pattern | Sustained threshold recovery after minimum-speed region | “A returned to at least 95% throttle earlier in this exit window; the segment gain was approximately 0.05 s.” |
| Gear choice at marker | Both gears valid at same marker and stable through adjacent native observations | “At the T7 marker, A was in fourth gear and B in third; A gained approximately 0.03 s across the configured window.” |

Numbers and A/B labels above are illustrative, not event findings. Published template text uses actual driver codes/names so view swapping cannot change its meaning. A pattern can accompany a gain in the opposite direction; templates must report that honestly. Never write “because,” “braked harder,” “better traction,” “more downforce,” “driver error,” or “caused the loss” from these channels alone.

Brake transition definition: find a false-to-true transition followed by at least two true native observations spanning at least 0.20 s in the configured approach. Onset lies between the last false and first true sample. If both drivers' intervals overlap, do not claim one braked later. Derive the possible onset-distance difference interval from the interval endpoints; round outward to 5 m. Multiple unresolved braking episodes suppress the template.

Throttle recovery definition: first native sample at or above 95% after the configured low-speed subwindow, remaining at or above 95% for at least 0.40 s with at least three native observations. Report the threshold-crossing bracket, not an exact pedal application instant. These thresholds are product choices.

### 8.3 When fewer than three findings qualify

The normal meaningful output has three supported observations. The evidence constraint outranks the count: return zero to three observations plus an explicit `insufficient_evidence` reason. The UI shows a neutral information panel for an unfilled slot; it must not label that panel as an observation. A curated launch fixture should be chosen to produce three legitimate findings. A quality warning can itself be displayed, but does not count as a performance finding.

## 9. Numerical test matrix

Use synthetic arrays for deterministic tests and a separately downloaded small real validation pack for acceptance. CI must not depend on live network availability.

| Case | Required assertion |
| --- | --- |
| Identical laps | Delta/gains zero, observations absent |
| Known constant speed pair | Analytical elapsed delta matches tolerance |
| Swap A/B | Exact sign reversal, identical grid/geometry/ranking |
| Partition accounting | Sum segment gains equals delta(L)-delta(0) within floating-point tolerance |
| Boundary insertions | Correct 0/L inclusion, no duplicate grid coordinates |
| Missing lap boundary | No extrapolation; telemetry blocked, sector-only fallback only if timing independently eligible |
| Conflicting duplicate timestamp | Explicit rejection |
| Long speed gap | Whole alignment blocked, not only the visible hole |
| Missing brake only | Timing usable; brake observation absent; null not false |
| Gear transition | No fractional gear; previous-value semantics checked |
| Bad throttle value | Masked with reason, never clamped to 100 |
| Official-sector perturbation | Raw curve unchanged, reconciliation severity changes |
| Forced endpoint match | Still labelled timing constraint; no accuracy upgrade |
| Individual residual cancellation | Pair pass cannot hide individual failure |
| Reference-lap interior check | Labelled calibration, not independent validation |
| Overlapping/wrapping segments | Partition validation rejects overlaps; wrap represented explicitly |
| Suzuka crossing | Ordered marker mapping selects correct branch |
| Thin native support | Dense 5 m grid does not satisfy sample-count gate |
| Observation language | Every number resolves to evidence, templates avoid causal wording |
| Missing third finding | Fewer than three returned, no invented prose |
| Independent phase selection | Q1/Q2/Q3 stored per lap; cross-phase requires opt-in and persistent context warning |
| Eliminated driver | Missing Q2/Q3 remains unavailable; no substitution |
| Complete session inventory | Any valid imported driver/lap pair is selectable without a prebuilt-pair whitelist |
| Sector-only fallback | Only categorical timing-boundary deltas; no synthesized distance arrays or turn gains |
| Mini-sector status codes | Never interpreted as durations or pair delta |
| Estimated minisector accounting | Independent partition telescopes; never added to corner-partition totals |
| Class boundary speeds | 150 belongs to medium, 250 to high; unstable window variants yield unknown |
| Class invariance | Driver/lap selection and A/B swap preserve reference classes |
| Mixed complex | No forced assignment from only its slowest constituent; excluded from class claim |
| Category cancellation | Gross gains/losses and material unit counts reveal a mixed pattern despite small net |
| Incomplete category coverage | Denominator retains excluded units; insufficient evidence cannot be labeled balanced |
| Wrapped category unit | Both pieces counted in length/gain, but independent-unit count increases once |
| Category exclusivity | “Only high/medium” suppressed unless every stated completeness/sign gate passes |
| Serialization | Finite numbers/null, equal array lengths, valid ranges, stable hash |

Recompute the same inputs/config twice and compare canonical artifact hashes excluding operational timestamps. All rounding happens in presentation. A numerical pipeline change increments the methodology version and regenerates reviewed artifacts.

## 10. First importer handoff

Implement in this order: resolve/import/cache full session → complete lap/phase inventory and tier eligibility → native-channel checks → canonical reference and classification → grid interpolation → raw delta → official reconciliation → independent corner/minisector partitions → metrics/category summaries → observation templates → bounded local pair resolver/cache → reviewed publication. Implement sector-only arithmetic separately so it cannot accidentally inherit telemetry claims. Do not begin interpretation templates until reconciliation and coverage reports are inspectable.

The analysis extra pins FastF1 3.9.2. Its request implementation uses `Cache.configure` and a Formula 1 account authentication adapter; the first importer ticket must exercise that supported flow and check actual seed-event availability. [FastF1 3.9.2 request implementation](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/req.py) General `main` documentation can still move independently of the release. If upstream access is unavailable, keep the empty-data workspace and offline tests usable and report the actual access failure without substituting invented real telemetry. Do not persist user credentials in artifacts or logs.
