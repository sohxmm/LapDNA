# V5 telemetry gate attribution — Step 0

Measurement only. No runtime, selection, alignment, contract or observation gate was changed.

Audit version `v5-gate-attribution-1`. Baseline source `0339baf194d2642a300ff53a3bea7de23c71c542`; active catalogue `a6dd7043ee2ba38f46fcdf54e06f3f291afc27dce4b5ba1dcb6b099aa64c47d9`.
Sessions: **217**. Full per-lap derived ledger: `config/gate-attribution-laps.jsonl.gz` (SHA-256 `3c8447b40cd9e34ffc147437a377e9c4ba4ff73f663c1991ee6cfd2b0106ae5f`).

## Cohorts and interpretation

Timing-eligible means the existing v5 source/timing selection, not a new denominator. All indexed known-phase laps are also audited, including excluded laps. Unknown-phase raw laps are outside the published lap index.
First failure follows the existing eligibility → native preparation → frozen-reference → individual-publication gate order. The publication's final combined condition orders interior residual, scale, sector sum, then sliced duration. Pair gates are contextual and are reported separately; a failed peer comparison does not make a lap intrinsically bad.
All-failure counts include diagnostic continuation using unchanged v5 equations on actual native gap endpoints where a frozen reference exists. This does not accept a gap, insert samples, implement v6 bridging, fit time to sectors, or establish independent validation. If prerequisites/reference are absent, downstream gates are explicitly not evaluated. Counts overlap; they must not be added as disjoint failures.
Missing throttle/gear/brake/RPM is channel availability, not an existing whole-lap graph gate. Only the required speed stream can prevent alignment. No new missing-optional-channel rejection is invented for this audit.

## Per-year baseline and native edge coverage

| Year | Indexed laps | Timing eligible | V5 telemetry | Telemetry % | Car brackets both edges | Bracket % | No in-lap car samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 6054 | 1733 | 1525 | 88.00 | 1733 | 100.00 | 0 |
| 2019 | 6084 | 2397 | 2093 | 87.32 | 2397 | 100.00 | 0 |
| 2020 | 5215 | 2023 | 1697 | 83.89 | 2023 | 100.00 | 0 |
| 2021 | 6887 | 2747 | 2509 | 91.34 | 2747 | 100.00 | 0 |
| 2022 | 6985 | 2865 | 666 | 23.25 | 2859 | 99.79 | 0 |
| 2023 | 8869 | 3594 | 803 | 22.34 | 3588 | 99.83 | 0 |
| 2024 | 8943 | 3446 | 950 | 27.57 | 3440 | 99.83 | 0 |
| 2025 | 8825 | 3109 | 120 | 3.86 | 3100 | 99.71 | 0 |
| 2026 | 8263 | 3357 | 68 | 2.03 | 3345 | 99.64 | 0 |

Car-edge coverage is an input feasibility measurement, not a Tier 0 coverage claim; no tier has been implemented.

## First failing lap gate — timing-eligible laps

| Year | interior_residual | missing_channel.speed | native_edges | native_gap | progress | scale | sector_sum | session_reference | sliced_duration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 201 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 |
| 2019 | 303 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 2020 | 112 | 0 | 0 | 0 | 0 | 0 | 0 | 214 | 0 |
| 2021 | 224 | 0 | 0 | 10 | 4 | 0 | 0 | 0 | 0 |
| 2022 | 42 | 0 | 6 | 2024 | 6 | 0 | 0 | 121 | 0 |
| 2023 | 64 | 0 | 6 | 2712 | 0 | 0 | 0 | 9 | 0 |
| 2024 | 65 | 0 | 6 | 2425 | 0 | 0 | 0 | 0 | 0 |
| 2025 | 3 | 0 | 9 | 2956 | 0 | 0 | 0 | 21 | 0 |
| 2026 | 14 | 0 | 12 | 3258 | 0 | 0 | 0 | 5 | 0 |

## All failed lap gates — timing-eligible laps

