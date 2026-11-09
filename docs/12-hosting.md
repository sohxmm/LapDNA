# Hosted preview

Updated 10 November 2026. [LapDNA](https://lapdna.vercel.app) serves the audited 63-session native batch with the shared editorial landing, blue dark/off-white light themes, event-specific team colours and no synthetic preview or fabricated fallback data.

## Deployed release

- Source commit: `071f0d75fa3c9d43894af12672282e693c262159`.
- Deployment: `dpl_9Gn8YBXj8QYwQDdgyQFjvCuh9boX`.
- Frozen release: `work/releases/071f0d75-20261109T195342Z`.
- Catalogue SHA-256: `cda8a8aa1a88d0100e11cbabfc930b9f6a5951d6ead44334942cf46f6067411d`.
- Audited publications: 21 Q sessions in 2018, 21 Q in 2019, 17 Q/three SQ in 2024, and timing-only Mexico 2026 Q.
- [Coverage ledger](../config/telemetry-coverage.json): 19,010 phase-best pairs plus reversals; 12,317 telemetry and 6,693 timing-only results. Every publication, source identity and inventory is digest-checked. This is not the Cartesian product of every actual lap.

The remaining 2018–2026 archive import is still in progress. The deployed batch does not automatically grow when local imports finish. Future sessions and absent source measurements are never invented. [Year/field coverage](18-data-availability-by-year.md) gives the exact scope.

## Hosting and storage

Vercel serves the React/Vite frontend and FastAPI comparison service. Small indices, manifests and recorded classifications are bundled. The 63 normalized publications (about 108 MB including indices/reports before offloading) have content-addressed public Vercel Blob objects; each upload was independently downloaded and SHA-256 checked. Runtime downloads only an immutable normalized artifact, verifies its pinned hash and size, then performs bounded calculations. No upstream telemetry parse or account login occurs on requests.

Source caches, raw telemetry, optional FastF1/numerical import dependencies and all operator credentials remain outside Git and deployment. The private GitHub repository remains private. The production Blob write credential stays server-side and is not required by the public artifact reader or frontend.

Frozen source/data prevent imports from changing an in-progress deployment. Failed imports preserve the prior active publication. The runtime retains at most eight compressed files, three decoded publications and 48 comparison results per process, with two concurrent builds. Verified source gaps, incomplete flags and numerical failures reduce capability instead of forcing a curve to match timing.

## Verification

The deployed API was checked for Monza 2024 NOR/RUS, Monza 2018 RAI/VET, Germany 2019 HAM/VER, Monaco 2019 HAM/BOT, Miami 2024 SQ3 VER/LEC and Mexico 2026 HAM/LEC. All returned source-matching lap IDs/times/colours, reversed selections retained canonical artifacts, and immutable GETs reproduced the results. Australia 2024 exposes 19 actual source drivers without fabricating an entry for the unassigned stream. First comparison requests in this check took roughly 0.5–4.1 seconds, including transport and cold artifact access; this is a small acceptance sample, not a latency guarantee. Monaco's selected phase-best pair correctly returned timing-only output.

Mexico HAM Q3 source lap 19 is 1:16.514; LEC source lap 23 is 1:16.633, recorded gap +0.119 s. Native speed gaps block the distance reference, so no continuous curve, map or corner claim is shown. Local browser checks confirmed Q/SQ switching, Back restoration, the real SQ3 comparison, the Mexico fallback, themed PNG export and white Williams traces on a light background. Mobile 390×844 has no page-level horizontal overflow and the keyboard distance cursor works. Final hosted visual evidence is recorded with the release handoff.

Checks: 210 Python tests passed, one Windows symlink test skipped; 30 client tests passed; generated contracts, typecheck and production build passed. The lazy ECharts chunk has an existing non-fatal size advisory.

## Current limits

Detailed 2020–2023, 2025 and other completed 2026 imports, plus the remaining 2024 Q/SQ sessions, are pending. The native importer respects both the library's limit and a persistent project request budget, waiting for the source window instead of resetting clients to bypass it. Authentication expiry stops with a local sign-in instruction.

Corner/straight zones outside the authored Monza profile are approximate fixed marker-vicinity windows, not measured entry/apex/exit boundaries. Brake is binary on/off; steering angle and brake pressure are unavailable. Optional RPM/DRS plots, inferred run labels and runtime LLM wording are not implemented. Exact links preserve the current method/source identity; arbitrary cross-method historical retention is still open. Public source access and software licences do not independently settle all underlying data redistribution rights.
