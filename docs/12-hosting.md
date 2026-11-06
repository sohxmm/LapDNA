# Hosted preview

Deployed 6 November 2026 to [LapDNA on Vercel](https://lapdna.vercel.app). Open the [telemetry design preview](https://lapdna.vercel.app/?preview=1) to explore the fictional six-turn example.

## What is deployed

- The React/Vite frontend and lazy-loaded ECharts telemetry workspace.
- The opt-in synthetic example, including turn selection, shared cursor, local-gain strip, corner-speed summary and sector-only mode.
- The existing FastAPI scaffold as one same-origin Python function. Health, empty inventory/catalogue and selection validation run on the host.
- No real session files, upstream cache, local QA fixture, source credentials or ingestion dependencies.

The ordinary home page intentionally reports that no qualifying sessions have been imported. The demo's Sample A/B, lap times, curves, turns and findings are all synthetic. A successful deployment does not validate a real lap comparison.

## Configuration

Deploy from the repository root, not apps/web. `vercel.json` selects Vite, runs npm ci / npm run build, serves apps/web/dist, and routes /api/v1/* to api/index.py. The entrypoint loads the existing services/api/src/lapdna package; it does not introduce a second API implementation. The Python source is explicitly bundled.

`requirements.txt` pins only the API's FastAPI/Pydantic runtime. Numerical dependencies and development/test tools stay in the separate local locks. `.vercelignore` excludes data, work, environment files, local Python/Node environments, generated local outputs and non-runtime material. The local `.python-version` is excluded because Vercel currently uses supported Python 3.12 by default, while the development setup remains Python 3.11. [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python).

Deployment metadata under .vercel is local and ignored. Reuse the linked lapdna project; do not create another project on each deploy. Current manual deployment command:

```powershell
npx --yes vercel@65.12.1 deploy --prod --yes --scope sohxm44s-projects
```

The stable production alias is used for this preview. Provider preview URLs may require the owner's Vercel sign-in; the stable alias was verified by unauthenticated HTTP. GitHub push and hosting deployment are separate steps until a Git integration is configured.

## Verification

Local checks: 44 Python tests, 3 client tests, TypeScript checking and the production build passed. The serverless entrypoint also returned the expected local health/inventory/missing-data responses.

Hosted HTTP checks:

| Request | Observed |
| --- | --- |
| GET / | 200 HTML |
| GET /?preview=1 | 200 HTML |
| GET /api/v1/health | 200, lapdna-api healthy |
| GET /api/v1/sessions | 200, schema 1.1.0, empty sessions |
| GET /api/v1/catalog | 200, schema 1.1.0, empty comparisons |
| GET /api/v1/sessions/missing/laps | 404, session_not_found |
| POST /api/v1/compare without imported data | 409, data_not_imported |
| GET /assets/index-CfpmbKqr.js | 200 JavaScript |

Browser verification passed: the hosted chart chunks render, T3 selection changes the shared range, keyboard cursor movement updates the numeric readout, the sector-only view shows discrete crossings, and the ordinary home page reports the empty real-session inventory. Keep source code and the hosted result separate: API health proves serving, not ingestion or analysis accuracy.

## Current limitations

1. No real session has been imported and validated. Full real driver/phase/lap comparisons therefore have no selectable data on this host.
2. The cold comparison engine is unfinished. The service can serve prepared validated artifacts; a cache miss returns an explicit preparation error. T01–T05 implement import, native eligibility, alignment, reconciliation, metrics and evidence.
3. Real reference track maps, production map/chart synchronization, dense turn-label handling, complete evidence/quality details, saved comparison URLs and export cards remain later tickets. The demo uses a fictional loop without a real circuit map.
4. The high/medium/low findings visible in the demo are constructed. Actual class findings need reviewed reference windows, sufficient native samples, coverage and sensitivity gates.
5. Steering angle and brake pressure are unavailable in the chosen public channels. Brake is on/off. Estimated 100 m mini-sectors are not recorded timing splits, and sector timing alone cannot locate a loss inside a corner.
6. Vercel's function-local files are not the planned durable dataset/cache store. Adding real data requires an explicit durable artifact/object-store or separate backend/worker design. Import jobs and large numerical work should remain outside ordinary page requests.

The next implementation gate remains T01 in the existing plan. This host provides a reviewable UI and API foundation while that work proceeds.
