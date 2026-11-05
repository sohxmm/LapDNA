# Current handoff

Last updated: 5 November 2026. Current milestone: **T00 complete — blueprint and runnable foundation**. The full analysis app is not implemented.

## Implemented

- React/TypeScript/Vite workspace with catalogue loading, honest no-data state, API failure and retry/refresh. Responsive dark visual foundation; no fake timings or track geometry.
- FastAPI read-only health, catalogue and comparison endpoints. Safe IDs and artifact-root confinement, file-size guard, structural validation and explicit invalid/blocked responses.
- Pydantic comparison contracts for metadata, shared distance/channels, raw delta, geometry, reconciliation, segment partitions, sensitivity, evidence and observations. Generated OpenAPI/JSON Schema/TypeScript stay in sync.
- Core Python and npm dependency locks, test suite and GitHub Actions workflow.
- Detailed product, architecture, numerical methodology, UX, contracts, implementation tickets, verification and operations documentation.
- Three **unverified candidate** circuit/session entries: 2024 qualifying at Monza, Silverstone and Suzuka. No upstream data is bundled or downloaded.

## Verification recorded for T00

| Check | Result |
| --- | --- |
| `.venv/Scripts/python -m pytest services/api/tests` | 26 passed |
| `npm run contracts:check` | Pass |
| `npm run typecheck` | Pass |
| `npm run build` | Pass |
| GitHub Actions on implementation commit `0f37b2a` | [Passed on Ubuntu/Python 3.11/Node 24](https://github.com/sohxmm/LapDNA/actions/runs/41938476921) |
| Local browser | Empty-data page renders; refresh works; API shutdown produces clear failure; retry restores the empty-data view after restart |
| Layout | Desktop and narrow/mobile layouts inspected; no horizontal overflow in measured DOM |

One non-fatal upstream Starlette warning recommends a future httpx2 transition for TestClient. No real FastF1 authentication, event retrieval, timing reconciliation, observation accuracy or exports have been verified. The optional data dependency set is declared but not installed/locked yet; T01 owns that work. The core lock was verified both locally on Windows/Python 3.11 and by the successful Linux CI run.

## Important decisions to preserve

- Offline computation, immutable artifacts and read-only delivery. No remote session download in a browser request.
- One frozen reference independent of A/B selection. Positive delta is B−A and favours A. Map colors show segment contributions, not cumulative delta.
- Raw elapsed-time curve only. Official timing is a separate check; constrained endpoints are not independent proof of accuracy.
- Brake is boolean. Native sampling limits evidence; a dense display grid is not new information.
- Up to three supported claims, with an explicit reason when fewer qualify. Published prose names actual drivers, so swapping display slots never changes its meaning.
- Each circuit initially has four eligible drivers and all six prepared pairs; at least 18 total for release. Availability depends on actual ingestion and validation.

## Next action: T01

Read `AGENTS.md`, `docs/00-blueprint.md`, then T01 in `docs/06-implementation-plan.md` and its named documents. Implement the pinned FastF1 adapter/importer and validate access to one candidate qualifying session. FastF1 3.9.2 source includes cache/authentication changes; inspect the installed public API and report actual access failures. Never substitute invented telemetry.

The implementation plan contains a copyable coding prompt, file targets, function boundaries, checks, completion gates and proposed commit subjects for every ticket. Treat the blueprint as fixed unless real evidence requires a documented adjustment.

## Known future work and boundaries

There is no CLI yet. Numerical processing, circuit geometry/markers, real eligibility, artifact promotion/review, charts/map synchronization, findings UI, export, production hosting and all real-data QA remain T01–T12. The current store discovers flat artifact JSON; T05 introduces an atomic catalogue manifest and must update the reader in the same change. Do not put a manifest into the current flat artifact directory.

The contract guide lists exact required metadata additions assigned to T01–T05. Wire validation currently checks structural/arithmetic integrity; the publication validator must additionally verify source-to-array correspondence, thresholds, eligibility, metric support and dataset review.

## Working practice

Use the README commands to run the app. Complete one bounded ticket, run its checks, update this handoff/status board, then commit and push with a descriptive ordinary message. Do not include tool/model attribution in commit messages or rewrite shared history. Keep raw caches, credentials and local QA outputs outside Git.