| Year | interior_residual | missing_channel.speed | native_edges | native_gap | progress | scale | sector_sum | session_reference | sliced_duration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 203 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 |
| 2019 | 303 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 |
| 2020 | 112 | 0 | 0 | 0 | 0 | 1 | 0 | 214 | 0 |
| 2021 | 225 | 0 | 0 | 10 | 4 | 0 | 0 | 0 | 0 |
| 2022 | 233 | 0 | 6 | 2027 | 17 | 2 | 0 | 245 | 0 |
| 2023 | 363 | 0 | 6 | 2716 | 4 | 3 | 0 | 349 | 0 |
| 2024 | 396 | 0 | 6 | 2430 | 1 | 0 | 0 | 0 | 0 |
| 2025 | 202 | 0 | 9 | 2964 | 7 | 0 | 0 | 516 | 0 |
| 2026 | 685 | 0 | 12 | 3269 | 1 | 180 | 0 | 1147 | 0 |

Sector-sum and sliced-duration failures can be zero in this cohort because timing selection already enforces them. The all-indexed histograms below preserve those earlier exclusions.

## First failures — all indexed laps

| Year | Gate | Laps |
| --- | --- | ---: |
| 2018 | interior_residual | 201 |
| 2018 | native_gap | 7 |
| 2018 | sector_sum | 1 |
| 2018 | sliced_duration | 95 |
| 2018 | timing_eligibility | 4225 |
| 2019 | interior_residual | 303 |
| 2019 | native_gap | 1 |
| 2019 | sliced_duration | 80 |
| 2019 | timing_eligibility | 3607 |
| 2020 | interior_residual | 112 |
| 2020 | session_reference | 214 |
| 2020 | sliced_duration | 20 |
| 2020 | timing_eligibility | 3172 |
| 2021 | interior_residual | 224 |
| 2021 | native_gap | 10 |
| 2021 | progress | 4 |
| 2021 | sliced_duration | 80 |
| 2021 | timing_eligibility | 4060 |
| 2022 | interior_residual | 42 |
| 2022 | native_edges | 6 |
| 2022 | native_gap | 2024 |
| 2022 | progress | 6 |
| 2022 | session_reference | 121 |
| 2022 | sliced_duration | 114 |
| 2022 | timing_eligibility | 4006 |
| 2023 | interior_residual | 64 |
| 2023 | native_edges | 6 |
| 2023 | native_gap | 2712 |
| 2023 | sector_sum | 1 |
| 2023 | session_reference | 9 |
| 2023 | sliced_duration | 102 |
| 2023 | timing_eligibility | 5172 |
| 2024 | interior_residual | 65 |
| 2024 | native_edges | 6 |
| 2024 | native_gap | 2425 |
| 2024 | sliced_duration | 52 |
| 2024 | timing_eligibility | 5445 |
| 2025 | interior_residual | 3 |
| 2025 | native_edges | 9 |
| 2025 | native_gap | 2956 |
| 2025 | session_reference | 21 |
| 2025 | sliced_duration | 84 |
| 2025 | timing_eligibility | 5632 |
| 2026 | interior_residual | 14 |
| 2026 | native_edges | 12 |
| 2026 | native_gap | 3258 |
| 2026 | session_reference | 5 |
| 2026 | sliced_duration | 121 |
| 2026 | timing_eligibility | 4785 |

### All failed gates — all indexed laps

