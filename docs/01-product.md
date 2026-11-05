# Product blueprint

Status: starting specification for implementation, not a claim that the full application exists. The repository's implementation status and backlog determine what is currently usable. All thresholds and interface choices in this document are product decisions; source capabilities and numerical constraints are defined in [the telemetry methodology](03-telemetry-methodology.md).

## 1. Product promise

LapDNA answers: **Where did the gap between these two qualifying laps develop, and what observable telemetry patterns accompanied it?**

The user selects two drivers' laps from one qualifying session and one qualifying phase. LapDNA places them on the same approximate distance axis, identifies the largest local differences, and connects each region to speed, throttle, gear, and brake-state traces. It distinguishes official timing from telemetry-derived estimates and makes the evidence behind each observation inspectable.

The product does not infer driver intent, mechanical setup, grip, brake pressure, steering input, tyre temperature, or the cause of a time difference from public telemetry. The central wording rule is **describe a measured pattern and its context; do not invent a causal explanation**.

Example of acceptable copy, with illustrative placeholders rather than real results:

> Driver A gained approximately {local_delta} through {region}. In this interval, A's minimum sampled speed was {difference} higher. The public telemetry does not establish the cause.

Unacceptable copy:

> Driver B braked too early because they lacked confidence.

## 2. Intended users and jobs

| User | Immediate job | Successful outcome |
| --- | --- | --- |
| Interested F1 viewer | Understand a qualifying gap beyond the final classification | Finds the two or three regions that explain most of the observed difference and can inspect the relevant traces |
| Analyst or writer | Prepare a compact, defensible comparison | Exports a readable card with the selected laps, estimated regions, official timing, provenance, and limitations |
| Portfolio reviewer | Evaluate the engineering and numerical work | Can run the project, inspect the methodology, reproduce an artifact, and follow its tests |

The primary journey is exploration of a prepared comparison. Data ingestion and artifact preparation are maintainer workflows; the first release does not ask a casual visitor to wait while FastF1 downloads an entire session.

## 3. Scope decision

### Included in the two-week MVP

- Three circuit configurations: Monza, Silverstone, and Suzuka.
- One validated historical qualifying session per circuit initially. The 2024 events are candidate seeds, not verified supported data until the import and validation work is completed.
- Two different drivers from the same session and the same qualifying phase. The initial catalog prepares one verified phase per seed session, preferring Q3 when the required coverage is available.
- At least four selected drivers per seed session and all six unordered pairs among those four, giving at least 18 prepared comparisons across the three circuits. Each pair uses those drivers' fastest eligible laps in the selected phase.
- Explicit selection of another eligible lap only when a corresponding comparison artifact has been prepared and published. The UI does not promise an arbitrary pair/lap combination that the read-only catalog cannot serve.
- A common distance view with a colored reference track outline and synchronized delta, speed, throttle, gear, and brake-state charts.
- A ranked summary of corner complexes and straights, using versioned region definitions.
- Up to three deterministic, evidence-backed observations; three are the target, never a reason to manufacture a claim.
- Official lap and sector comparisons alongside clearly labeled telemetry-derived timing and reconciliation results.
- A shareable URL for a prepared comparison and export of a portrait PNG analysis card with a machine-readable comparison JSON companion.
- Desktop and mobile reading, keyboard navigation, informative unavailable states, and a clear methodology panel.
- Repeatable local import, validation, generation, and publication instructions for a later qualifying session at one of the supported circuits.

### Outside the MVP

- Live timing, streaming telemetry, session notifications, automatic publication, or an always-running ingestion queue.
- Accounts, billing, comments, social feeds, database administration screens, or collaborative editing.
- Cross-circuit, cross-year, cross-session, mixed-phase, race, sprint, and more-than-two-driver comparisons.
- Uploads of arbitrary CSVs or third-party telemetry formats.
- Racing-line reconstruction, precise apex or braking-point claims, brake-pressure charts, and setup or driver coaching advice.
- A general-purpose chart editor, customizable dashboards, video synchronization, or a mobile native app.
- Clustering corner profiles. This remains a later experiment after the baseline is trustworthy and complete.

