# Sources and verification register

Research date: 5 November 2026. This register records primary sources and one historical source-availability probe. The first complete session import and comparison validation belong to T01 onward.

## Primary technical sources

| Source | What it supports | Implementation consequence |
| --- | --- | --- |
| [FastF1 data reference](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/index.rst) | Entry points for timing, channels, session information and circuit annotations | Keep ingestion behind one FastF1 adapter |
| [FastF1 3.9.2 channel definitions and lap access](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py) | Enumerated car/position channels and `split_qualifying_sessions()` | Use native speed, throttle, gear and brake-state records. Record each lap's phase. Omit steering and pressure traces. |
| [Timing field definitions](https://github.com/theOehrly/Fast-F1/blob/main/docs/api_reference/timing_data.rst) | Lap/sector clocks, deletion status, generated laps, tyre metadata and timing integrity | Retain validity reasons and distinguish timing from telemetry quality |
| [Accurate-calculation guidance](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/howto_accurate_calculations.rst) | Sparse/jittery inputs and pitfalls of interpolation/integration | Compute before display resampling; expose reconciliation and uncertainty |
| [Time and date explanation](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/time_explanation.rst) | Session clock, UTC date and slice-relative time have different meanings | Use explicit `SessionTime - LapStartTime` for elapsed telemetry |
| [CircuitInfo implementation](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/mvapi/data.py) | Approximate manually authored markers and reference-dependent marker distances | Review marker mapping and version circuit configuration |
| [FastF1 3.9.2 cache/request implementation](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/req.py) | Cache configuration, rate limiting and account-authentication integration in the pinned release | Use supported caching/authentication; retain failure states |
| [FastF1 3.9.2 release metadata](https://pypi.org/project/fastf1/3.9.2/) | Published distribution and package requirements | Analysis extra pins 3.9.2; verify that release during ingestion |
| [FastF1 license](https://github.com/theOehrly/Fast-F1/blob/main/LICENSE) | License for the software and accompanying documentation | Preserve required software notices where applicable |
| [FastF1 project notice](https://github.com/theOehrly/Fast-F1/blob/main/README.md#notice) | Project is unofficial and unaffiliated with Formula 1 companies | Do not imply endorsement in LapDNA branding |
| [OpenF1 laps](https://openf1.org/docs/#laps) | Separate fields for lap duration, S1/S2/S3 durations and per-sector status-code arrays | Optional sector-timing adapter. Keep mini-sector status codes categorical. |
| [OpenF1 car data](https://openf1.org/docs/#car-data) | Timestamped car channels sampled at approximately 3.7 Hz, including a 0/100 brake switch | Evaluate this source separately before use. Normalize units and preserve its provenance. |

The general documentation links follow the project's moving `main` branch. The channel, phase and request definitions above were checked against the pinned 3.9.2 source. Its release metadata specifies Python >=3.10 and pandas <3.0. The importer records the installed FastF1 version and pipeline commit in every dataset.

## Data source selection

1. Use FastF1 for imported qualifying session timing, native car samples, position, phase membership and circuit annotations. Preserve each source stream's own timestamps before alignment. The source's car channel list supports the four telemetry panels in LapDNA. Reproducing the reference image's steering row would require an additional data source with measured steering angle. [Pinned FastF1 channels](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py)
2. Use validated recorded S1/S2/S3 values for discrete sector comparisons when telemetry alignment is unavailable. OpenF1 documents historical data from 2023 onward and publishes sector durations. Its `segments_sector_*` values encode mini-sector statuses. A numeric within-sector delta requires measured timing splits or a telemetry-derived estimate. Keep OpenF1 as an optional adapter, with a separate source version, lap matching and eligibility verification. [OpenF1 API documentation](https://openf1.org/docs/#laps)
3. Derive the local performance strip from aligned telemetry in LapDNA's 100 m intervals. Label it “Estimated minisectors” and publish each bin's bounds, source and supported gain. The aligned time arrays supply the individual traversal durations. These intervals and the low/medium/high cutoffs are project choices documented in the [methodology](03-telemetry-methodology.md).

Raw car samples and official timing records describe different measurements. Adding display points through interpolation preserves the original source sampling density. The source matrix distinguishes measured channel values, categorical status codes and LapDNA estimates. [FastF1 channels](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/core.py), [OpenF1 laps](https://openf1.org/docs/#laps)

## Historical source availability probe

The standard-library utility `scripts/probe_openf1.py` requests a named historical session, the chosen driver's lap records and the car samples inside one reported lap window. Run `python scripts/probe_openf1.py --year 2024 --circuit Monza --driver 4` from the repository root to repeat it. The probe prints an inventory and saves no raw responses.

| Verified on 5 November 2026 | Observed response |
| --- | --- |
| OpenF1 session | 2024 Monza qualifying, `session_key=9586` |
| Driver number 4 | 12 returned lap records, seven with three positive sectors, positive lap duration and a start timestamp |
| Example record | Lap 11, reported duration 79.327 s |
| Reported S1/S2/S3 | 26.492 s / 26.579 s / 26.256 s, summing to the lap duration with 0 ms residual |
| Car data in the reported lap window | 306 timestamped rows. Speed, throttle, gear, brake, RPM and DRS were present. |
| Mini-sector statuses | All three `segments_sector_*` arrays were present. |

This confirms public historical timing and sampled car channels for one driver/session. The probe selected the shortest returned complete timing record for its sample. T01–T04 still need to establish phase membership, validity/deletion flags, native coverage and timing alignment. A reviewer must match the actual selected laps to the FIA reports before claiming external reconciliation. The FastF1 importer and its authenticated access path also remain to be exercised. [Reported source lap](https://api.openf1.org/v1/laps?session_key=9586&driver_number=4&lap_number=11), [OpenF1 definitions](https://openf1.org/docs/#laps)

## Published sector checks for the candidate sessions

The FIA hosts a qualifying session sector analysis for each 2024 candidate circuit. Each document lists driver laps and the three sector times. Match the selected event, driver and actual lap to the published row during validation. Session-best sector leaderboards can combine performances from different laps. Keep a link and verification record for each comparison under review, and check the published document's distribution terms before packaging any data.

- [Monza 2024 qualifying sector analysis](https://www.fia.com/sites/default/files/2024_16_ita_f1_q0_timing_qualifyingsessionsectoranalysis_v01.pdf)
- [Silverstone 2024 qualifying sector analysis](https://www.fia.com/sites/default/files/2024_12_gbr_f1_q0_timing_qualifyingsessionsectoranalysis_v01.pdf)
- [Suzuka 2024 qualifying sector analysis](https://www.fia.com/sites/default/files/2024_04_jpn_f1_q0_timing_qualifyingsessionsectoranalysis_v01_0.pdf)

These links verify the availability of external timing references. Checking them against specific imported laps is an ingestion/acceptance task. No comparison result or broadcast graphic is copied into the scaffold.

## Verified facts versus project decisions

The source defines brake application as a switch. LapDNA sets its own 5 m display grid, 100 m estimated minisectors, 150/250 km/h class cutoffs, canonical reference, additive segments, sign convention and observation rules. The validation pack must test these choices on actual sessions before release.

Historical coverage beginning in 2018 is the project's requested starting assumption. Coverage is not a guarantee that every session/channel is presently retrievable. The pinned 3.9.2 request implementation uses a Formula 1 account authentication adapter. That behavior is verified in source; authentication and event retrieval have not been exercised in this scaffold. The first data ticket must verify the supported access flow and availability for the selected three events before promising real-data support in the UI.

## Event evidence to add during implementation

Each reviewed real dataset needs an evidence manifest with:

- Exact season, event, round, session, both selected lap IDs and both phase labels, plus source retrieval UTC.
- Published official classification URL for the selected recorded lap times.
- Official detailed timing/sector URL when available; otherwise explicit `feed_only` status for sector checks.
- Native sample counts and timestamp-gap summaries; lap/sector reconciliation report.
- Canonical reference ID, marker and apex-window review, layout/config hash, class thresholds and methodology version.
- Result tier, derived-minisector coverage, corner-class expected/included units and gross gains/losses, plus any cross-phase context warning.
- Supported local observations and a reviewer result that every sentence resolves to its evidence and displayed interval(s).

Start with candidate 2024 conventional qualifying sessions at Monza, Silverstone and Suzuka. Select actual pairs after eligibility and availability checks. Do not invent driver pairs, event times, lap numbers or FIA document links to fill the manifest.

## Publication and data handling

FastF1's software license covers the software. Record the underlying timing source's terms and intended distribution scope in each dataset manifest before public data publication. Keep downloaded raw caches, user credentials and bulk real telemetry out of Git. Mark synthetic test or interface material explicitly.

Use the actual source and capability on exported cards. A telemetry example credit reads `Timing and telemetry via FastF1 · Local gains are estimates · Brake is on/off`. A sector-only example reads `Recorded sector timing via FastF1` when FastF1 supplied it. Include event/lap IDs, both phases, dataset revision, methodology version and any context warnings. Label synthetic examples `Synthetic development data` prominently.

## Research follow-ups already assigned to the roadmap

1. Verify installed-release import/cache/auth API and availability for one seed event.
2. Match the chosen actual laps to the linked sector reports and record phase/lap identity and residuals.
3. Review circuit marker mapping, especially Suzuka's crossover.
4. Audit the proposed guardrails, minisector support and corner classification against real laps, retaining failed cases.
5. Record source terms and artifact distribution scope before public deployment.

These follow-ups are expected implementation work, not completed evidence and not new feature ideas for the workhorse to brainstorm.
