# LapDNA

Where did the lap time go? Compare two qualifying laps on a common track-distance axis and connect approximate local gains to observed telemetry.

**Hosted app:** [LapDNA](https://lapdna.vercel.app). See [deployment status](docs/12-hosting.md) for the exact live release; local imports are not automatically deployed.

[Latest archive completion and deployment receipt](docs/21-archive-coverage.md) supersedes the first-batch checkpoint below when a later batch is confirmed.

**Status, 10 November 2026:** all 217 past qualifying and actual Sprint Qualifying sessions in the approved 2018–2026 scope are imported, audited and deployed. The 2026 archive contains 20 Q and six SQ sessions; 12 offer verified graph choices. Import coverage does not imply every lap/pair supports distance analysis. The [coverage ledger](config/telemetry-coverage.json), [live receipt](docs/21-archive-coverage.md) and [year/field guide](docs/18-data-availability-by-year.md) record the distinction. Earlier years retain recorded timing comparisons.

The studio offers actual event-specific drivers/teams, Q/SQ phases and eligible lap selection; source-coloured synchronized speed, throttle, gear and binary-brake traces; distance delta; linked approximate performance maps; evidence-based observations and PNG/JSON export. Quality failures remain timing-only or unavailable. Dark/light themes persist. No synthetic preview, fabricated fallback channel or runtime LLM claim is shipped.

## Start here

- [Verified telemetry expansion and prefinal release](docs/20-verified-telemetry-release.md)
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

For real telemetry choose 2024 → Italian Grand Prix → Lap telemetry. The generated pilot publication is deliberately ignored by Git; a fresh checkout must run the [reviewed import/publication commands](docs/19-monza-2024-pilot.md) before it has native lap data. An absent local publication keeps the recorded timing views usable. If port 5173 is unavailable, run `npm run dev --workspace @lapdna/web -- --port 5273`.

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