Every added circuit, data source, chart library, endpoint, and export format must serve an included behavior. The workhorse implementer should not expand this list without a recorded design change.

## 4. Product truth levels

Every displayed fact belongs to one of these levels. The UI must not collapse them into a single unqualified label.

| Level | Examples | Required presentation |
| --- | --- | --- |
| Official timing | Lap duration and three sector durations available through the timing source | Label as official timing; preserve source precision |
| Source telemetry | Speed, throttle, gear, binary brake samples | Name the channel and unit; show gaps and sample limitations |
| Derived estimate | Resampled delta, local region gain, estimated brake-state transition distance | Use approximate language and link to the method or quality detail |
| Interpretation | Relationship between a region's time change and accompanying channel patterns | Phrase as a co-occurring pattern with evidence; no causal certainty |

Synthetic data, if introduced for automated tests or development, must stay separate from production artifacts. A synthetic demo needs a visible persistent label and must not use real driver names with invented lap results. The initial scaffold should use an honest empty state.

## 5. Primary journey

1. **Open the workspace.** See the product purpose, supported circuits, and either a prepared comparison or an explanation that data must first be prepared.
2. **Choose a session and phase.** Only prepared sessions and phases appear as available. The initial seed catalog normally offers one verified phase per session. Unprepared phases are not implied to be supported.
3. **Choose A and B.** Driver labels include abbreviation and full name. The application selects each driver's fastest eligible lap within that phase. The same driver cannot occupy both slots.
4. **Review the selected laps.** Show lap number, official lap duration, tyre compound, tyre age when available, and qualifying phase. Offer a lap override only where a published artifact exists for that choice. Eligibility diagnostics remain available to maintainers without implying every eligible lap is available in the public catalog.
5. **Compare.** The title states the two drivers and official gap. The track shows where the local estimated gap changes. The delta trace explains how those changes accumulate.
6. **Inspect a region.** Hover, focus, tap, or select a corner/straight summary. The map, charts, cursor readout, and evidence agree on the same distance or interval.
7. **Read the observations.** Each observation names the region, gives the magnitude and channel evidence, and links back to the exact interval.
8. **Check the quality.** The visible quality summary reports whether reconciliation and coverage passed. Open the detail panel to inspect official and raw telemetry residuals.
9. **Export or share.** Export a card for the prepared comparison. Copying a link is a user action; the application never posts to a social service itself.

The selection form uses an explicit **Compare laps** button. Pending edits do not replace the current rendered comparison until a new artifact has loaded successfully. A small notice says “Selection changed — compare to update” while edits are pending. This prevents a title/trace mismatch during asynchronous loading.

## 6. Selection rules

- Session identity includes year, event, and session type. A display circuit name alone is insufficient.
- The curated session manifest may specify a default phase and pair after validation. Otherwise, choose the latest prepared phase, then the prepared pair with the smallest combined official lap duration. Break ties by driver code and then lap number for deterministic behavior.
- Changing session clears both drivers and lap overrides before applying that session's default pair.
- Changing phase clears lap overrides and retains each selected driver only if represented by prepared comparisons in the new phase. Fill missing slots using the deterministic default rule without duplicating a driver.
- Changing one driver resets that driver's lap to the published default for the new pair. If there is no published artifact compatible with the other driver's selected lap, show the prepared lap choices and require an explicit selection rather than silently changing the other driver's lap.
- Choosing a slower eligible lap is allowed only when a corresponding published artifact exists. Display “Selected lap” instead of implying that it was that driver's qualifying best.
- Derive available driver/lap combinations from catalog entries, not from every driver in the timing session. If a combination has not been prepared, display “This pair has not been prepared” and offer the available pairs; do not trigger live preprocessing or quietly substitute another lap.
- A comparison requires both laps to pass mandatory eligibility checks from the methodology. A user cannot bypass a mandatory invalid-data block through the interface.
- A different compound, tyre age, or track-condition context does not automatically invalidate an otherwise supported pair; it produces visible context. It must not become a claim about which factor caused the gap.
- Swapping A and B preserves the exact selected laps and physical reference geometry. It swaps colors and sign, without rerunning an asymmetric numerical alignment or choosing different regions.

