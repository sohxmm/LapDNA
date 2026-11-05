# Telemetry methodology

Status: implementation specification; numerical thresholds below are proposed project policy, not measured accuracy claims. No real comparison has been validated by this scaffold. Method identifier: `distance-v1`.

## 1. What the product can claim

The official recorded lap gap answers **how much** time separated the laps. LapDNA estimates **where** that gap developed and shows simultaneous channel patterns. A channel difference is evidence of an observed pattern, not proof of its cause. Fuel load, setup, wind, traffic, grip, electrical deployment and line choice remain uncontrolled.

Use these phrases consistently:

- **Official lap/sector time:** recorded timing value delivered through FastF1; store source provenance. The release validation pack separately checks selected examples against the event's published classification/timing documents.
- **Estimated local gain:** difference between two elapsed-time curves across the same canonical distance interval.
- **Approximate track distance:** a normalized integrated-speed coordinate; it is not a surveyed centerline or an exact common physical location for both cars.
- **Observed braking onset:** a transition in an on/off signal, reported as an interval between samples.
- **Data checks passed:** the checks in this document passed; it does not mean the intermediate curve is accurate to the displayed millisecond.

The source distinguishes native car and position streams, identifies brake as boolean, and treats gear as discrete. Position coordinates use tenths of a metre. Prefer the native streams over merged convenience telemetry for computation. [FastF1 channel and access definitions](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/core.py)

## 2. Fixed scope and identifiers

MVP imports completed conventional qualifying (`Q`) for Monza, Silverstone and Suzuka. Begin validation with each circuit's 2024 qualifying event; these are candidate datasets, not promises of availability or suitable pairs. The importer resolves the event through the schedule and records the round and circuit key. Never hardcode an unverified round from memory.

Keys must distinguish season, round, session, circuit layout/version, driver number and lap number. Use driver number as a string; display abbreviation is metadata, not a stable database identity. A comparison contains exactly two different drivers from the same session and qualifying phase. No sprint, race, wet/dry mixing, cross-year lap comparison or cross-layout comparison in v1.

Select the highest phase common to the chosen drivers with eligible laps, then the fastest eligible lap in that phase. Display that rule and allow explicit eligible lap selection. Do not automatically combine one driver's Q3 with another's Q2. If no common eligible phase exists, return an actionable empty state. Equal `LapTime` ties use lower lap number.

## 3. Import, eligibility and provenance

### 3.1 Import sequence

1. Resolve an allowlisted season/event/session to an exact upstream identifier.
2. Open a project-local FastF1 cache. Load timing, telemetry, weather, session status and race control messages through the installed public API. Record the exact FastF1 version and import timestamp.
3. Obtain Q1/Q2/Q3 membership with `split_qualifying_sessions()`. If phase membership is unavailable or ambiguous, stop publication of that session rather than infer phases from lap order.
4. Retain a lap index with every lap's eligibility and machine-readable exclusion reasons, including rejected laps.
5. Validate car data and position data separately. Preserve native timestamp/value records as the audit inputs outside Git.
6. Freeze one session geometry/reference version. Produce normalized laps, comparisons, quality reports and catalog manifests as immutable derived artifacts.
7. Validate all artifacts before atomically switching the catalog manifest. A failed import leaves the previous published catalog intact.