| Year | Gate | Laps |
| --- | --- | ---: |
| 2018 | interior_residual | 1452 |
| 2018 | native_gap | 83 |
| 2018 | progress | 1373 |
| 2018 | scale | 537 |
| 2018 | sector_sum | 1 |
| 2018 | sliced_duration | 95 |
| 2018 | timing_eligibility | 4225 |
| 2019 | interior_residual | 1606 |
| 2019 | native_gap | 20 |
| 2019 | progress | 1440 |
| 2019 | scale | 597 |
| 2019 | sliced_duration | 80 |
| 2019 | timing_eligibility | 3607 |
| 2020 | interior_residual | 985 |
| 2020 | progress | 1182 |
| 2020 | scale | 518 |
| 2020 | session_reference | 573 |
| 2020 | sliced_duration | 20 |
| 2020 | timing_eligibility | 3172 |
| 2021 | interior_residual | 1245 |
| 2021 | native_gap | 90 |
| 2021 | progress | 1567 |
| 2021 | scale | 664 |
| 2021 | sliced_duration | 80 |
| 2021 | timing_eligibility | 4060 |
| 2022 | interior_residual | 1255 |
| 2022 | native_edges | 16 |
| 2022 | native_gap | 5456 |
| 2022 | progress | 1562 |
| 2022 | scale | 556 |
| 2022 | session_reference | 416 |
| 2022 | sliced_duration | 114 |
| 2022 | timing_eligibility | 4006 |
| 2023 | interior_residual | 1568 |
| 2023 | native_edges | 16 |
| 2023 | native_gap | 7192 |
| 2023 | progress | 1945 |
| 2023 | scale | 637 |
| 2023 | sector_sum | 1 |
| 2023 | session_reference | 1094 |
| 2023 | sliced_duration | 102 |
| 2023 | timing_eligibility | 5172 |
| 2024 | interior_residual | 1791 |
| 2024 | native_edges | 14 |
| 2024 | native_gap | 7103 |
| 2024 | progress | 2067 |
| 2024 | scale | 822 |
| 2024 | sliced_duration | 52 |
| 2024 | timing_eligibility | 5445 |
| 2025 | interior_residual | 1272 |
| 2025 | native_edges | 25 |
| 2025 | native_gap | 8573 |
| 2025 | progress | 2223 |
| 2025 | scale | 598 |
| 2025 | session_reference | 1583 |
| 2025 | sliced_duration | 84 |
| 2025 | timing_eligibility | 5632 |
| 2026 | interior_residual | 1604 |
| 2026 | native_edges | 35 |
| 2026 | native_gap | 8131 |
| 2026 | progress | 1803 |
| 2026 | scale | 759 |
| 2026 | session_reference | 2986 |
| 2026 | sliced_duration | 121 |
| 2026 | timing_eligibility | 4785 |

The primary importer marks `native_timing_inconsistent` when sector sum OR exact source-clock duration differs by more than **5 ms**, before later 20 ms publication checks. The first offending source check is attributed to its numeric gate, with both source and preparation clock residuals retained. Source deletion/accuracy/pit/status exclusions remain explicit per lap and in each session/year ledger.

### Entirely missing in-lap channel observations — timing eligible

These are availability counts, not invented optional-channel gates.

| Year | Speed | Throttle | Gear | Brake | RPM |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2018 | 0 | 0 | 0 | 0 | 0 |
| 2019 | 0 | 0 | 0 | 0 | 0 |
| 2020 | 0 | 0 | 0 | 0 | 0 |
| 2021 | 0 | 0 | 0 | 0 | 0 |
| 2022 | 0 | 15 | 0 | 15 | 0 |
| 2023 | 0 | 0 | 0 | 0 | 0 |
| 2024 | 0 | 0 | 0 | 0 | 0 |
| 2025 | 0 | 0 | 0 | 0 | 0 |
| 2026 | 0 | 6 | 0 | 6 | 0 |

## Native interval distributions

Timing-eligible laps only. Unique actual car timestamps inside each lap define car sample spacing. Valid-speed intervals overlapping the lap use the original ±1 s window and available native edge padding. Maximum-gap distributions include only speed-bracketed laps. No resampled/display-grid points enter these distributions. Intervals are rounded to 1 microsecond for exact weighted nearest-rank quantiles; values below are milliseconds.