The prepared catalog is deliberate scope control: FastF1 retrieval and scientific processing happen in an offline command, and the API only reads immutable, validated comparison JSON. This keeps the first release deterministic and avoids network-dependent analysis requests. It still provides genuine two-driver choice across each circuit's prepared pairs. Additional drivers, phases, or laps can be added later by generating more artifacts; arbitrary server-side computation is a separate feature.

## 7. Analysis output contract, in product terms

### Official summary

Show both lap durations and the signed official difference, defined throughout the product as **B minus A**. Positive means A's lap was quicker. A tie at displayed precision is “Equal at displayed precision”; keep the underlying value for calculation.

Show sectors S1–S3 with both official durations and their signed differences. Prepared v1 artifacts require all three sector times. If a source value is missing, the operator report uses an em dash with “Unavailable” and publication is blocked; do not calculate an “official” sector by splitting a telemetry trace.

### Track map

Use the versioned reference path for the session/circuit configuration. The map illustrates location, not each driver's reconstructed racing line. Color is based on local estimated time contribution within analysis regions. A region where A gains uses cyan; a region where B gains uses orange; differences below the configured display floor use neutral gray. Unsupported regions use a visible gap or dashed treatment.

The legend must say “Estimated local gain” and must explain the current scale. Cumulative advantage belongs on the delta trace; it must never silently drive the default map colors.

### Traces

The required stack is cumulative delta, speed, throttle, gear, brake. All charts share one distance domain, one selected interval, and one cursor distance. The delta sign legend remains visible. Speed is in km/h, throttle in percent, gear is an integer step series, and brake is a binary state. No pressure unit or pressure-shaped axis appears for brake.

### Region summaries

Each row shows the region's name/type, estimated local contribution, the driver favored, a brief channel comparison, and any quality limitation. Ranking uses absolute magnitude among supported regions. All regions remain available in track order in an alternate view so the product does not hide neutral or unsupported portions of the lap.

### Observations

An observation needs a stable identifier, one region or deliberately grouped adjacent regions, a signed estimated time contribution, quantitative channel evidence, evidence distance range, and a quality/provenance reference. Ranking and text are deterministic. Clicking an observation selects its interval.

When only two observations satisfy the evidence rules, show two and a plain message: “Only two regions have enough evidence for an observation.” Do not fill the third slot with generic advice or restate the same interval. A region can still appear in the neutral region table when it lacks enough evidence for narrative text.

## 8. Quality is part of the normal flow

The comparison header always exposes one of the schema's quality statuses and a one-sentence explanation. Use text and icons as well as color.

- **Data checks passed (`pass`):** mandatory checks passed. Approximate corner attribution remains approximate.
- **Limited (`warn`):** the comparison is viewable with explicitly identified limitations. Unsupported intervals are masked; conclusions only use supported evidence. Dataset review is required before catalog promotion, and export carries the warning.
- **Unavailable (`block`):** the requested comparison cannot support the required analysis. Keep official timing and the blocking reason in the operator report; do not promote the comparison to the public catalog or generate an analysis card. If a previously saved or explicitly loaded blocked artifact reaches the client, render an unavailable state defensively.

The serialized status enum is exactly `pass | warn | block`; thresholds come from the methodology. The initial analysis uses raw elapsed-time differences only. A timing-sliced endpoint that agrees by construction is not proof of accuracy; its check is labeled `timing_constraint`. Interior raw residuals remain inspectable, with `calibration` or `cross_lap_consistency` basis as appropriate. No corrected or sector-anchored delta mode is included. A limit to narrative generation does not require hiding otherwise useful source telemetry in a supported artifact.

## 9. Export and publication

The MVP export is a 1080 × 1350 PNG card plus an optional JSON download using the exact loaded comparison artifact. The PNG is assembled from the same validated values, regions, and observation text used in the workspace; it must not recalculate results in a separate export path.

Required card content:

1. LapDNA title and circuit/event/year/qualifying phase.
2. Driver A/B labels, exact lap identifiers, both official lap times, and official gap.
3. Reference track map with local estimated gain legend.
4. Compact cumulative delta strip and three official sector differences.
5. Up to three concise observations with region names and quantitative evidence.
6. Quality summary, FastF1/source attribution, artifact/method version, and a compact statement that regional values are approximate and brake is on/off.

