# Results-first milestone and later run-by-run comparisons

Decision: user instruction, 7 November 2026. Implement recorded qualifying classifications first, then add individual laps/runs and full telemetry. This explicitly changes the immediate ticket order; R01 precedes the existing T01–T12 telemetry programme.

## R01 — Working recorded-results comparison

The first real-data release imports published phase/session best times and event-specific participant/team records. It supports any available circuit in the source archive, rather than restricting this timing tier to the three future telemetry profiles.

Flow: year → race → Qualifying or Sprint Qualifying (when an actual source classification exists) → exact phase → two drivers.

- Normal qualifying: Q1/Q2/Q3 from 2006 onward.
- Sprint Qualifying / historical Sprint Shootout: SQ1/SQ2/SQ3 where actual final phase classifications are available in OpenF1, from 2023 onward.
- Legacy qualifying: one published Qualifying time for the older format. The first six 2005 races have two historical qualifying components; preserve both as First qualifying and Second qualifying, with an aggregate-format warning.
- 2021–2022 sprint weekends used a different structure. Never fabricate a separate SQ1/SQ2/SQ3 session or mistake sprint race results for sprint qualifying.
- A race without published qualifying data has an honest unavailable state; a calendar date is not a result.
- Each driver carries the team from that specific source event/session, including mid-season substitutions and team changes. Do not join a past driver to their current team.
- Preserve provider classification position. It is not determined by taking the minimum time across all phases.
- Compare exact same-phase bests, with B−A in milliseconds. Keep a missing Q3 time null; never substitute Q2.
- latest_timed_phase/latest_time_ms identify the last declared timing field with a value, not a specific lap identity or proof of the last phase attempted. Where a historical QUALIFYING overall field exists, preserve that source-published duration and its format; never compute a ranking from the minimum of component times.
- Show all source roster entries, including no-time and native DNS/DSQ cases; restricted results are not eligible comparisons.
- Display a phase breakdown and gap bars, plus clear source/retrieval/coverage information. No fabricated continuous distance delta, sectors, corner findings or telemetry from final times alone.
- Preserve the separate labelled synthetic telemetry preview. Keep the detailed lap workspace available as future work.

## Data coverage and import boundary

R01 imports every qualifying classification in the paginated Jolpica archive (11,386 rows from 1994) and backfills whole missing historical events from F1DB v2026.19.0. The publication spans **1950–2026: 1,168 qualifying events**, plus **24 Sprint Qualifying sessions from 2023–2026**, with **27,581 driver-result rows** including explicit no-time/restricted records. Modern three-phase data starts in 2006; missing values and earlier formats remain explicit. The API coverage manifest is authoritative for actual imported years, event/session counts and timed rows; source coverage is not a guarantee that every driver has a valid time.

F1DB supplies 631 historical events missing from Jolpica. Another 23 complete event classifications use F1DB to preserve native exclusion/disqualification status not exposed by Jolpica's qualifying response. No driver rows are spliced between providers. Mexico 2026 is one such event: Lawson's native DSQ remains visible and ineligible, instead of trusting a duplicated numeric position. Source timings/positions are preserved; the app does not recalculate the classification from phase minima. F1DB attribution and CC BY 4.0 terms accompany its normalized data.

Source historical first/second-session component times are retained where available for F1DB events, alongside the separately published overall time. Aggregate and Indianapolis four-lap formats carry explicit warnings. Implausible component durations outside the supported positive, at-most-30-minute timing range remain unavailable with a reason; raw source values are retained privately rather than guessed or truncated.

Only final classification facts and supporting calendar/driver/session metadata are imported in this milestone. High-frequency telemetry, all individual laps, radio, weather series and race-by-race strategy datasets remain separate work. Do not label classification bests as completed telemetry ingestion.

