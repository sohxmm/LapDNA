# V6 telemetry-view coverage checkpoint

Measured on the unchanged v5 timing-eligible cohort; native snapshots and v5 publications are retained and hash-checked. No frontend rollout.

Tier 0 requires car timestamps at both timing edges only. Tier 1 requires native speed bracketing, increasing integrated progress, no speed gap above 2 s and a reference. No geometry/marker gate, sector-time fitting, interior-residual block, 3% scale block or pair-gap block is applied to Tier 1. These remain unchanged for Tier 2.

Cumulative bounds below are raw metres before canonical distance normalization. Quantiles use nearest rank over all speed-ready eligible laps, including those in reference-less sessions. Tier-1-only distributions and per-session denominators are also retained in the ledger. The bound is an endpoint-speed model diagnostic, not a physical guarantee, calibrated probability or independent validation.

Mode: `legacy_v5`. Sessions: 217. Catalogue: `a6dd7043ee2ba38f46fcdf54e06f3f291afc27dce4b5ba1dcb6b099aa64c47d9`.

| Year | Eligible | V5 graphs % | Tier 0 | Tier 0 % | Tier 1 | Tier 1 % | Bound P50 m | P90 m | P99 m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018 | 1733 | 88.00 | 1733 | 100.00 | 1733 | 100.00 | 0.000 | 0.000 | 0.000 |
| 2019 | 2397 | 87.32 | 2397 | 100.00 | 2396 | 99.96 | 0.000 | 0.000 | 0.000 |
| 2020 | 2023 | 83.89 | 2023 | 100.00 | 1809 | 89.42 | 0.000 | 0.000 | 0.000 |
| 2021 | 2747 | 91.34 | 2747 | 100.00 | 2742 | 99.82 | 0.000 | 0.000 | 0.000 |
| 2022 | 2865 | 23.25 | 2865 | 100.00 | 2583 | 90.16 | 2.250 | 10.465 | 21.008 |
| 2023 | 3594 | 22.34 | 3594 | 100.00 | 3241 | 90.18 | 3.111 | 12.254 | 26.126 |
| 2024 | 3446 | 27.57 | 3446 | 100.00 | 3417 | 99.16 | 1.944 | 9.441 | 20.573 |
| 2025 | 3109 | 3.86 | 3109 | 100.00 | 2581 | 83.02 | 5.853 | 15.002 | 27.313 |
| 2026 | 3357 | 2.03 | 3357 | 100.00 | 2204 | 65.65 | 6.194 | 15.303 | 25.452 |

## Remaining first failures

| Year | Gate | Laps |
| --- | --- | ---: |
| 2019 | speed_gap_over_2s | 1 |
| 2020 | session_reference | 214 |
| 2021 | progress | 4 |
| 2021 | speed_gap_over_2s | 1 |
| 2022 | progress | 17 |
| 2022 | session_reference | 245 |
| 2022 | speed_gap_over_2s | 20 |
| 2023 | progress | 4 |
| 2023 | session_reference | 349 |
| 2024 | progress | 1 |
| 2024 | speed_gap_over_2s | 28 |
| 2025 | progress | 7 |
| 2025 | session_reference | 512 |
| 2025 | speed_gap_over_2s | 9 |
| 2026 | progress | 1 |
| 2026 | session_reference | 1147 |
| 2026 | speed_gap_over_2s | 5 |

## Per-session coverage

