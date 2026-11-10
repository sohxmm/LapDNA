# Current handoff

2026 correction: the 166-session release had no usable 2026 distance graphs;
Mexico was its only 2026 publication and remained timing-only. The queue now
prioritizes 2026. [The correction checkpoint](22-2026-telemetry-checkpoint.md)
records actual local graph examples and the explicit telemetry-lap discovery
controls. Use the latest hosted receipt in docs/21 for deployed counts.

10 November repair checkpoint: source collection now follows the pinned FastF1 primary/mirror fallback with actual resource URLs/hashes and explicit mirror provenance; 2022 Bahrain's previously blocked native import succeeds. 2023 SQ uses provider identifier SS, restoring actual Sprint Shootout loading. Missing optional weather stays unknown; missing layout annotations allow timing-only publication (Sakhir 2020 now retains 145 eligible timing laps). Metadata-load failures no longer escape the per-session error handling. No numerical or validity gate was relaxed. The release workflow supports `complete_archive.py --publish-current` so audited ready sessions do not wait behind unfinished archive acquisition. Audited active publications supersede stale failed-attempt reports, and unattempted past-session candidates remain explicitly incomplete.

This checkpoint documents the first 63-session native release. [The latest audited archive receipt](21-archive-coverage.md) and machine-readable coverage ledger take precedence for subsequent import/deployment counts. `complete_archive.py` now runs the resumable import-to-audit-to-deployment workflow and stops on sign-in/source-review requirements; it never deploys changed unreviewed source.

Updated 10 November 2026. The deployed product contains a 63-session audited native batch. The remaining qualifying/Sprint Qualifying archive is actively importing; never describe the entire 2018–2026 programme as complete. [Hosting](12-hosting.md) identifies the live source/data release; [coverage](../config/telemetry-coverage.json) is the audited ledger, not a list of source candidates.

## Workspace and authorization

Use `C:/Users/soham/OneDrive/Desktop/LapDNA`, remote `https://github.com/sohxmm/LapDNA.git`, main branch. The Documents checkout is an older copy. The user authorized implementing all remaining verified 2018–2026 qualifying/SQ sessions, repairing blockers, committing/pushing small completed features and deploying the Vercel preview. Keep the repository private, do not commit/download/upload credentials or raw source caches, and never invent missing channels or timing. Existing sign-in was completed locally by the user.

## Current implementation

Sports-editorial landing → current-year calendar → actual race/session → independent actual Q/SQ phases and drivers/laps. React/TypeScript/Vite and one ECharts stacked chart render Python-authored facts. Source team colours are event-specific; A solid/B dashed. Teammates retain the same hue with dashed/hatching distinctions; missing colours are neutral. Contrasting under-strokes keep pale colours visible without changing their hue. Dark/light preference persists.

Python owns native masks, eligibility, fixed reference, integrated-speed distance, alignment, raw B−A delta, reconciliation, approximate regions, class totals and evidence. Positive B−A favours A. The comparison always identifies the exact selected source laps. Defaults use the fastest eligible timing pair in the highest shared phase; any switch to slower telemetry-supported laps is explicit. Cross-phase selection needs opt-in and permanent context.

Outputs include synchronized supported speed/throttle/gear/binary-brake/delta, numbered turns, linked approximate map, estimated 100 m bins, ranked differences, low/medium/high class evidence and up to three supported observations. Missing channels remain missing. Timing-only output has recorded sector crossing points/table and no spatial arrays or inferred local claims. PNG cards, evidence JSON and exact comparison URLs preserve source/method/orientation/context. No synthetic route, fake production fixture or runtime LLM is shipped.

Contracts: native comparison/inventory 1.4.0; legacy Q 1.2/1.3 accepted. Q and SQ phase prefixes must agree with actual format; SQ uses actual 2023-onward sessions. Calendar/classification contracts remain 1.0.0. Current methods `distance-v5-fastf1-native` and `distance-v5-openf1-native-composite`, pipeline `native-sessions-4`. Regenerate Pydantic-owned contracts rather than hand editing generated output.

## Sources and verified batch

The pinned FastF1 3.9.2 operator adapter decodes original compressed car/position messages before library filling. Actual timing clocks/phases/accuracy flags retain library version and source hashes. Missing brake/gear/throttle/DRS fields are not replaced with zero. Source DriverList supplies actual names, team and colours. The explicit OpenF1 native + pinned TracingInsights timing composite remains independently labelled for retained publications. Source snapshot bytes and authentication stay private and ignored.

The audited batch contains all 21 Q rounds in both 2018 and 2019; 17 Q/three SQ in 2024; and Mexico 2026 timing-only Q. It passed all 19,010 phase-best pairs plus reverse checks, with 12,317 telemetry and 6,693 timing-only results. Individual arbitrary lap pairs remain checked when requested. The three original circuits were validation pilots, not permanent coverage limits. Recorded classifications retain 1,168 Q and 24 actual SQ sessions across the broader historical years in the current R01 snapshot.