| Year | Distribution | N | P50 ms | P90 ms | P95 ms | P99 ms | Max ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | native_car_spacing | 653463 | 239.966 | 239.967 | 279.96 | 319.954 | 1199.829 |
| 2018 | native_speed_spacing | 656929 | 239.966 | 239.967 | 279.96 | 319.954 | 1199.829 |
| 2018 | speed_gaps_over_750ms | 7 | 1199.829 | 1199.829 | 1199.829 | 1199.829 | 1199.829 |
| 2018 | lap_max_speed_gap | 1733 | 359.949 | 399.943 | 399.944 | 439.937 | 1199.829 |
| 2019 | native_car_spacing | 885840 | 239.966 | 239.967 | 279.96 | 319.955 | 2680.617 |
| 2019 | native_speed_spacing | 890634 | 239.966 | 239.967 | 279.96 | 319.955 | 2680.617 |
| 2019 | speed_gaps_over_750ms | 3 | 1359.805 | 2680.617 | 2680.617 | 2680.617 | 2680.617 |
| 2019 | lap_max_speed_gap | 2397 | 360.948 | 399.944 | 400.943 | 439.94 | 2680.617 |
| 2020 | native_car_spacing | 715960 | 239.964 | 239.965 | 279.958 | 319.952 | 559.916 |
| 2020 | native_speed_spacing | 720006 | 239.964 | 239.965 | 279.958 | 319.952 | 559.916 |
| 2020 | speed_gaps_over_750ms | 0 | None | None | None | None | None |
| 2020 | lap_max_speed_gap | 2023 | 359.946 | 399.94 | 399.941 | 400.94 | 559.916 |
| 2021 | native_car_spacing | 1050102 | 239.964 | 239.965 | 240.964 | 279.959 | 5400.195 |
| 2021 | native_speed_spacing | 1055596 | 239.964 | 239.965 | 240.964 | 279.959 | 5400.195 |
| 2021 | speed_gaps_over_750ms | 10 | 1507.776 | 1507.776 | 5400.195 | 5400.195 | 5400.195 |
| 2021 | lap_max_speed_gap | 2747 | 279.959 | 280.958 | 280.958 | 332.95 | 5400.195 |
| 2022 | native_car_spacing | 993889 | 239.965 | 399.94 | 439.934 | 479.929 | 5229.217 |
| 2022 | native_speed_spacing | 999613 | 239.965 | 399.94 | 439.934 | 479.929 | 5229.217 |
| 2022 | speed_gaps_over_750ms | 3758 | 959.857 | 1199.821 | 1279.808 | 1560.767 | 5229.217 |
| 2022 | lap_max_speed_gap | 2859 | 959.857 | 1200.821 | 1279.809 | 1868.72 | 5229.217 |
| 2023 | native_car_spacing | 1260664 | 239.965 | 399.94 | 439.934 | 479.929 | 1839.723 |
| 2023 | native_speed_spacing | 1267846 | 239.965 | 399.94 | 439.934 | 479.929 | 1839.723 |
| 2023 | speed_gaps_over_750ms | 6125 | 959.857 | 1159.828 | 1200.822 | 1319.803 | 1839.723 |
| 2023 | lap_max_speed_gap | 3588 | 999.851 | 1199.822 | 1239.816 | 1359.798 | 1839.723 |
| 2024 | native_car_spacing | 1177788 | 239.965 | 399.94 | 439.934 | 479.929 | 5507.181 |
| 2024 | native_speed_spacing | 1184674 | 239.965 | 399.94 | 439.934 | 479.929 | 5507.181 |
| 2024 | speed_gaps_over_750ms | 4046 | 959.857 | 1199.821 | 1240.815 | 1359.798 | 5507.181 |
| 2024 | lap_max_speed_gap | 3440 | 919.863 | 1199.822 | 1279.809 | 1359.798 | 5507.181 |
| 2025 | native_car_spacing | 1029616 | 239.965 | 399.94 | 439.934 | 519.922 | 2480.632 |
| 2025 | native_speed_spacing | 1035824 | 239.965 | 399.94 | 439.934 | 519.922 | 2480.632 |
| 2025 | speed_gaps_over_750ms | 7468 | 959.858 | 1160.828 | 1239.816 | 1319.805 | 2480.632 |
| 2025 | lap_max_speed_gap | 3100 | 1079.831 | 1239.816 | 1280.809 | 1360.799 | 2480.632 |
| 2026 | native_car_spacing | 1150511 | 239.965 | 399.94 | 439.934 | 519.922 | 5360.205 |
| 2026 | native_speed_spacing | 1157213 | 239.965 | 399.94 | 439.934 | 519.922 | 5360.205 |
| 2026 | speed_gaps_over_750ms | 8605 | 959.858 | 1159.829 | 1239.806 | 1360.798 | 5360.205 |
| 2026 | lap_max_speed_gap | 3345 | 1079.84 | 1239.816 | 1279.811 | 1440.786 | 5360.205 |

### Speed-gap length bins (>750 ms)

Disjoint bins, not cumulative counts.