| Session | Eligible | Tier 0 | Tier 1 | First failures |
| --- | ---: | ---: | ---: | --- |
| 2018-1-albert_park-Q | 14 | 14 | 14 | {} |
| 2018-10-silverstone-Q | 82 | 82 | 82 | {} |
| 2018-11-hockenheimring-Q | 45 | 45 | 45 | {} |
| 2018-12-hungaroring-Q | 68 | 68 | 68 | {} |
| 2018-13-spa-Q | 88 | 88 | 88 | {} |
| 2018-14-monza-Q | 134 | 134 | 134 | {} |
| 2018-15-marina_bay-Q | 100 | 100 | 100 | {} |
| 2018-16-sochi-Q | 90 | 90 | 90 | {} |
| 2018-17-suzuka-Q | 65 | 65 | 65 | {} |
| 2018-18-americas-Q | 97 | 97 | 97 | {} |
| 2018-19-rodriguez-Q | 113 | 113 | 113 | {} |
| 2018-2-bahrain-Q | 64 | 64 | 64 | {} |
| 2018-20-interlagos-Q | 108 | 108 | 108 | {} |
| 2018-21-yas_marina-Q | 105 | 105 | 105 | {} |
| 2018-3-shanghai-Q | 60 | 60 | 60 | {} |
| 2018-4-baku-Q | 60 | 60 | 60 | {} |
| 2018-5-catalunya-Q | 60 | 60 | 60 | {} |
| 2018-6-monaco-Q | 170 | 170 | 170 | {} |
| 2018-7-villeneuve-Q | 59 | 59 | 59 | {} |
| 2018-8-ricard-Q | 36 | 36 | 36 | {} |
| 2018-9-red_bull_ring-Q | 115 | 115 | 115 | {} |
| 2019-1-albert_park-Q | 104 | 104 | 104 | {} |
| 2019-10-silverstone-Q | 162 | 162 | 162 | {} |
| 2019-11-hockenheimring-Q | 97 | 97 | 97 | {} |
| 2019-12-hungaroring-Q | 111 | 111 | 111 | {} |
| 2019-13-spa-Q | 68 | 68 | 68 | {} |
| 2019-14-monza-Q | 83 | 83 | 83 | {} |
| 2019-15-marina_bay-Q | 107 | 107 | 107 | {} |
| 2019-16-sochi-Q | 93 | 93 | 93 | {} |
| 2019-17-suzuka-Q | 88 | 88 | 88 | {} |
| 2019-18-rodriguez-Q | 125 | 125 | 125 | {} |
| 2019-19-americas-Q | 106 | 106 | 105 | {"speed_gap_over_2s": 1} |
| 2019-2-bahrain-Q | 87 | 87 | 87 | {} |
| 2019-20-interlagos-Q | 102 | 102 | 102 | {} |
| 2019-21-yas_marina-Q | 90 | 90 | 90 | {} |
| 2019-3-shanghai-Q | 79 | 79 | 79 | {} |
| 2019-4-baku-Q | 112 | 112 | 112 | {} |
| 2019-5-catalunya-Q | 99 | 99 | 99 | {} |
| 2019-6-monaco-Q | 259 | 259 | 259 | {} |
| 2019-7-villeneuve-Q | 137 | 137 | 137 | {} |
| 2019-8-ricard-Q | 139 | 139 | 139 | {} |
| 2019-9-red_bull_ring-Q | 149 | 149 | 149 | {} |
| 2020-1-red_bull_ring-Q | 116 | 116 | 116 | {} |
| 2020-10-sochi-Q | 80 | 80 | 80 | {} |
| 2020-11-nurburgring-Q | 128 | 128 | 128 | {} |
| 2020-12-portimao-Q | 198 | 198 | 198 | {} |
| 2020-13-imola-Q | 151 | 151 | 151 | {} |
| 2020-14-istanbul-Q | 99 | 99 | 99 | {} |
| 2020-15-bahrain-Q | 68 | 68 | 68 | {} |
| 2020-16-bahrain-Q | 145 | 145 | 0 | {"session_reference": 145} |
| 2020-17-yas_marina-Q | 81 | 81 | 81 | {} |
| 2020-2-red_bull_ring-Q | 321 | 321 | 321 | {} |
| 2020-3-hungaroring-Q | 134 | 134 | 134 | {} |
| 2020-4-silverstone-Q | 99 | 99 | 99 | {} |
| 2020-5-silverstone-Q | 97 | 97 | 97 | {} |
| 2020-6-catalunya-Q | 86 | 86 | 86 | {} |
| 2020-7-spa-Q | 70 | 70 | 70 | {} |
| 2020-8-monza-Q | 81 | 81 | 81 | {} |
| 2020-9-mugello-Q | 69 | 69 | 0 | {"session_reference": 69} |
| 2021-1-bahrain-Q | 64 | 64 | 64 | {} |
| 2021-10-silverstone-Q | 124 | 124 | 124 | {} |
| 2021-11-hungaroring-Q | 92 | 92 | 92 | {} |
| 2021-12-spa-Q | 157 | 157 | 157 | {} |
| 2021-13-zandvoort-Q | 109 | 109 | 108 | {"speed_gap_over_2s": 1} |
| 2021-14-monza-Q | 106 | 106 | 106 | {} |
| 2021-15-sochi-Q | 158 | 158 | 158 | {} |
| 2021-16-istanbul-Q | 140 | 140 | 140 | {} |
| 2021-17-americas-Q | 77 | 77 | 77 | {} |
| 2021-18-rodriguez-Q | 111 | 111 | 111 | {} |
| 2021-19-interlagos-Q | 129 | 129 | 129 | {} |
| 2021-2-imola-Q | 110 | 110 | 110 | {} |
| 2021-20-losail-Q | 118 | 118 | 117 | {"progress": 1} |
| 2021-21-jeddah-Q | 186 | 186 | 185 | {"progress": 1} |
| 2021-22-yas_marina-Q | 123 | 123 | 123 | {} |
| 2021-3-portimao-Q | 180 | 180 | 180 | {} |
| 2021-4-catalunya-Q | 88 | 88 | 88 | {} |
| 2021-5-monaco-Q | 261 | 261 | 261 | {} |
| 2021-6-baku-Q | 81 | 81 | 79 | {"progress": 2} |
| 2021-7-ricard-Q | 81 | 81 | 81 | {} |
| 2021-8-red_bull_ring-Q | 132 | 132 | 132 | {} |
| 2021-9-red_bull_ring-Q | 120 | 120 | 120 | {} |
| 2022-1-bahrain-Q | 86 | 86 | 86 | {} |
| 2022-10-silverstone-Q | 241 | 241 | 241 | {} |
| 2022-11-red_bull_ring-Q | 154 | 154 | 154 | {} |
| 2022-12-ricard-Q | 84 | 84 | 84 | {} |
| 2022-13-hungaroring-Q | 148 | 148 | 148 | {} |
| 2022-14-spa-Q | 74 | 74 | 74 | {} |
| 2022-15-zandvoort-Q | 98 | 98 | 98 | {} |
| 2022-16-monza-Q | 93 | 93 | 93 | {} |
| 2022-17-marina_bay-Q | 124 | 124 | 123 | {"progress": 1} |
| 2022-18-suzuka-Q | 86 | 86 | 86 | {} |
| 2022-19-americas-Q | 87 | 87 | 87 | {} |
| 2022-2-jeddah-Q | 146 | 146 | 146 | {} |
| 2022-20-rodriguez-Q | 110 | 110 | 104 | {"progress": 6} |
| 2022-21-interlagos-Q | 245 | 245 | 0 | {"session_reference": 245} |
| 2022-22-yas_marina-Q | 94 | 94 | 94 | {} |
| 2022-3-albert_park-Q | 131 | 131 | 111 | {"speed_gap_over_2s": 20} |
| 2022-4-imola-Q | 134 | 134 | 134 | {} |
| 2022-5-miami-Q | 151 | 151 | 142 | {"progress": 9} |
| 2022-6-catalunya-Q | 84 | 84 | 84 | {} |
| 2022-7-monaco-Q | 191 | 191 | 190 | {"progress": 1} |
| 2022-8-baku-Q | 72 | 72 | 72 | {} |
| 2022-9-villeneuve-Q | 232 | 232 | 232 | {} |
| 2023-1-bahrain-Q | 76 | 76 | 76 | {} |
| 2023-10-silverstone-Q | 157 | 157 | 157 | {} |
| 2023-11-hungaroring-Q | 129 | 129 | 129 | {} |
| 2023-12-spa-Q | 131 | 131 | 131 | {} |
| 2023-12-spa-SQ | 83 | 83 | 83 | {} |
| 2023-13-zandvoort-Q | 279 | 279 | 279 | {} |
| 2023-14-monza-Q | 129 | 129 | 0 | {"session_reference": 129} |
| 2023-15-marina_bay-Q | 94 | 94 | 0 | {"session_reference": 94} |
| 2023-16-suzuka-Q | 70 | 70 | 0 | {"session_reference": 70} |
| 2023-17-losail-Q | 138 | 138 | 138 | {} |
| 2023-17-losail-SQ | 109 | 109 | 109 | {} |
| 2023-18-americas-Q | 99 | 99 | 99 | {} |
| 2023-18-americas-SQ | 98 | 98 | 98 | {} |
| 2023-19-rodriguez-Q | 76 | 76 | 76 | {} |
| 2023-2-jeddah-Q | 138 | 138 | 134 | {"progress": 4} |
| 2023-20-interlagos-Q | 98 | 98 | 98 | {} |
| 2023-20-interlagos-SQ | 79 | 79 | 79 | {} |
| 2023-21-vegas-Q | 188 | 188 | 188 | {} |
| 2023-22-yas_marina-Q | 77 | 77 | 77 | {} |
| 2023-3-albert_park-Q | 235 | 235 | 235 | {} |
| 2023-4-baku-Q | 114 | 114 | 114 | {} |
| 2023-4-baku-SQ | 56 | 56 | 0 | {"session_reference": 56} |
| 2023-5-miami-Q | 140 | 140 | 140 | {} |
| 2023-6-monaco-Q | 220 | 220 | 220 | {} |
| 2023-7-catalunya-Q | 105 | 105 | 105 | {} |
| 2023-8-villeneuve-Q | 196 | 196 | 196 | {} |
| 2023-9-red_bull_ring-Q | 129 | 129 | 129 | {} |
| 2023-9-red_bull_ring-SQ | 151 | 151 | 151 | {} |
| 2024-1-bahrain-Q | 83 | 83 | 83 | {} |
| 2024-10-catalunya-Q | 79 | 79 | 79 | {} |
| 2024-11-red_bull_ring-Q | 100 | 100 | 100 | {} |
| 2024-11-red_bull_ring-SQ | 67 | 67 | 67 | {} |
| 2024-12-silverstone-Q | 169 | 169 | 169 | {} |
| 2024-13-hungaroring-Q | 123 | 123 | 123 | {} |
| 2024-14-spa-Q | 152 | 152 | 124 | {"speed_gap_over_2s": 28} |
| 2024-15-zandvoort-Q | 103 | 103 | 103 | {} |
| 2024-16-monza-Q | 80 | 80 | 80 | {} |
| 2024-17-baku-Q | 100 | 100 | 100 | {} |
| 2024-18-marina_bay-Q | 87 | 87 | 87 | {} |
| 2024-19-americas-Q | 82 | 82 | 82 | {} |
| 2024-19-americas-SQ | 72 | 72 | 72 | {} |
| 2024-2-jeddah-Q | 126 | 126 | 126 | {} |
| 2024-20-rodriguez-Q | 88 | 88 | 88 | {} |
| 2024-21-interlagos-Q | 121 | 121 | 121 | {} |
| 2024-21-interlagos-SQ | 79 | 79 | 79 | {} |
| 2024-22-vegas-Q | 172 | 172 | 172 | {} |
| 2024-23-losail-Q | 178 | 178 | 178 | {} |
| 2024-23-losail-SQ | 170 | 170 | 170 | {} |
| 2024-24-yas_marina-Q | 79 | 79 | 79 | {} |
| 2024-3-albert_park-Q | 143 | 143 | 143 | {} |
| 2024-4-suzuka-Q | 73 | 73 | 73 | {} |
| 2024-5-shanghai-Q | 83 | 83 | 83 | {} |
| 2024-5-shanghai-SQ | 113 | 113 | 113 | {} |
| 2024-6-miami-Q | 111 | 111 | 111 | {} |
| 2024-6-miami-SQ | 110 | 110 | 110 | {} |
| 2024-7-imola-Q | 80 | 80 | 80 | {} |
| 2024-8-monaco-Q | 215 | 215 | 214 | {"progress": 1} |
| 2024-9-villeneuve-Q | 208 | 208 | 208 | {} |
| 2025-1-albert_park-Q | 89 | 89 | 89 | {} |
| 2025-10-villeneuve-Q | 179 | 179 | 179 | {} |
| 2025-11-red_bull_ring-Q | 85 | 85 | 0 | {"session_reference": 85} |
| 2025-12-silverstone-Q | 100 | 100 | 0 | {"session_reference": 100} |
| 2025-13-spa-Q | 86 | 86 | 0 | {"session_reference": 86} |
| 2025-13-spa-SQ | 62 | 62 | 0 | {"session_reference": 62} |
| 2025-14-hungaroring-Q | 85 | 85 | 85 | {} |
| 2025-15-zandvoort-Q | 94 | 94 | 89 | {"speed_gap_over_2s": 5} |
| 2025-16-monza-Q | 106 | 106 | 106 | {} |
| 2025-17-baku-Q | 63 | 63 | 63 | {} |
| 2025-18-marina_bay-Q | 90 | 90 | 90 | {} |
| 2025-19-americas-Q | 77 | 77 | 77 | {} |
| 2025-19-americas-SQ | 83 | 83 | 83 | {} |
| 2025-2-shanghai-Q | 103 | 103 | 103 | {} |
| 2025-2-shanghai-SQ | 103 | 103 | 103 | {} |
| 2025-20-rodriguez-Q | 106 | 106 | 106 | {} |
| 2025-21-interlagos-Q | 109 | 109 | 109 | {} |
| 2025-21-interlagos-SQ | 117 | 117 | 117 | {} |
| 2025-22-vegas-Q | 113 | 113 | 113 | {} |
| 2025-23-losail-Q | 147 | 147 | 147 | {} |
| 2025-23-losail-SQ | 184 | 184 | 184 | {} |
| 2025-24-yas_marina-Q | 88 | 88 | 88 | {} |
| 2025-3-suzuka-Q | 100 | 100 | 0 | {"session_reference": 96, "speed_gap_over_2s": 4} |
| 2025-4-bahrain-Q | 76 | 76 | 76 | {} |
| 2025-5-jeddah-Q | 86 | 86 | 86 | {} |
| 2025-6-miami-Q | 106 | 106 | 100 | {"progress": 6} |
| 2025-6-miami-SQ | 83 | 83 | 0 | {"session_reference": 83} |
| 2025-7-imola-Q | 82 | 82 | 82 | {} |
| 2025-8-monaco-Q | 229 | 229 | 228 | {"progress": 1} |
| 2025-9-catalunya-Q | 78 | 78 | 78 | {} |
| 2026-1-albert_park-Q | 163 | 163 | 163 | {} |
| 2026-10-spa-Q | 89 | 89 | 89 | {} |
| 2026-11-hungaroring-Q | 80 | 80 | 79 | {"progress": 1} |
| 2026-12-zandvoort-Q | 157 | 157 | 157 | {} |
| 2026-12-zandvoort-SQ | 139 | 139 | 139 | {} |
| 2026-13-monza-Q | 103 | 103 | 103 | {} |
| 2026-14-madring-Q | 108 | 108 | 0 | {"session_reference": 108} |
| 2026-15-baku-Q | 169 | 169 | 0 | {"session_reference": 169} |
| 2026-16-sepang-Q | 74 | 74 | 0 | {"session_reference": 74} |
| 2026-17-marina_bay-Q | 127 | 127 | 127 | {} |
| 2026-17-marina_bay-SQ | 119 | 119 | 119 | {} |
| 2026-18-americas-Q | 94 | 94 | 94 | {} |
| 2026-19-rodriguez-Q | 134 | 134 | 0 | {"session_reference": 134} |
| 2026-2-shanghai-Q | 117 | 117 | 117 | {} |
| 2026-2-shanghai-SQ | 158 | 158 | 158 | {} |
| 2026-20-interlagos-Q | 141 | 141 | 141 | {} |
| 2026-3-suzuka-Q | 126 | 126 | 0 | {"session_reference": 126} |
| 2026-4-miami-Q | 113 | 113 | 0 | {"session_reference": 113} |
| 2026-4-miami-SQ | 84 | 84 | 84 | {} |
| 2026-5-villeneuve-Q | 260 | 260 | 260 | {} |
| 2026-5-villeneuve-SQ | 181 | 181 | 181 | {} |
| 2026-6-monaco-Q | 271 | 271 | 0 | {"session_reference": 271} |
| 2026-7-catalunya-Q | 72 | 72 | 0 | {"session_reference": 72} |
| 2026-8-red_bull_ring-Q | 90 | 90 | 85 | {"speed_gap_over_2s": 5} |
| 2026-9-silverstone-Q | 80 | 80 | 0 | {"session_reference": 80} |
| 2026-9-silverstone-SQ | 108 | 108 | 108 | {} |

## Qualification

Grade C is currently assigned for an absolute S1/S2 interior residual above 150 ms; other results remain ungraded pending the proposed distribution-based review. A small or zero endpoint-model bound does not establish accuracy, especially for equal endpoint speeds. Bridged spans never feed corner observations.
The 80-90% Tier 1 projection for 2022-2025 is a hypothesis, not an acceptance target. Compare the measured rows above; no threshold was tuned to reach that range.
Existing v5 runtime bytes, inputs and Tier 2 body hashes remain frozen. The old endpoint retains its original serializers/IDs; v6 is opt-in and has separate publications.
