# Local operation, data preparation and release

## Current setup

The repository targets Node 24 and Python 3.11. The root README gives exact install/start commands. No system-wide dependency installation is needed. The root `.venv`, npm dependencies, caches, logs and telemetry data are ignored.

`npm run dev` starts the client on `127.0.0.1:5173` and proxies `/api` to `127.0.0.1:8000`. Run Uvicorn separately with the root virtual environment. Stop either foreground server with Ctrl+C. When not running, the browser URL will be unavailable; that is normal for this local scaffold.

The API's default artifact directory is `<repository>/data/artifacts`. Set `LAPDNA_ARTIFACT_DIR` to an absolute directory to override it. Relative overrides resolve against the API process working directory. `LAPDNA_CORS_ORIGINS` is a comma-separated explicit allowlist; defaults cover localhost and 127.0.0.1 on port 5173. `.env.example` is documentation only; the scaffold does not auto-load `.env`.

Do not activate a global Python environment or copy credentials into the example file. In PowerShell an optional explicit override is:

```powershell
$env:LAPDNA_ARTIFACT_DIR = (Resolve-Path ./data/artifacts).Path
.venv\Scripts\python -m uvicorn lapdna.main:app --host 127.0.0.1 --port 8000
```

## Planned operator commands

The following interface is assigned to T01–T05 and **does not exist in the scaffold**:

```text
python -m lapdna.cli import-session --circuit monza --year 2024 --event "Italian Grand Prix" --session Q
python -m lapdna.cli list-laps --snapshot <manifest-path> --phase Q3 --output <report-path>
python -m lapdna.cli build-reference --snapshot <manifest-path> --profile <profile-path>
python -m lapdna.cli build-comparison --snapshot <manifest-path> --profile <profile-path> --lap-a <id> --lap-b <id>
python -m lapdna.cli validate --artifact <path> --review <review-path>
python -m lapdna.cli publish --artifacts <validated-directory> --review <review-path>
```

Use argparse for a small command tree; do not add a CLI framework by default. Each command emits a compact summary and JSON report path, exits 0 on success and nonzero on unsupported/unavailable/invalid input. `--help` must identify required inputs and local-only side effects. Parameterize output directories; never delete an entire data directory on an import failure.

`import-session` obtains source data; `build-reference` fixes the common geometry; `build-comparison` computes without publishing; `validate` checks a candidate; `publish` promotes only reviewed eligible outputs. These separation points make a later automation possible without hiding quality checks. Rate-limit source access, reuse supported caches and retry only transient errors with bounded backoff (three attempts, approximately 2/4/8 s plus small jitter). Do not retry authentication errors or corrupted inputs indefinitely.

## Preparing the next qualifying analysis

1. Confirm the event has completed and the supported source can load all required channels, timing, phases and validity flags. Check the pinned release's authentication requirements through its supported flow; never log credentials.
2. Import an immutable session snapshot and inspect its inventory and source manifest.
3. Review eligibility and select one common phase and four drivers. Record actual lap IDs and context; do not assume a driver's absolute fastest session lap is comparable.
4. Confirm circuit layout/config compatibility; create a new reference revision for a new session rather than silently reusing another event's distances.
5. Generate all intended pairs, run reconciliation and evidence checks, and review top observations and geometry. Investigate failures without hiding them.
6. Record official source links and external verification scope. Review every warning before promotion.
7. Publish the validated immutable artifacts with one atomic catalogue switch. Keep previous revision for rollback.
8. Open representative comparisons, inspect PNG/JSON exports, then release the served artifact set. Publication of a social post is not automated by the MVP.

## Failure and recovery rules

| Failure | Required behavior |
| --- | --- |
| Authentication/access unavailable | Show actual source failure; preserve old published data; no password in code/logs |
| Data incomplete shortly after session | Do not publish partial analysis; retry later explicitly with a new snapshot |
| Remote schema/API changes | Stop importer, record installed version and failing field, update adapter/test deliberately |
| Timing/geometry guardrail failure | Keep rejection report; withhold local claims; inspect clocks/reference/coverage |
| Corrupt published file | API fails clearly; restore the prior checked artifact/manifest and investigate source of corruption |
| Missing comparison | 404 with prepared-data explanation; no on-demand remote import |
| New pipeline version | Rebuild into new IDs/revisions; old immutable URLs keep their existing meaning |
| Failed publication | Old catalogue remains active; remove only the known temporary file after inspecting it |

Logs should include comparison/session IDs, phase, pipeline version, counts, runtime and safe reason codes. Exclude source credentials, private cache contents and authentication headers. Browser errors should explain recovery without revealing local filesystem paths.

## Production target for T12

Use a Linux runtime with the pinned Python environment, the Vite production bundle, and read-only prepared artifacts. Serve the browser and `/api` from the same origin. Allow only GET to the public API. Keep import commands separate from the web process. Add immutable caching for content-addressed comparisons, revalidation for catalogue, response compression and health checks. Avoid caching transient errors as successful content.

No container/provider has been configured or deployed in T00. Create and test the image only after the data pipeline and routes are stable. Production environment must specify the artifact mount; the source-relative development default is not a deployment-storage strategy. Keep source credentials out of runtime images and frontend environment variables. If upstream access is unnecessary for serving prepared artifacts, do not provide those credentials to the web service at all.

## Git workflow

The requested destination is `https://github.com/sohxmm/LapDNA.git`; the empty repository is initialized on `main`. Use the current configured user identity. Commit and push each small completed feature after relevant checks; commit subjects describe changes without tool/model attribution. Do not force push or rewrite shared history. When a later task explicitly needs isolation, use a `codex/` feature branch and keep each checked feature separately committed.

Before committing, inspect staged filenames and diff statistics. Exclude `.venv`, node_modules, data caches, credentials, exports generated for local QA and machine-specific paths. Documentation must describe current reality and the next step. Before pushing, check the remote/branch and avoid unrelated changes.

## Decision and handoff discipline

After each ticket update its status and `docs/10-handoff.md`: completed behavior, exact verification commands/results, any actual blockers, remaining limitations and the next ticket. An upstream assumption that fails needs a documented decision update, not a silent workaround. Keep planning documents coherent when changing method, schema, source version or scope.
