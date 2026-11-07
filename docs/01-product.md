# Product blueprint

LapDNA compares two qualifying laps and answers three questions. Where did the time difference develop? Which measured inputs changed there? Did the selected laps gain and lose time in different types of corners?

The user's immediate release priority is [R01 recorded session/phase results](16-results-first-milestone.md), now implemented across available circuits from 1950–2026. It compares recorded timings without local telemetry claims. Individual attempts/runs are deferred to R02; the three-circuit reference/telemetry scope below applies to that later numerical release.

A reader can choose any two different drivers in an imported event, pick each driver's Q1, Q2 or Q3 lap, and inspect the result by turn. “Any” covers every eligible imported lap, including a slower lap selected explicitly. A driver who did not reach Q3 has no Q3 selection. Each exclusion has a visible reason.

Enter through a year selector, defaulting to the current year. Load that year's actual calendar, choose a race, then open its studio. Preserve the year/race in the URL and browser history. A listed race is scheduling metadata, not a claim that qualifying has completed or its telemetry is ready. Only imported sessions matching that year and round populate the studio. Display source freshness and an honest empty state for unimported races.

## 1. The analysis readers receive

The opening comparison names both drivers, the phase and lap number on each side, the official lap times and the signed gap. One distance axis then ties together a dominance strip, sector dividers, numbered turns, the speed trace, throttle, gear, brake state and cumulative time delta. Selecting T7 locates that marker on every panel and highlights its analytical region on the reference track map.

The broadcast image establishes how those views relate visually. LapDNA uses its own branding and validated source data. The [source audit](13-data-source-audit.md) verifies native speed, throttle, gear and a brake switch, so retain those features. Each factor needs its own source channel and per-lap availability; never infer pedal or gear values from speed. Steering and brake pressure have no verified measured field in the selected feeds. Additional providers require review before either adding or dropping a proposed feature. Preserve the labelled synthetic demo while that review proceeds. Displayed reference distances and local time gains are estimates. Official sector durations retain their source precision. See [telemetry methodology](03-telemetry-methodology.md) and [sources](09-sources.md).

Below the chart, the reader can expand low-, medium- and high-speed corner groups. Each group shows where either selected lap gained or lost time, how much of the class had adequate telemetry, and which turns support the conclusion. An analysis sentence can therefore distinguish a net high-speed advantage from a class where several sizeable gains and losses canceled each other.

## 2. Scope and first release

| Capability | Release requirement |
| --- | --- |
| Circuits | One validated conventional qualifying session each at Monza, Silverstone and Suzuka. The 2024 events are candidates pending source and data-quality checks. |
| Eligible population | Inventory all drivers and actual laps in Q1, Q2 and Q3 for each imported event. Preserve exclusions and reasons. |
| Pairing | Two different drivers from that event. Same-phase comparison by default, with an explicit independent-phases mode. Each slot accepts an eligible individual lap. |
| Processing | Import and normalize the event offline. Resolve the requested pair from local inputs, reuse cached results and apply quality checks before serving. |
| Timing | Official lap and sector values, telemetry-derived cumulative delta, two independent local views of the same lap (analytical regions and estimated minisectors). |
| Findings | Corner-class comparison and up to three supported regional observations. Each finding links to its contributing intervals and evidence. |
| Presentation | Synchronized responsive charts, colored reference map, turn navigation, keyboard controls, shareable comparison link, 1080 × 1350 PNG and evidence JSON. |
| Fallback | Official sector-only comparison when detailed telemetry cannot be used but official timing passes its own checks. |
| Editorial workflow | Import after qualifying, validate the session, compare, inspect evidence and export a card for deliberate publication. |

The updated selection rule replaces the curated four-driver catalogue. Precompute reusable per-lap inputs once. Generate bounded pair results from those local inputs and cache them by immutable identity. A visitor selecting a new pair should never have to download an upstream session. The scaffold can look up an already prepared result and report when locally computed results are unavailable. The release must resolve uncached eligible pairs too.

The two-week target now has a staged acceptance gate. Deliver one validated whole-event inventory and a working arbitrary-lap comparison first. Then verify the new corner-class analysis, export and other two circuit profiles. Describe actual coverage if the calendar expires before a gate passes. Later work includes live updates, more circuits, clustering and publication automation.

## 3. What the data can answer

| Data available | Workspace | Claims |
| --- | --- | --- |
| Both laps have validated telemetry | Reference map, aligned traces, turn ruler, estimated minisectors, corner summaries, category analysis and quality report | Supported local time estimates and co-occurring channel patterns for these laps |
| Both laps have valid official lap and sector timing only | Lap/sector table plus discrete cumulative delta markers at S1 end, S2 end and Finish | Which official sector contributed to the gap and the gap at each sector end |
| A required eligibility or timing check fails | Reason, selected lap identities and available next actions | Withhold the unsupported comparison |

The sector-only markers use a categorical timing-line axis. Sector totals do not identify where inside a sector the time changed. This view omits turn-level loss, continuous distance curves, a performance-colored map, estimated minisectors and corner-speed conclusions. A separately validated sector-only result may remain useful when the spatial checks fail.

The nominal 100 m estimated minisectors in telemetry mode are calculated from the raw elapsed-time curves on the shared axis. Use the shorter final interval when needed. Preserve unknown intervals and identify the method in the legend. Source mini-sector status colors alone cannot supply numeric head-to-head durations. A future adapter for actual measured splits would require its own provenance and validation.

The default entry page shows imported data availability. The explicit Synthetic Design Preview at `?preview=1` uses fictional geometry and anonymous driver slots to demonstrate the visual layout, turn selection, zoom and category presentation. It stays visibly labeled throughout. The current handoff records which interactions have been tested. Demonstration traces and category examples must remain outside the production catalogue and editorial exports.