| Year | Gap bin | Intervals |
| --- | --- | ---: |
| 2018 | (750, 1000] ms | 3 |
| 2018 | (1000, 1500] ms | 4 |
| 2019 | (1000, 1500] ms | 2 |
| 2019 | (2000, 5000] ms | 1 |
| 2021 | (1500, 2000] ms | 9 |
| 2021 | > 5000 ms | 1 |
| 2022 | (750, 1000] ms | 2239 |
| 2022 | (1000, 1500] ms | 1469 |
| 2022 | (1500, 2000] ms | 30 |
| 2022 | (2000, 5000] ms | 12 |
| 2022 | > 5000 ms | 8 |
| 2023 | (750, 1000] ms | 3878 |
| 2023 | (1000, 1500] ms | 2245 |
| 2023 | (1500, 2000] ms | 2 |
| 2024 | (750, 1000] ms | 2568 |
| 2024 | (1000, 1500] ms | 1449 |
| 2024 | (2000, 5000] ms | 9 |
| 2024 | > 5000 ms | 20 |
| 2025 | (750, 1000] ms | 4668 |
| 2025 | (1000, 1500] ms | 2776 |
| 2025 | (1500, 2000] ms | 15 |
| 2025 | (2000, 5000] ms | 9 |
| 2026 | (750, 1000] ms | 5306 |
| 2026 | (1000, 1500] ms | 3280 |
| 2026 | (1500, 2000] ms | 15 |
| 2026 | > 5000 ms | 4 |

## Downstream gates not evaluated — timing eligible

| Year | Gate | Laps |
| --- | --- | ---: |
| 2020 | interior_residual | 214 |
| 2020 | pair_gap | 214 |
| 2020 | scale | 214 |
| 2021 | interior_residual | 4 |
| 2021 | pair_gap | 4 |
| 2021 | scale | 4 |
| 2022 | interior_residual | 267 |
| 2022 | pair_gap | 267 |
| 2022 | scale | 267 |
| 2023 | interior_residual | 357 |
| 2023 | pair_gap | 357 |
| 2023 | scale | 357 |
| 2024 | interior_residual | 7 |
| 2024 | pair_gap | 7 |
| 2024 | scale | 7 |
| 2025 | interior_residual | 530 |
| 2025 | pair_gap | 530 |
| 2025 | scale | 530 |
| 2026 | interior_residual | 1158 |
| 2026 | pair_gap | 1158 |
| 2026 | scale | 1158 |

## Pair-gap attribution

All distinct timing-eligible lap pairs are counted using scalar residual comparisons only; no Cartesian comparison artifacts or observations are generated. Same-phase and cross-phase-opt-in distinct-driver cohorts are separate. Same-driver pairs remain rejected by current selection and are recorded as such. Actual pair gates require both currently published telemetry laps; other calculable residual differences are diagnostic-only. A peer's failure remains pair context in each lap record.

| Year | Cohort | Pairs | Actual evaluated | Diagnostic evaluated | Prerequisites absent | Actual pair-sector-1 failures | Actual pair-sector-2 failures | Actual pair-lap-gap failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | same_driver_selection_blocked | 4362 | 0 | 4362 | 0 | 0 | 0 | 0 |
| 2018 | same_phase | 32188 | 24131 | 8057 | 0 | 304 | 340 | 0 |
| 2018 | cross_phase_opt_in | 46713 | 35774 | 10939 | 0 | 436 | 493 | 0 |
| 2019 | same_driver_selection_blocked | 7546 | 0 | 7546 | 0 | 0 | 0 | 0 |
| 2019 | same_phase | 61106 | 44144 | 16962 | 0 | 968 | 644 | 0 |
| 2019 | cross_phase_opt_in | 83668 | 64088 | 19580 | 0 | 1102 | 971 | 0 |
| 2020 | same_driver_selection_blocked | 7890 | 0 | 7246 | 644 | 0 | 0 | 0 |
| 2020 | same_phase | 58655 | 45171 | 8348 | 5136 | 399 | 936 | 0 |
| 2020 | cross_phase_opt_in | 84484 | 67385 | 10093 | 7006 | 442 | 1167 | 0 |
| 2021 | same_driver_selection_blocked | 9715 | 0 | 9699 | 16 | 0 | 0 | 0 |
| 2021 | same_phase | 74184 | 58672 | 15308 | 204 | 654 | 1235 | 0 |
| 2021 | cross_phase_opt_in | 106786 | 87856 | 18689 | 241 | 1072 | 1885 | 0 |
| 2022 | same_driver_selection_blocked | 10980 | 0 | 9411 | 1569 | 0 | 0 | 0 |
| 2022 | same_phase | 88860 | 5273 | 68071 | 15516 | 48 | 23 | 0 |
| 2022 | cross_phase_opt_in | 116209 | 6764 | 93745 | 15700 | 81 | 56 | 0 |
| 2023 | same_driver_selection_blocked | 13639 | 0 | 12802 | 837 | 0 | 0 | 0 |
| 2023 | same_phase | 112217 | 8146 | 96761 | 7310 | 114 | 126 | 0 |
| 2023 | cross_phase_opt_in | 142268 | 9953 | 122648 | 9667 | 114 | 106 | 0 |
| 2024 | same_driver_selection_blocked | 11088 | 0 | 11034 | 54 | 0 | 0 | 0 |
| 2024 | same_phase | 88512 | 7156 | 80860 | 496 | 46 | 78 | 0 |
| 2024 | cross_phase_opt_in | 122455 | 8789 | 113135 | 531 | 40 | 71 | 0 |
| 2025 | same_driver_selection_blocked | 9126 | 0 | 7976 | 1150 | 0 | 0 | 0 |
| 2025 | same_phase | 69265 | 258 | 60228 | 8779 | 0 | 4 | 0 |
| 2025 | cross_phase_opt_in | 100634 | 225 | 86305 | 14104 | 0 | 7 | 0 |
| 2026 | same_driver_selection_blocked | 11684 | 0 | 7417 | 4267 | 0 | 0 | 0 |
| 2026 | same_phase | 95317 | 103 | 60868 | 34346 | 2 | 0 | 0 |
| 2026 | cross_phase_opt_in | 140139 | 56 | 89109 | 50974 | 0 | 0 | 0 |

