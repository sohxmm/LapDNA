# Native archive completion

The first 63-session batch is [deployed and verified](12-hosting.md). The remaining past-session 2018–2026 qualifying/Sprint Qualifying candidates are queued in the primary importer, with source limits respected. This file will be replaced by the next frozen batch's actual audited coverage, unresolved source failures and confirmed deployment receipt.

Run `.venv\Scripts\python -u scripts/complete_archive.py` from the Desktop project folder to resume the complete workflow: acquisition, one bounded retry pass, checks, frozen-data audit, metadata commit/push, verified Blob upload, deployment and hosted checks. It stops if local sign-in needs renewal or reviewed source changes during acquisition. No raw caches or credentials are committed or uploaded. Status is retained privately in `work/archive-release-state.json`; per-session attempts are in `work/fastf1/archive-report.json`.

Current audited data remains [the coverage ledger](../config/telemetry-coverage.json). A finished import is not a deployed release until the final hosted checks pass. Source/unavailable laps remain explicit; the process never relaxes numerical gates or fabricates channels to make a session appear complete.