Keep all text readable at half size. If observations do not fit, reduce wording by deterministic compact templates; never shrink the text indefinitely or remove provenance. Export with fewer observations remains valid and carries the same limitation message. Missing required data or an unavailable comparison blocks export with an actionable explanation.

Filename convention: `lapdna-{year}-{circuit}-{phase}-{driverA}-lap{nA}-vs-{driverB}-lap{nB}-{artifactShortId}.png`. Use safe characters and an equally named `.json` companion. The card should include its public permalink only when a public deployment actually exists. Never insert a local development URL into a public-looking export.

“Publish after every qualifying session” is a repeatable maintainer process in this release: import an explicitly selected session, validate results, review the artifact and observations, add it to the prepared catalog, build, and deploy. Scheduling and unattended editorial publication are later work. Data access through an open-source package does not by itself settle redistribution rights; release guidance must distinguish library licensing from the underlying data's terms.

## 10. Nonfunctional acceptance targets

These are targets to measure during implementation, not claims about the scaffold.

| Area | MVP target |
| --- | --- |
| Reproducibility | Same normalized input, configuration, and method version produces the same result values and stable comparison identifier |
| Time truth | Official values retained unchanged; raw reconciliation and the basis of each check exposed separately |
| Robustness | Missing channels/intervals produce explicit masks and limitations; no fabricated zeros or extrapolated precision |
| Interaction | Map, chart, row, and observation selections resolve to the same distance domain |
| Readability | Chart axes, units, signs, and limitations remain legible at 1280 px desktop and 390 px mobile widths |
| Accessibility | Core selection and evidence inspection work without a pointer; color is never the only distinction |
| Performance | Cached prepared comparison becomes interactive within 2 s on a documented local baseline; no ingestion on the request path |
| Cursor response | Shared cursor updates feel immediate; keep handlers under a 16 ms frame budget in a measured representative comparison |
| Export | Card passes visual inspection at full and half size and reproduces loaded values exactly |
| Maintenance | Another implementer can run documented commands and complete the next ticket without deciding the architecture |

## 11. Two-week sequence

The detailed implementation backlog is authoritative for file-level changes and checks. This sequence defines the product dependency order.

| Working days | Outcome | Exit evidence |
| --- | --- | --- |
| 1–2 | T01–T02: source adapter, first prepared session, lap eligibility | One session can be loaded and eligibility decisions inspected |
| 3–4 | T03–T04: reference, distance alignment, raw timing reconciliation | Numerical tests pass; real-lap residual report reviewed |
| 5 | T05–T06: region evidence and prepared comparison selection | First real comparison artifact is selectable and its official summary is inspectable |
| 6–7 | T07–T08: telemetry and map interaction | Synchronized cursor, shared interval, valid map coloring, and keyboard access |
| 8 | T09–T10: region summaries, observations, export | Claims point to evidence; cards pass visual QA |
| 9 | T11: all three circuits | Per-circuit validation packs and at least 18 prepared comparisons |
| 10 | T12: release verification and operations | Cold-start rehearsal, performance evidence, mobile/accessibility checks, no-data/error verification, and reproducible release |

This is ten focused working days within a two-week calendar window, with remaining calendar time as buffer. Upstream availability and numerical validation may require more time; the schedule never overrides a failed quality gate.

If time slips, protect numerical validity, the first complete comparison, and source transparency. Reduce decoration and optional presentation polish first. Clustering does not enter the schedule until all mandatory release checks pass.

## 12. Definition of done

A small feature is done only when its ticket's behavior and relevant checks pass, documentation and implementation status agree, its diff is reviewed for accidental data/secrets, and a focused descriptive commit is pushed to the requested repository. Commit messages describe the behavior or change, such as `feat: synchronize telemetry cursor across panels`; they do not reference the tools or models used to author it.

The MVP is done when a fresh checkout can prepare and inspect a validated two-driver comparison at each of the three supported circuits; official timing and raw residuals are visible; every generated observation traces to actual evidence; all required charts and interactions work; and a portable card accurately represents the selected comparison. A scaffold with empty states is a completed foundation milestone, not a completed analysis product.