## Reproduce and inspect

```powershell
.venv\Scripts\python scripts/attribute_telemetry_gates.py
```

The script reads retained source snapshots and activated publications offline. Source digests, active file hashes, eligibility parity and every currently published lap's reconstructed timing array are checked. Raw car/position rows, authentication and absolute cache paths are not committed. The ledger contains derived diagnostics only. `config/telemetry-coverage.json` retains the original coverage fields and adds the attribution receipt, per-year and per-session summaries; the compressed JSON-lines companion records every indexed lap.

Gate definitions:

- `timing_eligibility`: Source validity/phase/compound/timing eligibility.
- `sector_sum`: Source import flags >5 ms inconsistency; later publication limit is >20.0001 ms (stages retained per lap).
- `sliced_duration`: Source import flags >5 ms clock inconsistency; later publication limit is >20.0001 ms (stages retained per lap).
- `native_edges`: Valid native speed does not bracket both lap edges.
- `native_gap`: Maximum native speed interval >750.0001 ms.
- `native_conflict`: Conflicting native records at one timestamp.
- `native_samples`: Insufficient native speed observations.
- `progress`: Nonpositive/nonmonotone integrated lap progress.
- `session_reference`: No accepted frozen session reference/geometry/markers.
- `interior_residual`: Unadjusted individual sector-crossing residual >150.0001 ms.
- `scale`: Absolute integrated-distance scale error >3.00001%.
- `missing_channel.speed`: No valid native Speed observations (required input).
- `other_alignment`: Other original v5 alignment rejection.

**Stop point:** Step 0 only. No contracts, v6 method, bridge masks, selection rules, graph rows or observation gates have changed. Review this report before proceeding to Step 1.


## Findings for owner review

- All **66,125 indexed laps** are recorded, including **25,271 timing-eligible laps**. **14,840** eligible laps currently lack graphs.
- The native-gap gate is first for **13,393** of those failures (**90.25%**).
- **25,232/25,271** eligible laps have car samples bracketing both edges under the v5 ±1 s crop (**99.85%**). **0** eligible laps have no in-lap car observations.
- Bracketing is a conservative input-feasibility check using the existing crop, not a new Tier 0 acceptance decision or a forecast of final coverage. Missing edge padding is not automatically complete source absence.
- Downstream failures overlap with gaps: the all-failure tables retain those conditional diagnostics. Where a frozen reference or valid progress is absent, residual/scale/pair checks remain not evaluated.
- Missing optional channels do not currently reject an entire lap. Peer-specific pair failures do not make a lap globally unusable.

### Session-reference failures

| Year | Sessions without a frozen v5 reference | No prepared reference candidate reached geometry checks |
| --- | ---: | ---: |
| 2018 | 0 | 0 |
| 2019 | 0 | 0 |
| 2020 | 2 | 0 |
| 2021 | 0 | 0 |
| 2022 | 1 | 0 |
| 2023 | 4 | 2 |
| 2024 | 0 | 0 |
| 2025 | 6 | 2 |
| 2026 | 9 | 5 |

Reference-candidate rejection messages (counts are candidate attempts, not laps or sessions):

