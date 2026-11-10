# Hosted application

Updated 10 November 2026. [LapDNA](https://lapdna.vercel.app) serves the audited
217-session past 2018–2026 Q/actual SQ archive with recorded classifications,
source-coloured telemetry where supported and persistent dark/light themes.
No synthetic preview or fabricated fallback data is shipped.

## Exact release

- Application source: `5e117098727475a20394359f6a7a8d0adf8316a8`.
- Deployment: `dpl_DW72dC1W4D9bEgCvNYJpLNLUGU8R`.
- Frozen release: `work/releases/5e117098-20261110T111308Z`.
- Native catalogue SHA-256: `a6dd7043ee2ba38f46fcdf54e06f3f291afc27dce4b5ba1dcb6b099aa64c47d9`.
- Native audit base: `fb91de2468e1fb4d3f1fb8668dbca20994990269`.
- Recorded source: checksum-verified F1DB v2026.20.0, including Brazil 2026.

All runtime Python, frontend source, contracts, native manifests and native
catalogue match the 217-session audit exactly. The classification refresh keeps
all 1,192 prior session driver facts and adds Brazil's 22-driver qualifying.
`audit-reuse.json`, `hosted-checks.json` and `recorded-hosted-checks.json` in the
private release directory record reuse and actual hosted checks. [Coverage](21-archive-coverage.md)
distinguishes imports from usable graph choices; [field/year guide](18-data-availability-by-year.md)
defines measurements and derived outputs.

## Storage and verification

Vercel serves React/Vite and FastAPI. Small indices/manifests/classifications are
bundled; normalized telemetry uses hash-addressed public Blob objects. The API
validates origin, size and digest before use. No upstream credentials or raw
caches enter the deployment. Acquisition runs offline, never inside a web
comparison request. Three decoded sessions, 48 results, eight compressed blobs
and two builders bound runtime caches/work. Pushes alone do not deploy.

The audit checks 70,382 phase-best pairs plus reversals, with 26,751 telemetry
and 43,631 timing-only results, and 464 explicit discovery choices. Hosted
checks cover inventory, selected real comparisons, exact links, swaps, colours,
Australia's source roster and Brazil/Mexico recorded facts. A first cold check
timed out; its retry passed. Cold/network loading can be slow, and receipts
retain observed request durations. The chart-library size warning is advisory.

Local browser checks cover 390 × 844 light mode, keyboard graph selection and
result focus, no horizontal page overflow and source colours. Live China 2026
proof is retained at `work/qa/2026-11-10-live-china-2026-graphs.png`.

## Current limits

All 26 past 2026 Q/SQ sessions are imported, but only 12 have verified displayed
graph choices. Selected laps still pass pairwise checks; many timing bests,
including Mexico, fail continuous alignment. The UI offers explicit supported
laps and otherwise shows recorded sectors. These gates were not relaxed.

Public telemetry supports approximate analysis, not driving causation or
surveyed corner boundaries. Brake is binary; steering angle/brake pressure are
unavailable. RPM/DRS plots, inferred run labels, clustering and runtime LLM
wording are deferred. Current-method exact links work; durable cross-method
history is still open. Future qualifying data is not invented in advance.