Race control data is necessary to evaluate deleted laps, and `IsAccurate` is a timing integrity flag rather than a blanket telemetry-accuracy guarantee. [Timing reference](https://github.com/theOehrly/Fast-F1/blob/main/docs/api_reference/timing_data.rst) Phase splitting also depends on session status. [FastF1 phase implementation](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/core.py)

### 3.2 Publication eligibility

Every following condition is required for a normal comparison:

| Check | Required outcome | Failure behavior |
| --- | --- | --- |
| Recorded lap and all three sectors | Finite, positive durations | Exclude lap |
| `Deleted` | Explicitly false, with race control loaded | Unknown is not false; exclude |
| `FastF1Generated` | Explicitly false | Exclude |
| `IsAccurate` | Explicitly true | Exclude; retain reason |
| Pit in/out | Both absent | Exclude |
| Phase | One known Q phase | Exclude |
| Track status | Green throughout for the curated MVP | Exclude other/unknown states |
| Tyre | Known dry compound | Exclude wet/intermediate/unknown |
| Native car coverage | Brackets both timing boundaries, acceptable gaps | Exclude from aligned telemetry |
| Speed/time integrity | Satisfies section 5 | Exclude from alignment |
| Timing consistency | Satisfies section 7 | Warn or block as specified |

Same phase does not mean same conditions. Display compound, tyre age, lap start UTC/time-of-day, and elapsed time between the laps. Different dry compounds or tyre ages are a visible comparison-context warning, not an automatic claim about tyre performance. Do not infer wetness from a dry compound alone; rain/weather/track context can also trigger review.

No silent fallback from a rejected fastest lap: label the chosen result **fastest eligible lap** and retain a reason if it differs from the official phase best. Classification order and lap availability are separate concepts.

### 3.3 Provenance record

Store the source identifier, source session identifier, import UTC, FastF1 version, pipeline commit, methodology version, circuit-config hash, canonical-reference lap ID, native-input hash, output hash, units, all thresholds, and dataset review status. The served-artifact contract currently accepts only `provenance.source = fastf1`; a future browser demo fixture would need an explicit synthetic source value and prominent UI labelling. Keep software and input versions independent. Reimports may change upstream lap validity; publish a new revision rather than mutating an old comparison.

The scaffold contains an artificial unit-test factory only. It is not served by the app; the app starts with an honest empty-data state. Test geometry and times must never be presented as a real event.

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

Create `distance_m = sorted(unique([0, 5, 10, ..., floor(L/5)*5, L, segment boundaries, sector boundaries]))`. Record a nominal spacing of 5 m; the final interval and explicitly inserted boundaries may be shorter. This is display resolution, not measurement resolution. A 5 m grid creates no new source evidence.

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

Do not colour by cumulative delta: a driver who gained earlier would otherwise appear faster on a later section where they are losing time. A future continuous 100 m local-window view may be added as a separate labelled mode; it is not necessary for v1.

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

These defaults must be checked on the three real validation datasets before release. Changing them requires a methodology/config version, before/after evidence and updated fixtures.

| Metric | `pass` | `warn` | `block` |
| --- | --- | --- | --- |
| Absolute sector-sum versus official lap | <=3 ms | >3 and <=20 ms | >20 ms or missing |
| Absolute sliced duration versus official lap | <=3 ms | >3 and <=20 ms | >20 ms or missing |
| Max absolute interior individual/pair residual | <=50 ms | >50 and <=150 ms | >150 ms or unavailable |
| Absolute distance scale deviation | <=1% | >1 and <=3% | >3% |
| Native speed/time gap | <=0.50 s | >0.50 and <=0.75 s | >0.75 s |

Take the worst applicable severity. `pass` means eligible for a reviewed publication, not an accuracy guarantee. `warn` may be browsed with a persistent explanation and a residual table; publication/export must include that warning and requires dataset review before catalog promotion. `block` retains official timing and reasons in the operator report but is withheld from the public catalogue and API artifact response. The browser shows an unavailable comparison, not ranked local claims or publication cards.

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
| Missing lap boundary | No extrapolation; lap blocked |
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
| Serialization | Finite numbers/null, equal array lengths, valid ranges, stable hash |

Recompute the same inputs/config twice and compare canonical artifact hashes excluding operational timestamps. All rounding happens in presentation. A numerical pipeline change increments the methodology version and regenerates reviewed artifacts.

## 10. First importer handoff

Implement in this order: resolve/import/cache → lap eligibility report → native-channel checks → canonical reference and normalization → grid interpolation → raw delta → official reconciliation → circuit partition → metrics → observation templates → catalog promotion. Do not begin inference templates until the reconciliation report is inspectable.

The analysis extra pins FastF1 3.9.2. Its request implementation uses `Cache.configure` and a Formula 1 account authentication adapter; the first importer ticket must exercise that supported flow and check actual seed-event availability. [FastF1 3.9.2 request implementation](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/req.py) General `main` documentation can still move independently of the release. If upstream access is unavailable, keep the empty-data workspace and offline tests usable and report the actual access failure without substituting invented real telemetry. Do not persist user credentials in artifacts or logs.