- source turn annotation inventory is empty or exceeds the reviewed bound: 141.
- reference position coverage is incomplete: 126.
- source marker and position frames do not agree: 103.

### All diagnostic pair-gap failures

These are conditional residual probes after an earlier prerequisite failed, including currently disallowed same-driver pairs. They are **not** accepted comparison results or extra graph coverage. Counts overlap across checks.

| Year | Cohort | Diagnostic sector 1 | Diagnostic sector 2 | Diagnostic lap gap |
| --- | --- | ---: | ---: | ---: |
| 2018 | same_driver_selection_blocked | 315 | 345 | 0 |
| 2018 | same_phase | 2161 | 2329 | 0 |
| 2018 | cross_phase_opt_in | 3226 | 3238 | 0 |
| 2019 | same_driver_selection_blocked | 1167 | 814 | 0 |
| 2019 | same_phase | 9486 | 6474 | 0 |
| 2019 | cross_phase_opt_in | 10958 | 7158 | 0 |
| 2020 | same_driver_selection_blocked | 276 | 462 | 0 |
| 2020 | same_phase | 2141 | 3969 | 0 |
| 2020 | cross_phase_opt_in | 2198 | 4467 | 0 |
| 2021 | same_driver_selection_blocked | 713 | 881 | 0 |
| 2021 | same_phase | 4900 | 5832 | 0 |
| 2021 | cross_phase_opt_in | 6813 | 7072 | 0 |
| 2022 | same_driver_selection_blocked | 737 | 734 | 0 |
| 2022 | same_phase | 6986 | 6197 | 0 |
| 2022 | cross_phase_opt_in | 7479 | 7435 | 0 |
| 2023 | same_driver_selection_blocked | 1480 | 1484 | 0 |
| 2023 | same_phase | 13698 | 13532 | 0 |
| 2023 | cross_phase_opt_in | 15113 | 14477 | 0 |
| 2024 | same_driver_selection_blocked | 1357 | 996 | 0 |
| 2024 | same_phase | 11498 | 9120 | 0 |
| 2024 | cross_phase_opt_in | 13529 | 11163 | 0 |
| 2025 | same_driver_selection_blocked | 785 | 624 | 0 |
| 2025 | same_phase | 7122 | 5493 | 0 |
| 2025 | cross_phase_opt_in | 8355 | 6664 | 0 |
| 2026 | same_driver_selection_blocked | 1261 | 1537 | 0 |
| 2026 | same_phase | 12545 | 15099 | 0 |
| 2026 | cross_phase_opt_in | 17132 | 21166 | 0 |

### First pair-level blockers

Missing alignment is the actual early pair blocker when one or both laps have no published timing curve. Later residual differences are reported separately above, not silently substituted for this first gate.