The 2005 exception is documented in [Formula 1's qualifying-format history](https://www.formula1.com/en/latest/article/deciding-the-grid-a-history-of-f1-qualifying-formats.1oh1hemlnZ4x9rt2nff8vn). Preserve the source's separate components without presenting a computed sum as a recorded lap.

## Storage and repeatability

1. scripts/import_classifications.py fetches public source records with bounded requests, retries, pagination/count validation and reusable raw cache.
2. Raw responses remain ignored under work/classification-source, including request URL, retrieval UTC and content hash.
3. scripts/publish_classifications.py normalizes the whole archive using Python contracts. It matches Sprint Qualifying to a unique same-country calendar weekend, not a guessed round number. Ambiguous matches fail. The pinned F1DB archive is checked against its published checksum and only explicitly selected files are extracted.
4. Validated public classification facts are published by season under services/api/src/lapdna/classification_snapshots; a coverage manifest states actual availability.
5. Full source-stamped calendar snapshots support those imported years.
6. Vercel bundles these compact read-only publications. Ordinary result pages make no upstream result download. Refresh/republication is an explicit operator operation.
7. Future source corrections create a new reviewed publication/commit; source freshness remains visible. Raw caches, credentials and bulk telemetry never enter Git.

## Required user acceptance check

Use the 2026 Mexico City Grand Prix, source round 19:
- 22 classified driver rows are available in the fetched qualifying source.
- Team labels come from this event's 2026 classification.
- Choose Q1/Q2/Q3 and any two eligible drivers; times must match their exact source phase.
- Hamilton's published Q3 time is 1:16.514 in the imported source; the same driver's Q1/Q2 values must remain distinct.
- Leclerc's Q3 time is 1:16.633, so the same-phase B−A gap against Hamilton is +0.119 s. Lawson's DSQ is retained even though source times are present.
- An eliminated driver's absent Q3 stays unavailable, while their earlier recorded phase can be selected.
- Mexico has no separate Sprint Qualifying session in the inspected source metadata; do not show a populated SQ option.
- Year/race/session/phase/driver choices survive a link refresh and browser navigation.
- Swapping drivers reverses the signed gap without changing recorded times.

Also check an actual Sprint Qualifying weekend, an older season with different driver/team assignments, the historical 2005 two-component format and a season before the imported qualifying archive.

## R02 — Individual laps and runs (deferred, requested)

After R01 acceptance, implement the actual T01/T02 lap import and eligibility gates before extending selectors.

- Retain actual session, phase, source lap number, timestamps, validity, deletion status, tyre context and source capability per lap.
- Distinguish phase best from each actual lap. A classification best is not a fabricated lap object.
- Add independent lap selectors for each driver; do not assume both had the same number of attempts.
- Define run labels from reviewed session activity/tyre-run context. Run 1 / Run 2 is not necessarily the first/second recorded lap: out laps, preparation laps and repeated push laps may exist.
- Preserve the underlying actual lap IDs and elapsed time between the selected attempts. An aligned run-number comparison is a convenience, not proof of matched conditions.
- Add explicit phase/cross-phase and context qualifications using the existing methodology. Missing/deleted/ineligible runs remain visible with reasons.
- Only then connect recorded sectors and validated native telemetry, distance alignment, track map, corner classes, evidence and exports through T03–T12.

The existing numerical method, sign convention, source-fidelity rules and synthetic-isolation boundaries remain unchanged. R01 does not satisfy any real telemetry acceptance gate.

## Operator commands

Run from the Desktop repository. The initial fetch is resumable; cached reruns make no source requests. Use --refresh deliberately for a new publication; the F1DB release is pinned in the importer and must be reviewed/updated when newer results are needed.

```powershell
.venv\Scripts\python scripts/import_classifications.py --through-year 2026
.venv\Scripts\python scripts/publish_classifications.py
.venv\Scripts\python -m pytest services/api/tests
npm run contracts:check
npm run test:web
npm run typecheck
npm run build
```

Raw cache: work/classification-source. Published data: services/api/src/lapdna/classification_snapshots. All 77 source-stamped calendar snapshots are bundled. A recent bundled calendar uses the existing six-hour freshness window on a cold instance, avoiding an unnecessary upstream request; older snapshots still attempt refresh and expose stale fallback status.
