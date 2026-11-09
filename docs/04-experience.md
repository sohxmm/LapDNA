# Comparison workspace experience

The workspace makes it possible to read a time change, locate its turn, and check the associated telemetry without translating between separate axes. This guide specifies the full application. The user has approved a sports-editorial landing and G1 stacked overlays; [the approved decision](17-approved-ui-and-telemetry-rollout.md) governs entry flow, minimal copy and verified 2018–2026 telemetry scope. The prefinal product has no synthetic preview. Real session ingestion and numerical validation follow the implementation tickets. See [current handoff](10-handoff.md).

## 1. Layout and visual language

Use a dark analytical surface, system fonts with tabular numerals, high-contrast text, quiet gridlines and two persistent driver encodings. Driver A uses cyan (#5ADBEA) with solid traces. Driver B uses orange (#FFB16B) with dashed traces. Pair every color-coded value with a driver code, sign or text label. Use a neutral gray for gains beneath the configured display threshold and a separate hatch/gap plus “Unavailable” label for unknown intervals.

The supplied reference informs the ordering and alignment of the traces. The interface uses LapDNA identity, factual labels, accessible chart descriptions and units. An image or decorative track outline cannot substitute for decoded source data.

Desktop reading order:

```text
Event/session                         Dataset and quality details
Mode: Same phase | Independent phases
A: Driver / Phase / Lap               B: Driver / Phase / Lap     Compare
Selected lap A | Selected lap B | Official gap | Context / Share / Export
Local gain: estimated minisectors     [A] [Neutral] [B] [Unavailable]
S1                               S2                           S3
Turn ruler T1   T2 T3                 T4a T4b ...              Tn
Speed (km/h)          A solid   B dashed              shared distance
Throttle (%)          A solid   B dashed
Gear                  integer steps
Brake                 A on/off lane, B on/off lane
Cumulative delta (s)  B−A, zero baseline, positive favors A
Reference distance (m)                     Shared cursor and zoom / reset
Track map + selected turn                 Official sector timing
Corner-speed analysis: low / medium / high, coverage, exceptions
Corner/straight table                     Regional evidence and findings
Method, source, dataset revision and limitations
```

Keep speed the tallest channel panel and delta visibly separate with its own zero line. On narrow screens, stack selectors and summaries vertically and keep a single chart width. The turn chooser, region table and evidence follow the chart in document order. Permit an individual table to scroll horizontally with an accessible label, but avoid page-level horizontal scrolling. Use 44 px touch targets for primary actions. Dense chart marks obtain larger separate hit targets or a companion list.

## 2. Data entry and states

The ordinary home view is the approved landing, with Open Studio entering the current-year calendar. The flow is year → race → actual session/phase → two drivers. The existing classification comparison provides useful real timings even when no detailed laps are imported; do not replace it with a global empty-data message. Detailed lap inventory has its own honest empty state. No demo route or fabricated graph/map fallback is shipped. The landing circuit outline is a small excerpt of the verified Monza reference geometry. No image from the reference is required at runtime.

In a populated release, event selection loads the session's driver/lap inventory. Each slot shows driver, phase, lap, official time, compound, tyre age and start time as available. Put the actual phase next to every loaded lap in the comparison header even in same-phase mode. A phase option with no eligible lap is disabled with a reason. The form offers all eligible individual laps from the imported event, including non-fastest laps.

Same-phase mode links the two phase controls. Its default is the highest common eligible phase and each driver's fastest eligible lap in that phase. Independent-phases mode unlocks each slot's phase control. Choosing different phases displays a persistent context notice and places `allow_cross_phase=true` in the request. This single mode choice is sufficient. Do not repeatedly interrupt selection with a confirmation dialog.

Maintain separate draft and loaded state. The draft contains session ID, both lap IDs and phase mode. A comparison request resolves that exact selection through the API. Cached and freshly computed results share the same workspace behavior. Until local computation is implemented, an eligible pair without a prepared result gets a specific “Comparison engine has not prepared this pair” state.

| Event | State transition and visible result |
| --- | --- |
| Inventory loading / empty / failure | Skeleton during active request, clear no-data state on empty, retry on failure |
| Draft changes | Keep loaded title and traces together, mark pending selection, offer Compare |
| Valid draft submitted | Freeze request identity, disable export of the pending result, abort superseded requests |
| Telemetry result received | Switch header, chart and evidence together and reset view state for the new artifact |
| Sector-only result received | Render the timing workspace and fallback reason |
| Missing session/lap or rejected pair | Show the exact missing choice or quality reason and preserve the prior loaded result's identity |
| Transient failure | Retry the same request or return to selection |
| Shared link refers to an unknown revision | Explain the missing result and offer the inventory without silently changing laps |

Use the source's reason codes for missing data and rejected eligibility. Avoid claiming a sporting elimination from a missing source row alone. A comparison accepted across phases carries phase labels, time separation and compound/weather limitations in the analysis and export. Further data checks may still reject the pair.

## 3. Chart implementation decision

Keep React, TypeScript and Vite for the UI. Apache ECharts 6.1.0 owns the telemetry rendering through a small direct adapter, with a single multi-grid Canvas chart for the stacked channels. React owns selection state, controls, layout, accessibility and the textual readout. The reference map uses SVG with stable region paths. A dedicated export composition produces the PNG independently of the live chart scroll/zoom state.

Use one numeric x-axis per grid with identical minimum, maximum and plot margins. Link the axis pointers. Apply one shared dataZoom domain to all x-axis indices. Give the React workspace one canonical cursor distance, selected turn/region and viewport. Map pointer and chart events to that shared state, avoiding an independent cursor or domain per panel. Resize the chart with ResizeObserver, update series when the artifact changes, clean up listeners and dispose the chart instance on unmount. Avoid recreating the entire instance on every cursor movement.

Renderer responsibilities end at display transformations. The browser formats units, maps data to pixels, finds a nearest shared-grid sample for a readout and applies an explicit view swap. Python calculates elapsed time, gains, support, class summaries and findings. The app should not require an external chart server, graph image service or model call to render the result.

## 4. Turn ruler, sectors and local dominance

Give the turn ruler its own horizontal band between the dominance strip and speed panel. Place each T-number or lettered label at the reviewed marker's canonical distance. Never space labels evenly by ordinal number. A marker can lie inside a multi-turn complex. In that case the tooltip names both the selected marker and the gain-owning complex.

Turns and sectors share exactly the same projection as all channel and delta panels. Draw subtle sector divider lines across the entire stack and label S1/S2/S3 intervals. Official sector durations come from timing records. Their displayed positions on the distance axis are estimates from the frozen reference crossings. Selecting a turn draws a higher-contrast guide through all panels and shows its name, distance and referenced segment.

Keep every marker selectable. Use measured label widths and two staggered ruler rows where possible. When full-lap labels still collide, group adjacent labels into an explicit range such as T6–T8. Clicking the group zooms far enough to resolve its members. A searchable/focusable turn list always exposes every exact marker and label. Recalculate collisions on resize, zoom or font changes while keeping data coordinates fixed. Labels, hit targets and guide lines must move together.

The dominance strip uses estimated 100 m minisectors by default. Its legend reads “Estimated minisector gain · nominal 100 m.” Equal-width data bins occupy their actual projected distance, including the final short bin. Color by local B−A traversal difference. Neutral and unsupported bins are visually distinct. Tooltip lists bounds, both durations, signed gain, data support and any overlapping turn markers. The 10 ms neutral visual band is distinct from the stricter evidence threshold in the methodology.

The adjacent region table and track map use the reviewed corner/complex/straight partition. Give each partition an explicit name. A user can inspect the same distance through either view, but totals from the two partitions describe the same lap and must be kept separate.

## 5. Telemetry panels

| Panel | Rendering and readout |
| --- | --- |
| Speed | A/B lines on one km/h scale, with headroom for both. Make this the most prominent channel. |
| Throttle | A/B percent traces on a fixed 0–100 scale. |
| Gear | Previous-sample step rendering with integer ticks. Distinguish neutral gear from unknown. |
| Brake | Two labeled state lanes. On and off are discrete, and an unavailable span has a separate treatment. |
| Cumulative delta | One raw estimated B−A curve in seconds with zero baseline and sign legend. Use a symmetric y-domain around zero. |

Every panel uses the same horizontal axis and current viewport. Show distance ticks on the last panel with faint aligned guides above. Use symbols only where they convey specific meaning. Preserve null gaps and the step transitions. Keep local estimates available at useful displayed precision without implying exact physical positioning.

The shared cursor readout names distance, containing region, nearby turn, cumulative delta and both laps' supported channel values. If a channel is missing at the cursor, return “Unavailable” at that location. Do not skip a gap to a distant valid point and display it as though it were at the cursor. A persistent summary above the stack works on mobile and for keyboard users.

The public channel set excludes steering angle and brake pressure. Do not add placeholder axes for either. A missing throttle/gear/brake channel can suppress that channel's evidence while supported time and speed remain usable under the method's rules.

## 6. Selection and inspection behavior

| Action | Result |
| --- | --- |
| Hover chart | Move temporary shared cursor to nearest reference-grid distance and highlight the same map location |
| Tap/click chart | Pin cursor until moved or cleared |
| Leave chart | Clear temporary cursor, preserve pinned cursor and selected region |
| Move keyboard distance slider | Move one grid step with arrows, ten with Shift+arrow, Home/End to view bounds |
| Select turn in ruler/list | Set cursor to its marker, highlight owning region and all associated evidence |
| Select a dominance bin | Highlight that bin's exact interval and show local gain with overlap labels |
| Select a map region or table row | Highlight the same region across map and chart, allow explicit zoom |
| Inspect an observation | Select its interval and zoom with 10% context padding, clamped to lap bounds |
| Select a corner class | Highlight the member intervals as a set and expand their rows. Do not create a contiguous zoom spanning separated corners. |
| Inspect a class member | Select that member's actual region and offer normal region zoom |
| Reset to full lap | Restore distance domain while keeping the current selection readable |
| Swap A/B | Reverse applicable signs, exchange colors and evidence columns, keep geometry and member classes fixed |
| Escape | Close active popover first, then clear temporary/pinned inspection state |

A class can contain disjoint corners. A group summary should not shade intervening straights or imply a single continuous high-speed interval. For Suzuka's crossover, restrict map picking to an identified segment and its ordered distance range. The accessible turn/region list duplicates every map action.

Use clear focus styling, semantic buttons and labels, an accessible chart description, and one shared distance slider. Keep source values, region contributions and class summaries available as actual text or tables. Avoid placing thousands of Canvas points in the focus order or announcing every pointer movement on a live region. Announce explicit selections and completed comparison loads.

## 7. Corner-speed analysis and evidence

Place a section titled **Where each lap gained by corner speed** after the chart and map. Display one class summary sentence scoped to these selected laps, followed by low/medium/high rows. A compact definition states that classes come from the frozen reference profile and shows the thresholds below 150, 150 to below 250, and at least 250 km/h. Each class row can expose its reference basis and actual member turns.

| Column | Meaning |
| --- | --- |
| Class | Low, medium or high with the versioned reference-speed band |
| Supported | Included/expected independent corner units and supported distance coverage |
| A gains / B gains | Gross estimated advantage in each direction across supported members |
| Net | A gains minus B gains, with sign and favored driver label |
| Pattern | Directional, mixed, balanced or insufficient as returned by Python |
| Inspect | Member turns, gains, excluded regions, reasons and evidence links |

Keep mixed complexes, unknown classes and straights visible as separate context. A corner can be slow in a chosen driver's lap without changing its frozen reference class. Display “No eligible units in this class” when the class is absent, and “Insufficient evidence” for inadequate support. Neither condition is a 0.00 s tie.

A headline about gaining through high/medium while losing through low-speed windows requires the methodology's coverage, counts, materiality and sign-stability checks. Show opposing member gains and qualifying exceptions. Avoid “only” or “all” where the member evidence is mixed or incomplete. Carry the two phase labels and cross-phase warning into this section. The backend owns the wording and evidence references so UI and export agree.

Below this aggregate analysis, show up to three disjoint regional observations. Each includes the signed estimate, driver names, region/turn range, measured pattern, support and an “Inspect evidence” action. Keep a short plain-language reason when fewer qualify. A class total or quality warning cannot fill a missing regional observation slot.

## 8. Sector-only workspace

Keep the header, exact selected phases/laps and context. Show one official table with S1, S2, S3, both durations, the signed sector difference, and cumulative B−A at that boundary. Draw separate labeled points or bars at S1 end, S2 end and Finish on a categorical axis. The title says “Official delta at sector ends”. Show the reason that detailed telemetry is unavailable.

This capability has no measured distance support for turn-level attribution. Omit the turn ruler, colored map, continuous telemetry/delta curves, estimated minisectors, corner classes and corner observations. Keep an explicit “Sector timing only” badge in the workspace and export. If official sector eligibility fails too, render the unavailable state and recovery options.

## 9. Map, quality and formatting

Draw the frozen reference path at equal x/y scale with start/finish, direction and reviewed corners. Apply rotation once to all geometry. Map color represents estimated local gain through the reviewed region. The marker identifies current reference distance. Unknown spans have a visible gap or hatched treatment. Provide an adjacent linked list for small screens and nonvisual inspection.

The quality panel exposes source timing, raw estimates and signed residuals by lap/pair. Identify timing-record consistency, imposed lap-edge constraints, reference calibration and interior cross-lap consistency. Show native sample counts/gaps, missing channels, distance scale factors, reference ID, profile/config/method versions, source retrieval time if known, generation time and applicable exclusions.

Format official lap times as m:ss.sss and official sectors as ss.sss. Official signed gaps retain source precision. Regional gains ordinarily use approximately hundredths of a second. The chart delta values remain labeled estimates. Speed uses km/h, throttle percent, gear integers and brake On/Off/Unavailable. Show missing values with a dash and accessible reason. Format negative zero as zero.

A quality warning remains visible during zoom, class expansion and export. A blocked spatial analysis may transition to a separately validated sector-only result. Its header names its actual capability and reason.

## 10. Export, failure and acceptance

A 1080 × 1350 analysis card uses the loaded artifact, view order and exact laps. Prioritize event, both phase/driver/time labels, official gap, compact map/delta or sector-only visual, class pattern and concise local findings, then source/method/quality footer. Place cross-phase context alongside the people and laps it qualifies. Keep text legible at half size by using compact deterministic templates. The JSON companion retains full detail and source order.

| Failure | Reader action |
| --- | --- |
| Missing import | Select another imported session or follow the import workflow |
| Driver/phase has no eligible lap | Read the reason, choose another actual phase/lap |
| Same driver selected twice | Select a different driver in one slot |
| Cross-phase selection while phases linked | Enable Independent phases or select a common phase |
| Scaffold has no computed pair | Explain the prepared-result boundary without pretending data is unavailable upstream |
| Local processing busy or failed | Retry the same selection and retain the last valid result's identity |
| No supported class pattern | Show coverage and member evidence with insufficient/mixed status |
| Unknown shared revision | Return to session inventory with an explicit missing-result explanation |
| Export or clipboard failure | Retain the comparison and offer retry, JSON download or selectable link |

Acceptance requires useful layouts at 1440×900, 768×1024 and 390×844, plus keyboard exploration and 200% text zoom. Check that every turn can be selected, ruler/sector guides align through the delta panel after resizing/zooming, the cross-phase warning survives export, a sector-only response never renders a false curve, and mixed/insufficient groups remain visible. Test an A/B swap with mixed class contributions and an eliminated driver's missing Q3 laps. See [verification](07-verification.md).