## 4. Selecting the laps

1. Select an imported session by season, event and session type. Display the session's available phases and import/quality status.
2. Select A and B from its full driver inventory. Show abbreviation, name and actual phases reached or available. Disable each driver's own identity in the other slot.
3. **Same phase** starts with the highest common phase containing eligible laps, then takes the fastest eligible lap for each selected driver. Equal official times use the lower lap number. If they have no common eligible phase, explain the condition and offer independent phase selection.
4. **Independent phases** exposes a separate Q1/Q2/Q3 choice for each slot. The user can compare Q1 against Q3 or two laps in the same phase. Selecting independent phases explicitly authorizes the request's cross-phase flag when the chosen phases differ.
5. Each slot's lap selector lists eligible lap numbers, official durations, compound, tyre life and start time where known. Label the default “Fastest eligible lap”. A manual choice becomes “Selected lap”. Show excluded laps and their source-backed reasons in a separate diagnostic disclosure.
6. Display the capability supported by both selected laps. A timing-only lap can still participate in a sector comparison when its official timing passes eligibility.
7. The **Compare laps** action freezes the exact request. Pending edits leave the previous result's title, values and identity together until the next result arrives. A missing or rejected request never silently substitutes another lap.
8. Offer **Swap drivers** for the loaded comparison. Swap labels, channel roles, colors and directional calculations consistently. Keep the same reference, classes, grid and intervals. Identity-based observation text continues to describe the actual drivers.

An event change clears lap selections. A driver change resets only that slot's phase/lap to valid choices. A shared phase change in Same phase mode resets both laps. Changing a slot's phase in Independent phases mode resets only its own lap. Explain a missing phase using the available evidence. “No Q3 lap in this import” is safer than claiming elimination when the import is incomplete.

Cross-phase results carry both phase labels, the elapsed start-time separation when available, compound/tyre context and a visible caution about changing conditions. Carry that context into the analysis and card. The request flag addresses phase selection only. Weather or other mandatory eligibility gates still apply.

## 5. Reading the comparison

**Official timing.** Define signed time as B minus A throughout. Positive cumulative delta means A reached that distance sooner. Positive local gain means A increased its advantage through the selected interval. A lap can still be behind overall while gaining locally. Both official durations and their difference remain visible in every result.

**Distance view.** The turn names T1…Tn appear on the reviewed reference axis and can be selected even when nearby labels need collision handling. Put official sector divisions on all panels. The dominance strip shows the sign and magnitude of gain in each estimated minisector. The associated tooltip gives the range, traversal times, gain and approximate turn context. A bin touching multiple turns cannot be attributed in full to each turn.

**Corner and straight summary.** The additive region partition assigns every metre once. Its table can switch between track order and absolute gain ranking. A grouped corner complex gets one contribution and identifies all of its markers. Class totals cover classified corners, while straights, mixed complexes and unknown classes remain visible separately. The minisector partition independently covers the same lap. The UI never adds the two partitions' totals.

**Class definitions.** The reference speed comes from the minimum supported native speed in a reviewed neighborhood of a corner marker in the frozen reference lap. Initial project bands use low below 150 km/h, medium from 150 to below 250 km/h, and high from 250 km/h upward. The classification method, reference and thresholds are versioned. Re-selecting a driver or reversing A/B cannot move a corner between bands. A mixed complex and an unstable or unsupported classification get explicit labels.

**Tailored analysis.** For each low/medium/high row show expected and supported corner units, supported distance coverage, gross time gained by A, gross time gained by B, net signed gain and supporting turns. Allow expanding rows to see opposing contributions and exclusions. For directional prose use the methodology's count, coverage, sensitivity and materiality gates. If those gates pass, a sentence can read “Across these selected laps, {driver} gained approximately {high gain} in the supported high-speed regions and conceded approximately {low loss} in low-speed regions.” Include the medium-speed outcome where supported. A mixed or inadequate class receives its actual status and explanation. Reserve exclusivity words such as “only” for the stricter complete-coverage check.

**Regional findings.** Up to three disjoint supported regions connect a time contribution with a measured pattern such as exit speed or a brake-switch transition bracket. Each sentence names the actual driver and exact evidence range. A click inspects that range. Fewer than three supported findings produces an explanation. The class summary stays separate from the regional observation count.

Keep conclusions specific to the selected laps and their conditions. The data alone cannot justify enduring driver-skill rankings, setup diagnoses or causal claims about grip, bravery or braking force. A deterministic Python interpretation is sufficient, and the browser consumes its structured evidence.

## 6. Quality, export and acceptance

Use the method's pass/warn/block quality state alongside the actual result type. The header, class section and export retain material warnings. Keep raw residuals and their calibration/timing-constraint labels inspectable. A dense display grid does not increase native sample support.

Export the loaded result and orientation. A telemetry card includes both phases/laps, official times, regional map and delta, class summary, supported observations, source, method, comparison ID and limitations. A sector-only card identifies that capability and uses its table and discrete boundary values. Keep cross-phase warnings legible in either format. The JSON companion retains original artifact order and the requested display order.

Release checks include an eliminated or missing-phase driver, a cross-phase pair, two non-fastest selections, a previously uncached eligible pair, mixed data capabilities, a sector-only result, inadequate category coverage, opposite gains within one class, a wrapped complex and mobile/keyboard turn navigation. Verify the class totals against member evidence and both independent partitions against their own expected accounting. The handoff records when real sessions meet these requirements. See [implementation tickets](06-implementation-plan.md) and [verification](07-verification.md).
