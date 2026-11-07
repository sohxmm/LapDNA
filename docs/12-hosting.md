# Hosted preview

Updated 7 November 2026 at [LapDNA on Vercel](https://lapdna.vercel.app). The app starts with the current year, loads that year's race calendar, then opens the selected race's studio. Open the [telemetry design preview](https://lapdna.vercel.app/?preview=1) to explore the preserved fictional six-turn example.

**R01 is live:** [2026 Mexican GP qualifying](https://lapdna.vercel.app/?year=2026&race=2026-19&view=studio). Real recorded classifications cover 1,168 qualifying events from 1950–2026 and 24 Sprint Qualifying sessions from 2023–2026. Event-specific drivers/teams, exact phase bests, historical formats, DSQ/DNS and missing values are preserved. Individual runs/laps and native telemetry remain the next stage.

## What is deployed

- The React/Vite frontend and lazy-loaded ECharts telemetry workspace.
- The opt-in synthetic example, including turn selection, shared cursor, local-gain strip, corner-speed summary and sector-only mode.
- The existing FastAPI scaffold as one same-origin Python function. Health, empty inventory/catalogue and selection validation run on the host.
- Sourced Jolpica calendar metadata, default current year, historical season browsing, exact year/round studio filtering and refreshable navigation links. Warm caching and bundled, provenance-stamped 1950–2026 calendars preserve explicit freshness warnings.
- Per-driver native-channel provenance contracts and availability-aware telemetry rendering. All four preview channels remain synthetic and unchanged; no source data is inferred from speed for production results.
- Read-only bundled classification publications and their coverage API, with 27,581 driver-result rows. Recorded timing comparisons and gap bars use actual same-phase durations, not a fabricated distance curve. Source-stamped calendars now cover all 77 seasons.
- No native telemetry session files, raw upstream cache, local QA fixture, source credentials or numerical ingestion dependencies are bundled.

The ordinary home page displays a sourced race calendar. Published races open recorded-results comparison; absent/future results remain unavailable. The demo's Sample A/B, lap times, curves, turns and findings are all synthetic. Scheduled qualifying start times do not establish session completion. A recorded phase-best comparison does not establish distance alignment, native telemetry quality or a particular run identity.

## Configuration

Deploy from the repository root, not apps/web. `vercel.json` selects Vite, runs npm ci / npm run build, serves apps/web/dist, and routes /api/v1/* to api/index.py. The entrypoint loads the existing services/api/src/lapdna package; it does not introduce a second API implementation. The Python source is explicitly bundled.

`requirements.txt` pins only the API's FastAPI/Pydantic runtime. Numerical dependencies and development/test tools stay in the separate local locks. `.vercelignore` excludes data, work, environment files, local Python/Node environments, generated local outputs and non-runtime material. The local `.python-version` is excluded because Vercel currently uses supported Python 3.12 by default, while the development setup remains Python 3.11. [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python).

Deployment metadata under .vercel is local and ignored. Reuse the linked lapdna project; do not create another project on each deploy. Current manual deployment command:

```powershell
npx --yes vercel@65.12.1 deploy --prod --yes --scope sohxm44s-projects
```

The stable production alias is used for this preview. Provider preview URLs may require the owner's Vercel sign-in; the stable alias was verified by unauthenticated HTTP. GitHub push and hosting deployment are separate steps until a Git integration is configured.

The current deployed application code is commit `c9a8a75`, deployment `dpl_HzNFBd6TghXuFWRiotwskMcHiv1C`. Later documentation-only commits do not require redeployment. [Deployment inspection](https://vercel.com/sohxm44s-projects/lapdna/HzNFBd6TghXuFWRiotwskMcHiv1C).

## Verification

Local checks: 144 Python tests passed with one Windows symlink test skipped; 16 client tests, generated-contract checking, TypeScript checking and production build passed. The chart chunk retains a non-fatal size advisory. [Ubuntu CI passed](https://github.com/sohxmm/LapDNA/actions/runs/42293091029).

Hosted HTTP checks:

| Request | Observed |
| --- | --- |
| GET / | 200 HTML |
| GET /?preview=1 | 200 HTML |
| GET /api/v1/health | 200, lapdna-api healthy |
| GET /api/v1/seasons | 200, schema 1.0.0, current year 2026 |
| GET /api/v1/calendar/2026 | 200, schema 1.0.0, 23 events in the retrieved source calendar |
| GET /api/v1/calendar/2024 | 200, schema 1.0.0, 24 events in the retrieved source calendar |
| GET /api/v1/sessions | 200, schema 1.2.0, empty sessions |
| GET /api/v1/catalog | 200, schema 1.2.0, empty comparisons |
| GET /api/v1/classifications/coverage | 200, 77 years, 1,168 qualifying + 24 Sprint Qualifying sessions |
| GET /api/v1/classifications/2026/19 | 200, 22 drivers, F1DB source; HAM Q3 76514 ms, LEC 76633 ms, LAW disqualified |
| GET /api/v1/classifications/2026/2 | 200, separate Qualifying and Sprint Qualifying sessions |
| GET /api/v1/classifications/1950/1 | 200, historical single published qualifying field, 21 event-specific driver entries |
| GET /api/v1/classifications/1983/10 | 200, native historical components and published overall value |
| GET /api/v1/classifications/2005/1 | 200, first/second historical qualifying components |
| GET /api/v1/sessions/missing/laps | 404, session_not_found |
| POST /api/v1/compare without imported data | 409, data_not_imported |
| GET the built /assets/index-*.js referenced by home HTML | 200 JavaScript |

Browser verification covers the current-year default, historical calendar change, race studio, deep-link refresh/back navigation and honest unimported-race state. Desktop/mobile checks cover the preserved demo, T3 selection, keyboard cursor, synthetic channel labels and discrete sector-only crossings. Opening a race resets page position and moves keyboard focus to the studio title. Keep source code and the hosted result separate: API health proves serving, not ingestion or analysis accuracy.

## Current limitations

1. Final phase/session classifications are imported, but individual qualifying laps/runs and native telemetry have not been imported. They cannot identify matched run 1/run 2 attempts or support local corner/braking claims.
2. The cold comparison engine is unfinished. The service can serve prepared validated artifacts; a cache miss returns an explicit preparation error. T01–T05 implement import, native eligibility, alignment, reconciliation, metrics and evidence.
3. Real reference track maps, production map/chart synchronization, dense turn-label handling, complete evidence/quality details, saved comparison URLs and export cards remain later tickets. The demo uses a fictional loop without a real circuit map.
4. The high/medium/low findings visible in the demo are constructed. Actual class findings need reviewed reference windows, sufficient native samples, coverage and sensitivity gates.
5. Steering angle and brake pressure are unavailable in the chosen public channels. Brake is on/off. Estimated 100 m mini-sectors are not recorded timing splits, and sector timing alone cannot locate a loss inside a corner.
6. R01 uses committed read-only classification publications bundled with the function; it needs no writable runtime store. Larger normalized telemetry datasets and writable comparison caches still require a reviewed durable storage/worker design. Import jobs remain outside page requests. Current result refresh/publication is an explicit operator command; F1DB release updates are reviewed and pinned.
7. Demo prose is fixed; prepared real artifacts render saved evidence summaries. No LLM provider is configured or called. The optional fresh-narrative design in [analysis generation](14-analysis-generation.md) follows validated numerical evidence; it cannot invent missing measurements or establish why time was lost.

The user acceptance milestone is R01 at Mexico 2026. The subsequent individual-run milestone R02 resumes T01/T02 before the full telemetry pipeline. [Scope and commands](16-results-first-milestone.md).
