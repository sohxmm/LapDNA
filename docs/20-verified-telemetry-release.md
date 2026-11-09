# Verified telemetry expansion and prefinal release

Decision update, 9 November 2026. This supersedes earlier instructions to preserve the synthetic preview, restrict publication to Monza, or assign cyan/orange to A/B. The requested telemetry range remains **2018–2026**, with timing comparisons before 2018. A provider's advertised date range is not a verified session inventory.

## Product changes

- No synthetic dataset, demo component, fixture generator, demo route, illustrative telemetry or fabricated circuit is shipped. The landing outline is a small excerpt of Monza's actual reference position geometry. Automated analytical test fixtures remain isolated from the shipped application.
- Actual event-roster `team_colour` is retained in lap metadata and the inventory. Traces and PNG cards use that exact colour. A is solid and B dashed; teammates keep the same colour. Teammate gains use solid/dashed map strokes and a hatched B minisector strip. Missing source colours use neutral styling, never a current-team guess. Driver names stay readable in both themes.
- Year → sourced race calendar → studio remains the entry flow. Detailed lap selection appears only for a published inventory. A genuine source/quality failure never triggers a synthetic fallback or a silent change to another lap.
- Multiple sessions have independent digest-checked manifests and normalized publications. The root catalogue activates complete per-session revisions. Normalized streams and manifests have content-derived filenames; old files are not overwritten. The process retains at most three decoded sessions and 48 comparisons. Result IDs include a session tag, so immutable lookup does not load the whole archive or search every session's pairs.

## Source coverage and access

| Years | Recorded results | Native detailed-data route | Actual limitation |
| --- | --- | --- | --- |
| Before 2018 | Existing historical timing tier | Outside requested detailed range | No distance curves or corner attribution |
| 2018–2022 | Existing timing tier | FastF1 documents timing/car/position coverage | Tested 2018 primary session metadata returns HTTP 401; the tested mirror native resource returns 404. The authenticated raw-presence adapter is now implemented and Monza 2018 has passed real import/validation; other sessions still require individual verification. |
| 2023–2026 | Existing qualifying and actual SQ classifications | Native OpenF1 car/location + identity-matched pinned TracingInsights clocks/flags | Source/session identity, fields, dry eligibility, geometry, native gaps and raw timing residuals must pass separately |

