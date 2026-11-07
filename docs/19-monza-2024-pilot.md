# Monza 2024 working pilot

Updated 8 November 2026. This is the first real telemetry dataset, with the shared editorial theme and persistent dark/light modes. The pilot covers **2024 Italian Grand Prix conventional qualifying**, round 16, OpenF1 session 9586. It does not establish imported telemetry for other races or years. See [year/field coverage](18-data-availability-by-year.md).

## Source decision and repeatability

The primary FastF1 archive metadata request required authentication and the tested mirror lacked that resource. The supported pilot therefore uses an explicit **OpenF1 + TracingInsights/FastF1 composite**, not an invented FastF1 download:

- Native timestamped car and position records, roster, lap durations/sectors, tyres, weather and race-control data come from OpenF1.
- Original timing clocks, phases and validity flags come from the identity-matched TracingInsights 2024 archive, pinned to commit `d1543a71370d9b617b627319f8ad80b2f85dfd5e`. Its original FastF1 library version is unknown and stays unknown.
- All 276 driver/lap identities were matched, and all available archive lap/sector durations agree with OpenF1. The preserved original flags must pass the published eligibility rules. Unknown Deleted is not treated as false.
- The original timing clock is used instead of OpenF1's approximate `date_start`. Over 174 timed non-out laps the latter differs by −1 to +609 ms (mean about 89.6 ms); those offsets are reported, never distributed into the curve.
- Eleven approximate circuit markers come from MultiViewer circuit 39 / 2024. Reference geometry retains OpenF1 source units, explicitly labelled; there is no assumed conversion into surveyed metres.
- Every source file has its URL, retrieval time and SHA-256. No merged/interpolated archive `*_tel` stream is called native car data. A second community archive is not independent official timing validation.

The reviewed immutable source snapshot is `work/monza2024/snapshots/20ffd525c5a06e19d51d41d5/snapshot.json`; its source digest is `d9993d260af7eeec9e272e268eb057dfe00628b7427f03951698da9545f093e2`. Raw source records are approximately 104.3 MB and remain ignored. The method is `distance-v3-openf1-native-composite`, pipeline `monza-pilot-1`, wire schema 1.3.0. Legacy 1.2.0 artifacts remain readable.

Run from the Desktop repository:

```powershell
.venv\Scripts\python scripts/import_telemetry.py --help
.venv\Scripts\python scripts/publish_telemetry.py --snapshot work/monza2024/snapshots/20ffd525c5a06e19d51d41d5/snapshot.json
.venv\Scripts\python scripts/validate_telemetry.py
```

Use the import command's help for the actual supported source/cache options. Cached source reruns made zero OpenF1 requests; publication and validation make no upstream requests. The importer is deliberately allowlisted to Monza 2024, not an unverified general archive importer.

## Actual coverage

| Item | Verified count or result |
| --- | --- |
| Event-specific drivers and teams | 20 |
| Actual lap records | 276: Q1 123, Q2 94, Q3 59 |
| Timing-eligible laps | 79: Q1 26, Q2 34, Q3 19 |
| Laps with normalized telemetry | 40 |
| Timing-eligible sector-only laps | 39 |
| Ineligible laps retained with reasons | 197 |
| Native car records | 348,120 |
| Position records | 364,780 |
| Weather records | 79 |
| Turn markers | 11 |
| Frozen reference | Norris Q3 source lap 11; integrated length about 5755.17 m |
| Normalized publication | About 2.67 MB plain / 985 KB compressed |

All drivers have at least one timing-eligible lap somewhere. A particular driver's phase can still be unavailable. Piastri Q1 has no eligible lap under the original validity/green-track gates; that is not a claim that he did not participate. Final phase-best comparisons remain available through R01.

Speed, throttle, gear and binary brake use the actual native fields. Invalid throttle sentinel 104, absent fields and unsupported intervals become null. RPM and historical DRS are retained in the raw import but are not additional core graph rows. Weather, pit/race-control and source timing records support eligibility/context; this pilot does not add a strategy or radio interface.

## Working behavior

