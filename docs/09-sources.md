# Sources and verification register

Research date: 5 November 2026. This register records primary sources consulted for the blueprint. It is not a record of real-event validation; no qualifying dataset has yet been imported or checked by this scaffold.

## Primary technical sources

| Source | What it supports | Implementation consequence |
| --- | --- | --- |
| [FastF1 data reference](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/index.rst) | Entry points for timing, channels, session information and circuit annotations | Keep ingestion behind one FastF1 adapter |
| [FastF1 channel definitions and lap access](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/core.py) | Speed units, boolean brake, discrete gear, native versus merged streams, phase splitting | Native samples for calculations; explicit step interpolation |
| [Timing field definitions](https://github.com/theOehrly/Fast-F1/blob/main/docs/api_reference/timing_data.rst) | Lap/sector clocks, deletion status, generated laps, tyre metadata and timing integrity | Retain validity reasons and distinguish timing from telemetry quality |
| [Accurate-calculation guidance](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/howto_accurate_calculations.rst) | Sparse/jittery inputs and pitfalls of interpolation/integration | Compute before display resampling; expose reconciliation and uncertainty |
| [Time and date explanation](https://github.com/theOehrly/Fast-F1/blob/main/docs/data_reference/time_explanation.rst) | Session clock, UTC date and slice-relative time have different meanings | Use explicit `SessionTime - LapStartTime` for elapsed telemetry |
| [CircuitInfo implementation](https://github.com/theOehrly/Fast-F1/blob/main/fastf1/mvapi/data.py) | Approximate manually authored markers and reference-dependent marker distances | Review marker mapping and version circuit configuration |
| [FastF1 3.9.2 cache/request implementation](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/req.py) | Cache configuration, rate limiting and account-authentication integration in the pinned release | Use supported caching/authentication; retain failure states |
| [FastF1 3.9.2 release metadata](https://pypi.org/project/fastf1/3.9.2/) | Published distribution and package requirements | Analysis extra pins 3.9.2; verify that release during ingestion |
| [FastF1 license](https://github.com/theOehrly/Fast-F1/blob/main/LICENSE) | License for the software and accompanying documentation | Preserve required software notices where applicable |
| [FastF1 project notice](https://github.com/theOehrly/Fast-F1/blob/main/README.md#notice) | Project is unofficial and unaffiliated with Formula 1 companies | Do not imply endorsement in LapDNA branding |

The documentation host returned access errors during this planning session, so its upstream source files were read directly. GitHub `main` is moving; the general documentation links explain decisions but are not a reproducibility lock. The pinned 3.9.2 release metadata and request source were separately verified. Its published requirements include Python >=3.10 and pandas <3.0. The importer must record the exact installed FastF1 version and pipeline commit in every dataset. Pin remaining method-source links to the release tag/commit during ingestion implementation.

## Verified facts versus project decisions

The underlying distinction between an on/off brake signal and brake pressure is verified from the source; LapDNA cannot compute pressure from it. The 5 m grid, thresholds, canonical-reference policy, segment partition, sign convention and observation rules are **LapDNA design choices**. Their suitability must be demonstrated using the validation pack, not attributed to FastF1.

Historical coverage beginning in 2018 is the project's requested starting assumption. Coverage is not a guarantee that every session/channel is presently retrievable. The pinned 3.9.2 request implementation uses a Formula 1 account authentication adapter. That behavior is verified in source; authentication and event retrieval have not been exercised in this scaffold. The first data ticket must verify the supported access flow and availability for the selected three events before promising real-data support in the UI.

## Event evidence to add during implementation

Each reviewed real dataset needs an evidence manifest with:

- Exact season, event, round, session and phase; source retrieval UTC; selected driver/lap IDs.
- Published official classification URL for the selected recorded lap times.
- Official detailed timing/sector URL when available; otherwise explicit `feed_only` status for sector checks.
- Native sample counts and timestamp-gap summaries; lap/sector reconciliation report.
- Canonical reference ID, marker review, layout/config hash and methodology version.
- The three structured observations and a reviewer result that every sentence is supported by its displayed interval.

Start with candidate 2024 conventional qualifying sessions at Monza, Silverstone and Suzuka. Select actual pairs after eligibility and availability checks. Do not invent driver pairs, event times, lap numbers or FIA document links to fill the manifest.

## Publication and data handling

FastF1's software license does not itself establish rights to redistribute the underlying third-party timing feed. This blueprint makes no separate rights claim. Before public data publication, record the applicable source terms and the intended distribution scope in the dataset manifest. The initial repository contains original code/docs and an artificial test-only factory; no telemetry fixture is served by the app. Keep downloaded raw caches, user credentials and bulk real telemetry out of Git.

Use a compact source credit on exported cards: `Timing and telemetry via FastF1 · Local gains are estimates · Brake is on/off`. Include event/lap IDs, dataset revision and methodology version in the card metadata or companion JSON. A synthetic card must say `Synthetic development data` prominently instead of implying FastF1 supplied it.

## Research follow-ups already assigned to the roadmap

1. Verify installed-release import/cache/auth API and availability for one seed event.
2. Check official lap and sector documents for the selected pairs.
3. Review circuit marker mapping, especially Suzuka's crossover.
4. Calibrate proposed guardrails against real residuals without hiding failed cases.
5. Record source terms and artifact distribution scope before public deployment.

These follow-ups are expected implementation work, not completed evidence and not new feature ideas for the workhorse to brainstorm.
