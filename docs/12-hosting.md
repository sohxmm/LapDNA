# Hosted preview

Updated 8 November 2026 at [LapDNA on Vercel](https://lapdna.vercel.app). The real [Monza 2024 studio](https://lapdna.vercel.app/?year=2024&race=2024-16&view=studio) is live, with persistent blue dark/off-white light themes. The landing opens the current-year calendar; existing direct links remain valid. The [synthetic preview](https://lapdna.vercel.app/?preview=1) remains separate. Telemetry expansion targets verified sessions/channels in 2018–2026; older timing comparisons remain available.

**R01 remains live:** [2026 Mexican GP qualifying](https://lapdna.vercel.app/?year=2026&race=2026-19&view=studio). Recorded classifications cover 1,168 qualifying events from 1950–2026 and 24 Sprint Qualifying sessions from 2023–2026. Monza additionally has 20 drivers and 276 actual laps: 40 telemetry, 39 sector-only and 197 unavailable with reasons. [Pilot source and acceptance](19-monza-2024-pilot.md); [data by year](18-data-availability-by-year.md).

## What is deployed

- The React/Vite frontend and lazy-loaded ECharts telemetry workspace.
- Sports-editorial landing, compact dark calendar/results studio, expandable Data details/full classification, and G1 with separate binary brake lanes, taller speed and symmetric delta scale.
- The opt-in synthetic example, including turn selection, shared cursor, local-gain strip, corner-speed summary and sector-only mode.
- FastAPI as one same-origin Python function, with the complete Monza roster/index and bounded on-demand comparison from pre-normalized local inputs. No request downloads a source session.
- Sourced Jolpica calendar metadata, default current year, historical season browsing, exact year/round studio filtering and refreshable navigation links. Warm caching and bundled, provenance-stamped 1950–2026 calendars preserve explicit freshness warnings.
- Per-driver native-channel provenance contracts and availability-aware telemetry rendering. All four preview channels remain synthetic and unchanged; no source data is inferred from speed for production results.
- Read-only bundled classification publications and their coverage API, with 27,581 driver-result rows. Recorded timing comparisons and gap bars use actual same-phase durations, not a fabricated distance curve. Source-stamped calendars now cover all 77 seasons.
- A compact generated Monza publication (about 985 KB compressed normalized data plus index/manifest/report) is bundled read-only. Raw 104.3 MB source records, upstream caches, local QA fixtures, credentials and numerical import dependencies remain excluded. Generated pilot files are intentionally ignored by Git and must exist before this manual deployment.
- Actual-lap/phase selection, native channel traces, a linked performance map, corner/straight and class summaries, supported observations, quality details, PNG/JSON exports and exact selection links.

The ordinary home page displays the landing; Open Studio enters the sourced current-year calendar. Published races open recorded-results comparison; absent/future results remain unavailable. The demo's Sample A/B, lap times, curves, turns and findings are all synthetic. Scheduled qualifying start times do not establish session completion. A recorded phase-best comparison does not establish distance alignment, native telemetry quality or a particular run identity.

## Configuration

Deploy from the repository root, not apps/web. `vercel.json` selects Vite, runs npm ci / npm run build, serves apps/web/dist, and routes /api/v1/* to api/index.py. The entrypoint loads the existing services/api/src/lapdna package; it does not introduce a second API implementation. The Python source is explicitly bundled.

`requirements.txt` pins only the API's FastAPI/Pydantic runtime. Numerical dependencies and development/test tools stay in the separate local locks. `.vercelignore` excludes data, work, environment files, local Python/Node environments, generated local outputs and non-runtime material. The local `.python-version` is excluded because Vercel currently uses supported Python 3.12 by default, while the development setup remains Python 3.11. [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python).

Deployment metadata under .vercel is local and ignored. Reuse the linked lapdna project; do not create another project on each deploy. Current manual deployment command:

```powershell
npx --yes vercel@65.12.1 deploy --prod --yes --scope sohxm44s-projects
```

The stable production alias is used for this preview. Provider preview URLs may require the owner's Vercel sign-in; the stable alias was verified by unauthenticated HTTP. GitHub push and hosting deployment are separate steps until a Git integration is configured.

The current deployed application code is commit `3361e03`, deployment `dpl_2jjmf7tAenA18DRBVZYQfMDk7CYt`. Later documentation-only commits do not require redeployment. [Deployment inspection](https://vercel.com/sohxm44s-projects/lapdna/2jjmf7tAenA18DRBVZYQfMDk7CYt).

## Verification

Pilot checks: 183 Python tests passed locally with one Windows symlink skip; 25 client tests, generated contracts, TypeScript and production build passed. [Ubuntu CI on the deployed commit passed](https://github.com/sohxmm/LapDNA/actions/runs/42406657115): 184 Python tests and 25 client tests. The lazy chart chunk is about 520.20 KB, with a non-fatal size advisory. The real 321-pair/reverse matrix is recorded separately in doc 19.

Hosted HTTP checks:

| Request | Observed |
| --- | --- |
| GET / | 200 HTML |
| GET /?preview=1 | 200 HTML |
| GET /api/v1/health | 200, lapdna-api healthy |
| GET /api/v1/seasons | 200, schema 1.0.0, current year 2026 |
| GET /api/v1/calendar/2026 | 200, schema 1.0.0, 23 events in the retrieved source calendar |
| GET /api/v1/calendar/2024 | 200, schema 1.0.0, 24 events in the retrieved source calendar |
| GET /api/v1/sessions | 200, one Monza session, 20 drivers and 79 selectable laps |
| GET /api/v1/catalog | 200, schema 1.2.0, empty comparisons |
| GET /api/v1/classifications/coverage | 200, 77 years, 1,168 qualifying + 24 Sprint Qualifying sessions |
| GET /api/v1/classifications/2026/19 | 200, 22 drivers, F1DB source; HAM Q3 76514 ms, LEC 76633 ms, LAW disqualified |
| GET /api/v1/classifications/2026/2 | 200, separate Qualifying and Sprint Qualifying sessions |
| GET /api/v1/classifications/1950/1 | 200, historical single published qualifying field, 21 event-specific driver entries |
| GET /api/v1/classifications/1983/10 | 200, native historical components and published overall value |
| GET /api/v1/classifications/2005/1 | 200, first/second historical qualifying components |
| GET /api/v1/sessions/missing/laps | 404, session_not_found |
| POST /api/v1/compare without imported data | 409, data_not_imported |
| POST /api/v1/compare Monza NOR lap 11 / RUS lap 17 | 200, schema 1.3.0 telemetry, 1155 points, 3 observations, raw final delta approximately +113 ms |
| GET the built /assets/index-*.js referenced by home HTML | 200 JavaScript |

Browser verification covers the current-year default, historical calendar change, race studio, deep-link refresh/back navigation and honest unimported-race state. Desktop/mobile checks cover the preserved demo, T3 selection, keyboard cursor, synthetic channel labels and discrete sector-only crossings. Opening a race resets page position and moves keyboard focus to the studio title. Keep source code and the hosted result separate: API health proves serving, not ingestion or analysis accuracy.

U01 was inspected at 1440×900, 768×1024 and 390×844, with no page-level horizontal overflow observed. Hosted checks confirm the new landing, the separate G1 synthetic preview, and Mexico Q3 Hamilton 1:16.514 versus Leclerc 1:16.633 with a +0.119 s B−A gap and Timing only status. The 200% text-zoom accessibility check remains outstanding; the preview browser did not apply the tested zoom shortcut.

The live real pilot was additionally checked at actual CSS viewport sizes 1440×900 and 390×844. Dark/light choice survives reload; exact shared NOR/RUS selection restores automatically; swap produces −0.113 s and browser Back restores the original pair. Map/turn selection updates the shared graph interval/cursor. Light and dark 1080×1350 cards were downloaded and inspected, and the evidence JSON contains the original artifact, orientation, theme and all 70 source components. Mobile expanded quality details do not cause page-level horizontal overflow. Source units remain explicit. This does not close the separate 200% text-zoom or additional-circuit acceptance gates.

## Current limitations

1. Real telemetry is imported only for Monza 2024 conventional qualifying. Other races/years keep their actual recorded timing comparisons. The importer is intentionally allowlisted; 2018–2026 source coverage is not imported archive coverage.
2. Source gaps genuinely reduce capability: Piastri's fastest Q3 lap remains sector-only because of a 1.119 s native speed gap. His later Q3 lap supports telemetry. A selected alternate lap is labelled, never presented as his phase best. Piastri Q1 has no eligible lap under the source validity/green-track gates.
3. Geometry and projected turn markers are approximate; OpenF1 source coordinates are not surveyed metres. Integrated-speed distance, local gains and boundary sensitivity remain estimates. The direct FastF1 account adapter is still unimplemented; actual source lineage is the explicit verified composite.
4. The labelled demo remains synthetic. Real category/observation text is generated from the selected numerical evidence; mixed/unknown regions and sparse classes remain qualified, and unsupported claims are withheld.
5. Steering angle and brake pressure are unavailable in the chosen public channels. Brake is on/off. Estimated 100 m mini-sectors are not recorded timing splits, and sector timing alone cannot locate a loss inside a corner.
6. The compact frozen pilot can regenerate exact comparison IDs across a cold process. Bulk archive storage, persistent multi-revision retention and broad automatic post-session updates remain future work. The disposable process cache is not durable storage. Ordinary deployment requires the generated pilot publication; no source import runs during a request or Vercel build.
7. No LLM provider is configured or called. The numerical engine generates comparison-specific summaries/templates; optional LLM wording remains an extension after those facts. Individual laps are selectable, but matched Run 1 / Run 2 labels are not inferred.

Current user acceptance is the real Monza pilot alongside R01's Mexico 2026 regression. Follow [pilot commands and boundaries](19-monza-2024-pilot.md) before expanding to another source/layout.
