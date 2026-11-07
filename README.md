# LapDNA

Where did the lap time go? Compare two qualifying laps on a common track-distance axis and connect approximate local gains to observed telemetry.

**Hosted app:** [LapDNA](https://lapdna.vercel.app) · [2026 Mexican GP qualifying](https://lapdna.vercel.app/?year=2026&race=2026-19&view=studio) · [Synthetic telemetry demo](https://lapdna.vercel.app/?preview=1). The real Monza 2024 telemetry pilot is implemented and checked locally; its final hosted release verification is pending. See [deployment status](docs/12-hosting.md) and [the pilot guide](docs/19-monza-2024-pilot.md).

**Status, 8 November 2026:** recorded-results comparison covers 1,168 qualifying events from 1950–2026 and 24 Sprint Qualifying sessions from 2023–2026. The Monza 2024 pilot adds all 20 event-specific drivers, 276 actual laps, same/independent Q phases, real speed/throttle/gear/binary-brake traces, raw distance delta, linked performance map, supported corner analysis and PNG/JSON export. It has 79 timing-eligible laps: 40 support telemetry and 39 remain sector-only; 197 ineligible records retain reasons. Shared dark/light themes persist across navigation/reload. Native car/position records come from OpenF1 and are identity-matched to pinned TracingInsights timing clocks/flags; source composition and uncertainty remain visible. Other circuits/years are not implied by this pilot. The four-channel synthetic preview stays separate.

## Start here

- [Blueprint and reading order](docs/00-blueprint.md)
- [Implementation tickets](docs/06-implementation-plan.md)
- [Current handoff](docs/10-handoff.md)
- [Results-first scope, coverage, import commands and later run selection](docs/16-results-first-milestone.md)
- [Approved UI and verified 2018–2026 telemetry rollout](docs/17-approved-ui-and-telemetry-rollout.md)
- [Data available by year, fields and useful outputs](docs/18-data-availability-by-year.md)
- [Monza 2024 real-data pilot, examples and preparation commands](docs/19-monza-2024-pilot.md)
- [Implementing with GPT-6.1 Sol](docs/11-implementation-workflow.md)
- [20-source qualifying data audit](docs/13-data-source-audit.md)
- [Detailed data-point inventory and rollout](docs/15-data-points-and-rollout.md)
- [Analysis generation and optional LLM wording](docs/14-analysis-generation.md)
- [Contributor rules](AGENTS.md)

## Local setup

Use Node.js 24 and Python 3.11. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r services/api/requirements.lock
.venv\Scripts\python -m pip install --no-deps -e services/api
npm ci
```

Start the API in one terminal and the frontend in another:

```powershell
.venv\Scripts\python -m uvicorn lapdna.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173). Vite proxies `/api` to port 8000. On macOS/Linux replace `.venv\Scripts\python` with `.venv/bin/python`.

Use the **Synthetic demo** link, or append `?preview=1`, to inspect the explicitly synthetic trace layout. For the real pilot choose 2024 → Italian Grand Prix → Lap telemetry. The generated pilot publication is deliberately ignored by Git; a fresh checkout must run the [reviewed import/publication commands](docs/19-monza-2024-pilot.md) before it has native lap data. An absent local publication keeps the recorded timing views usable. If port 5173 is unavailable, run `npm run dev --workspace @lapdna/web -- --port 5273`.

## Verify

```powershell
.venv\Scripts\python -m pytest services/api/tests
npm run test:web
npm run contracts:check
npm run typecheck
npm run build
```

Pydantic is the contract source of truth. After intentional model changes, run `npm run contracts` and commit the schemas and TypeScript output together. `LAPDNA_PYTHON` can select a different Python executable for this command.

## Project layout

```text
apps/web/             React + TypeScript browser workspace
services/api/         FastAPI, native alignment/comparison engine and contracts
packages/contracts/   Generated OpenAPI, JSON Schema, and TypeScript
config/circuits/      Circuit seeds; Monza profile is prepared from reviewed source markers
data/                 Local ignored data; no upstream cache in Git
docs/                 Product, methodology, design, tickets, operations
scripts/              Contract generation, real import/publication and validation utilities
```

Positive delta means **B has taken longer than A**, so A is ahead. Local estimates must never be presented as causal proof or exact corner timing. The brake channel represents on/off state, not pressure. See [methodology](docs/03-telemetry-methodology.md).

The FastF1 software licence does not automatically grant rights to redistribute its upstream datasets. Keep raw caches private and review data terms before a public release. See [sources](docs/09-sources.md).