FastF1 3.9.2 documents detailed coverage from 2018 and its current client supports Formula 1 account authentication. Never request passwords in chat or store credentials in this repository. [Data reference](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/docs/data_reference/index.rst), [authenticated transport](https://github.com/theOehrly/Fast-F1/blob/v3.9.2/fastf1/internals/f1account/transport.py). OpenF1 documents historical access from 2023 and a free limit of 30 requests/minute. [OpenF1](https://openf1.org/).

`config/telemetry-sessions.json` contains **import candidates**, not enabled features. Discovery matched source session/meeting keys against pinned archive metadata and event calendar identity; this includes delayed qualifying dates rather than requiring a scheduled date to equal the actual date. It currently resolves 87 conventional-Q candidates across 2023–2026. Six unresolved 2026 entries remain absent. Native SQ is not implemented by this conventional-Q adapter.

## Primary FastF1 route for 2018 onward

`scripts/import_fastf1.py --year 2018 --round 14 --publish` uses pinned FastF1 3.9.2, a locally stored account token and the library’s supported authenticated transport. It never starts sign-in implicitly or writes credentials/authorization headers to an export. Use `.venv\Scripts\python -m fastf1 auth f1tv --authenticate` in your own terminal when access is required. A completed primary snapshot can be reused offline without sign-in; `--refresh` is deliberate. `--all` processes completed calendar candidates and stops on authentication/rate-window failures while retaining progress.

Raw `CarData.z.jsonStream` and `Position.z.jsonStream` are decoded as bounded JSON/base64/deflate messages. Absent raw channels stay absent, invalid/sentinel values stay available to downstream masks, absent DRS never becomes measured off, and missing coordinates/status never become an origin point or off-track state. No remote executable/pickle archive is decoded. The library’s current version supplies timing clocks, Q-phase splits and validity checks, with its exact version retained. Car/position DataFrames that the library may fill are never analytical inputs. Original source weather field presence is retained; uncertain/wet context does not become assumed dry. Before 2020, geometry remains in its actual year-specific source frame and must match that year’s annotations.

Primary publications use `distance-v4-fastf1-native`; composite publications retain `distance-v4-openf1-native-composite`. Their components, channel names, quality descriptions and method IDs remain distinct. Monza 2018 has 20 source drivers, 284 actual records, 76 telemetry-capable laps, one sector-only eligible lap and 207 excluded records. All 271 fastest eligible same-phase pairs and reversals passed with telemetry and three supported observations. RAI Q3 source lap 19 is 1:19.119; VET Q3 source lap 18 is 1:19.280, gap +0.161 s. Both retain their source Ferrari colour `#DC0000`, with solid/dashed distinctions. The selected Q3 lap values were also matched to the [published F1 classification](https://www.formula1.com/en/results/2018/races/992/italian/qualifying), and their sector triples match the [FIA best-sector report](https://www.fia.com/file/72377/download?token=v_jkOHSG). A best-sector report does not generally identify every lap. These are timing/clock/numerical checks, not independent physical ground truth. Broader 2018 import is underway; no year-wide availability is inferred from Monza.

## Approximate circuit profiles

Method `distance-v4-openf1-native-composite`, pipeline `native-composite-2` retains the raw B−A curve, fixed independent reference, 5 m display grid, native masks, discrete brake/gear, original timing residuals and existing pass/warn/block thresholds. It does not repair a curve to fit sectors.

Monza retains the authored `monza-v1` disjoint corner/straight profile. Other layouts use **`marker-windows-v1`**, an explicitly approximate analysis partition: ±120 m around each ordered projected source turn marker, clipped to lap edges; overlapping windows merge into complexes; the complement forms straights. Bounds are frozen on the reference and never follow the selected A/B laps. All members of a merged complex retain their turn labels. Mixed/unknown native speed classes remain outside class totals. Boundary sensitivity and sample-support gates still govern every observation. These are turn vicinities, not measured physical entry/apex/exit boundaries; the UI, artifact provenance and class limitations disclose this. This is the smallest generic extension that avoids copying Monza's named physical regions to unrelated circuits.

Projection requires complete source annotations in order and agreement with the actual reference position frame. Native position units remain explicit source units. Suzuka's crossing uses ordered marker projection and region-constrained picking. This does not establish a surveyed racing line.

## Reproducible operator workflow

From the Desktop repository, with the API dependencies and editable package installed:

```powershell
.venv\Scripts\python scripts/discover_telemetry.py
.venv\Scripts\python scripts/import_telemetry.py --year 2024 --round 4 --publish
.venv\Scripts\python scripts/import_telemetry.py --year 2024 --all --publish --bulk
.venv\Scripts\python scripts/validate_telemetry.py --session 2024-4-suzuka-Q --output work/suzuka2024/validation-report.json
```

Discovery downloads only small identity/annotation metadata. Imports preserve raw source files and hashes outside Git. Native whole-session requests can be rejected as too large, so bulk acquisition uses bounded UTC windows, overlapping source requests and a local half-open partition without resampling or boundary duplication. Every returned row is checked against its requested source/session/time interval and roster. Requests respect the free historical rate limit. Hash-valid complete snapshots and partial source caches are reused; `--refresh` is explicit. Every failed session retains its reason in an ignored import report and leaves its previous usable publication in place. A candidate without a usable reference is not activated.

Generated normalized publications remain ignored and must be prepared before deployment; a clean checkout can still serve recorded timings without them. Vercel bundles compact normalized publications, not raw acquisition files or authentication. An import runs offline as an operator job, never in a comparison request.

## Verification and current release gate

The first checked increment has three local real inventories:

| 2024 event | Drivers | Actual lap records | Telemetry-capable laps | Sector-only eligible laps | Fastest same-phase pair checks |
| --- | ---: | ---: | ---: | ---: | --- |
| Monza | 20 | 276 | 40 | 39 | 321 pairs: 84 telemetry, 237 sectors |
| Suzuka | 20 | 223 | 18 | 55 | 340 pairs: 16 telemetry, 324 sectors |
| Silverstone | 20 | 368 | 11 | 94 | 228 pairs: all sectors; faster eligible laps are not silently replaced |

Each pair was checked in both orientations. Supported telemetry results have three evidence-backed observations; sparse results must show fewer. Cold numerical builds remain local and bounded. A lap being individually telemetry-capable does not guarantee that its pair passes reconciliation. The wider 2024 batch is underway; its completed, checked publication counts must replace this initial table before claiming a broader release. None of the remaining candidates is implied by these three inventories.

Local visual checks cover real Monza traces in dark desktop and light 390 px phone layouts, with exact McLaren orange and Mercedes turquoise and no horizontal page overflow. Final hosted verification, selected-lap exports, other-circuit visual review and clean release checks remain required. Previous v3 comparison IDs are not silently translated to v4; users must deliberately compare again to obtain the new method identity. Durable cross-method result retention remains open under T12.
