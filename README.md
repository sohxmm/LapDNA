# LapDNA

Where did the lap time go? Compare two qualifying laps on a common track-distance axis and connect approximate local gains to observed telemetry.

**Status: blueprint and runnable foundation.** This repository currently contains a typed read-only API, an honest empty-state web workspace, generated contracts, checks, and the implementation plan. FastF1 ingestion, alignment, charts, observations, and export are planned work. No real telemetry is bundled and no comparison has been validated yet.

## Start here

- [Blueprint and reading order](docs/00-blueprint.md)
- [Implementation tickets](docs/06-implementation-plan.md)
- [Current handoff](docs/10-handoff.md)
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

## Verify

```powershell
.venv\Scripts\python -m pytest services/api/tests
npm run contracts:check
npm run typecheck
npm run build
```

Pydantic is the contract source of truth. After intentional model changes, run `npm run contracts` and commit the schemas and TypeScript output together. `LAPDNA_PYTHON` can select a different Python executable for this command.

## Project layout

```text
apps/web/             React + TypeScript browser workspace
services/api/         FastAPI artifact reader and Python domain contracts
packages/contracts/   Generated OpenAPI, JSON Schema, and TypeScript
config/circuits/      Circuit seed manifest; geometry awaits validation
data/                 Local ignored data; no upstream cache in Git
docs/                 Product, methodology, design, tickets, operations
scripts/              Contract generation and later ingestion utilities
```

Positive delta means **B has taken longer than A**, so A is ahead. Local estimates must never be presented as causal proof or exact corner timing. The brake channel represents on/off state, not pressure. See [methodology](docs/03-telemetry-methodology.md).

The FastF1 software licence does not automatically grant rights to redistribute its upstream datasets. Keep raw caches private and review data terms before a public release. See [sources](docs/09-sources.md).