| Year | Cohort | First gate | Pairs |
| --- | --- | --- | ---: |
| 2018 | same_driver_selection_blocked | selection_same_driver | 4362 |
| 2018 | same_phase | none | 23560 |
| 2018 | same_phase | missing_alignment | 8057 |
| 2018 | same_phase | pair_sector_1 | 304 |
| 2018 | same_phase | pair_sector_2 | 267 |
| 2018 | cross_phase_opt_in | none | 34930 |
| 2018 | cross_phase_opt_in | pair_sector_1 | 436 |
| 2018 | cross_phase_opt_in | missing_alignment | 10939 |
| 2018 | cross_phase_opt_in | pair_sector_2 | 408 |
| 2019 | same_driver_selection_blocked | selection_same_driver | 7546 |
| 2019 | same_phase | none | 42618 |
| 2019 | same_phase | missing_alignment | 16962 |
| 2019 | same_phase | pair_sector_1 | 968 |
| 2019 | same_phase | pair_sector_2 | 558 |
| 2019 | cross_phase_opt_in | none | 62133 |
| 2019 | cross_phase_opt_in | missing_alignment | 19580 |
| 2019 | cross_phase_opt_in | pair_sector_1 | 1102 |
| 2019 | cross_phase_opt_in | pair_sector_2 | 853 |
| 2020 | same_driver_selection_blocked | selection_same_driver | 7890 |
| 2020 | same_phase | none | 43897 |
| 2020 | same_phase | missing_alignment | 13484 |
| 2020 | same_phase | pair_sector_2 | 875 |
| 2020 | same_phase | pair_sector_1 | 399 |
| 2020 | cross_phase_opt_in | none | 65823 |
| 2020 | cross_phase_opt_in | missing_alignment | 17099 |
| 2020 | cross_phase_opt_in | pair_sector_2 | 1120 |
| 2020 | cross_phase_opt_in | pair_sector_1 | 442 |
| 2021 | same_driver_selection_blocked | selection_same_driver | 9715 |
| 2021 | same_phase | none | 56842 |
| 2021 | same_phase | missing_alignment | 15512 |
| 2021 | same_phase | pair_sector_2 | 1176 |
| 2021 | same_phase | pair_sector_1 | 654 |
| 2021 | cross_phase_opt_in | none | 85031 |
| 2021 | cross_phase_opt_in | missing_alignment | 18930 |
| 2021 | cross_phase_opt_in | pair_sector_1 | 1072 |
| 2021 | cross_phase_opt_in | pair_sector_2 | 1753 |
| 2022 | same_driver_selection_blocked | selection_same_driver | 10980 |
| 2022 | same_phase | missing_alignment | 83587 |
| 2022 | same_phase | none | 5204 |
| 2022 | same_phase | pair_sector_2 | 21 |
| 2022 | same_phase | pair_sector_1 | 48 |
| 2022 | cross_phase_opt_in | missing_alignment | 109445 |
| 2022 | cross_phase_opt_in | none | 6630 |
| 2022 | cross_phase_opt_in | pair_sector_2 | 53 |
| 2022 | cross_phase_opt_in | pair_sector_1 | 81 |
| 2023 | same_driver_selection_blocked | selection_same_driver | 13639 |
| 2023 | same_phase | missing_alignment | 104071 |
| 2023 | same_phase | none | 7911 |
| 2023 | same_phase | pair_sector_2 | 121 |
| 2023 | same_phase | pair_sector_1 | 114 |
| 2023 | cross_phase_opt_in | missing_alignment | 132315 |
| 2023 | cross_phase_opt_in | none | 9735 |
| 2023 | cross_phase_opt_in | pair_sector_1 | 114 |
| 2023 | cross_phase_opt_in | pair_sector_2 | 104 |
| 2024 | same_driver_selection_blocked | selection_same_driver | 11088 |
| 2024 | same_phase | none | 7037 |
| 2024 | same_phase | missing_alignment | 81356 |
| 2024 | same_phase | pair_sector_2 | 73 |
| 2024 | same_phase | pair_sector_1 | 46 |
| 2024 | cross_phase_opt_in | none | 8686 |
| 2024 | cross_phase_opt_in | missing_alignment | 113666 |
| 2024 | cross_phase_opt_in | pair_sector_2 | 63 |
| 2024 | cross_phase_opt_in | pair_sector_1 | 40 |
| 2025 | same_driver_selection_blocked | selection_same_driver | 9126 |
| 2025 | same_phase | missing_alignment | 69007 |
| 2025 | same_phase | none | 254 |
| 2025 | same_phase | pair_sector_2 | 4 |
| 2025 | cross_phase_opt_in | missing_alignment | 100409 |
| 2025 | cross_phase_opt_in | none | 218 |
| 2025 | cross_phase_opt_in | pair_sector_2 | 7 |
| 2026 | same_driver_selection_blocked | selection_same_driver | 11684 |
| 2026 | same_phase | missing_alignment | 95214 |
| 2026 | same_phase | none | 101 |
| 2026 | same_phase | pair_sector_1 | 2 |
| 2026 | cross_phase_opt_in | missing_alignment | 140083 |
| 2026 | cross_phase_opt_in | none | 56 |

### Re-render or inspect a lap

```powershell
.venv\Scripts\python scripts/render_gate_attribution.py
.venv\Scripts\python scripts/render_gate_attribution.py --lap-id fastf1_2026_19_Q_44_19
```

This renderer reads the committed derived ledger only. It neither reacquires data nor changes gates. The measurement command above followed by this renderer reproduces the complete report. Per-lap entries retain first/all lap gates, unknown downstream checks, raw eligibility reasons, channel availability, native gap measurements and actual/diagnostic peer context.

**Step 0 is the stop point.** Tier 0/Tier 1, contracts, same-driver selection, RPM and UI changes are not implemented by this audit. Tier 2 gate bodies and all measured v5 runtime files remain unchanged.