2018 France/Hungary were recovered by accepting source-known wet conditions without changing native/residual gates. Germany 2019 contained an early stale multi-series sample: actual lap-envelope clipping retains five seconds of interpolation padding and records excluded counts. All actual timing identities must match the roster. Unassigned streams without lap identities are quarantined/countable, never reassigned; this recovered Australia 2024's actual 19-driver roster. Monaco 2019 exceeded the former 256 eligible-lap resource limit; the bound is now 512 while the 5,000-point and 20 MiB limits remain. Known wet tyres and real rain context are supported; unknown rainfall never becomes dry grip. Deleted, generated, inaccurate, pit, unknown-status and inconsistent-timing gates are preserved.

Monza has the authored disjoint `monza-v1` profile. Other layouts use fixed ±120 m ordered source-turn vicinities; overlaps merge into complexes, complements are straights. They are approximate analysis zones, not measured physical corner boundaries. Mixed/unknown complexes and sparse classes remain explicit. No causal driver/car inference is supported.

## Import and release operations

Install operator dependencies from `services/api/requirements-data.lock` in the local `.venv` only. `scripts/import_archive.py` resumes per-session results in `work/fastf1/archive-report.json` and covers past calendar Q plus actual R01 SQ candidates. Both the library limiter and persistent stricter project ledger stay enabled. A rate response waits for its window; access expiry/revocation stops without a password prompt. Renew sign-in locally only if needed. The request ledger contains timestamps only; never print tokens or cached HTTP headers.

`scripts/rebuild_publications.py` normalizes retained complete snapshots offline. `scripts/audit_publications.py` checks activated identities/digests and phase-best pairs. Failed candidates preserve earlier usable sources. Current `pilot_data` is generated and ignored, with content-addressed normalized blobs, per-session manifests and a small atomic root catalogue. Do not mutate production mounts during requests.

`scripts/prepare_release.py` requires clean committed source and freezes only referenced active data. `scripts/publish_release_blobs.py` reads ignored operator credentials, uploads content-addressed normalized files, independently verifies downloaded hashes, then offloads only those exact frozen files. The reader accepts only the configured public Blob HTTPS origin, checks hashes/size and refuses cross-origin redirects. This is an immutable normalized-artifact fetch, never live upstream telemetry acquisition. Cache bounds: eight compressed, three decoded publications, 48 results, two builders. No credentials/raw caches enter the deployment.

Deploy from the frozen release directory with the pinned Vercel CLI; Git pushes alone do not deploy. `scripts/verify_deployment.py` checks live identities, team colours, canonical reverse results, exact result GETs, Mexico timing facts and Australia's roster. The presently deployed commit is `071f0d75`, deployment `dpl_9Gn8YBXj8QYwQDdgyQFjvCuh9boX`, 63 publications. Ongoing local imports are a separate, later batch until audited/deployed.

## Checks and acceptance

210 Python tests pass, one Windows symlink skip; 30 client tests pass; contracts, typecheck and production build pass. Existing lazy ECharts size advisory is non-fatal. Live API checks cover Monza 2024/2018, Germany/Monaco 2019, Miami 2024 SQ and Mexico 2026. Local visual checks cover Q↔SQ, Back, real white STR/SIR Monza lines in light mode, 390×844 with no horizontal page overflow, keyboard distance cursor and PNG export. Finish/record hosted visual evidence before the final user handoff.

Preserve Mexico HAM/LEC +0.119 s, Q2 reversal by 0.009 s and LAW DSQ in recorded classifications. Native Mexico has no eligible reference because of source speed gaps; show timing only. Monza 2024 source NOR 1:19.327 / PIA 1:19.436 stays a timing comparison when PIA's native gap fails; the explicit telemetry alternative must disclose its slower selected lap. Published source ordinals differ across providers: official timing checks match actual driver, phase, lap duration and sector triple.

## Next work and limits

Continue the source-limited archive job, inspect each real failure and fix the smallest proven cause. Re-audit/freeze/release newly completed batches; do not claim absent data was imported or force numerical gates to obtain graphs. Detailed 2020–2023, 2025, other completed 2026 and remaining 2024 Q/SQ sessions are not in the current deployed batch. Future sessions are unavailable until actual source publication. T11 remains open for the complete archive; T12 retains cross-method durable historical result storage beyond the presently retained source/method. Current exact links regenerate only with their retained publication/method.

Optional RPM/DRS graph rows, inferred Run 1/Run 2 labels, clustering and runtime LLM rewriting remain deferred. Actual source lap numbers can already be selected. Steering angle/brake pressure are unavailable; brake is on/off only. Never derive control inputs from speed, force a curve to sector timings or fill unknowns with zero.