1. Landing → current-year calendar → chosen race. Monza 2024 exposes Recorded timings and Lap telemetry. Other races retain their real R01 timing view.
2. The full Monza roster and actual Q1/Q2/Q3 lap selectors are available. Same-phase defaults are retained; independent phases require the visible opt-in. No run-number labels are inferred.
3. The default two drivers follow the source classification order and select each driver's fastest eligible same-phase lap. A telemetry failure does not silently substitute a slower lap.
4. When an eligible selected lap is sector-only and both drivers have an alternative with telemetry, **Compare fastest telemetry-supported laps** makes that change explicit. The selected lap/time and fastest timing-eligible value remain visible.
5. Supported pairs show speed, throttle, stepped gear, separate binary brake lanes and raw B−A delta on a shared distance axis. Turn/region, keyboard cursor and map inspection share state. Corner/straight and estimated 100 m layers stay separate.
6. The analysis reports supported low/medium/high classes, gross/net values, coverage, mixed/unknown regions and up to three distinct evidence-backed observations. There is no runtime LLM or causal attribution.
7. Recorded sectors and unadjusted timing residuals remain inspectable. A quality block produces independently eligible sector timing, not a repaired continuous curve. An explicit telemetry-only request fails when unsupported.
8. PNG cards, evidence JSON and exact selection links preserve actual phases/laps, source revision, orientation and warnings. Card appearance follows the current theme. The preference persists across reload/navigation; dark uses the blue palette and light uses the editorial off-white palette.

## Acceptance examples and external timing check

- Norris Q3 source lap 11: 1:19.327; sectors 26.492 / 26.579 / 26.256 s.
- Piastri Q3 source lap 15: 1:19.436; sectors 26.407 / 26.643 / 26.386 s. The recorded gap is +0.109 s. A genuine 1.119 s native speed gap blocks its telemetry tier.
- Piastri Q3 source lap 18: 1:19.661; sectors 26.439 / 26.796 / 26.426 s. It supports telemetry; its selected-lap gap against Norris is +0.334 s, not the phase-best gap.
- Russell Q3 source lap 17: 1:19.440, supporting telemetry; its gap against Norris is +0.113 s. The reviewed pair's maximum individual/pair interior residual is about 43.37 ms.

These timing triples were matched against the [FIA Monza qualifying sector analysis](https://www.fia.com/sites/default/files/2024_16_ita_f1_q0_timing_qualifyingsessionsectoranalysis_v01.pdf): Norris on page 1, Russell on page 7, Piastri on page 8. FIA report ordinals include an extra opening row; retain each provider's actual lap identity instead of pretending those ordinal numbers are identical. The report is linked for verification, not redistributed.

Source integrity review checked all 70 source-file hashes and phase identities. The real comparison matrix checks 321 phase-best pairs plus their reversals: 84 telemetry results with three supported observations, 237 sector-only results. This is a pipeline regression matrix, not a claim of precise corner ground truth. Local cold calculations measured median about 0.5 ms and maximum about 23 ms; hosted timings remain separate.

## Publication and remaining boundaries

The compact generated pilot lives in ignored `services/api/src/lapdna/pilot_data/`, with a digest manifest, full roster index, compressed normalized arrays and operator report. Vercel bundles this one compact reviewed publication; raw telemetry, source caches and numerical import dependencies remain excluded. It is generated before deployment and deliberately not committed to Git.

Requests calculate only from the frozen local normalized inputs. Two concurrent builders, duplicate-request sharing, a bounded disposable memory cache, strict file/array limits and content-derived IDs bound work. Exact results can regenerate across a cold process while this immutable publication is retained. A changed dataset revision must never silently replace a linked selection. Long-term multi-revision retention and bulk 2018–2026 object storage remain future archive work; the single-pilot bundle is not that storage system.

Attribution travels with the comparison/evidence. OpenF1's current project licence is [CC BY-NC-SA 4.0](https://github.com/br-g/openf1/blob/main/LICENSE). The pinned TracingInsights archive carries [MIT terms](https://github.com/TracingInsights/2024/blob/d1543a71370d9b617b627319f8ad80b2f85dfd5e/LICENSE); underlying source rights remain distinct. MultiViewer annotation redistribution terms have not been independently verified. Do not describe the combined inputs as unrestricted or relicense the upstream data as LapDNA software.

Other circuits/years, a direct FastF1 account adapter, optional RPM/DRS plots, independently reviewed additional layout profiles, persistent multi-revision archive hosting and LLM rewriting are not completed by this pilot. Brake pressure, steering angle and true official mini-sector durations remain unavailable.
