# 2026 telemetry correction

The 166-session release did not deliver usable 2026 distance graphs. Its only
2026 native publication was Mexico qualifying, and that entire publication was
timing-only. Calendar classifications and imported sessions must never be
described as verified two-driver graph coverage.

The archive queue now starts at 2026 and proceeds backwards. Provider limits and
the shared persistent request ledger remain enabled; changing queue order does
not reset either limit. Missing source samples are not invented and the 750 ms
speed-gap limit, independent sector residuals and all eligibility gates remain
unchanged.

## Finding an actual graph comparison

The session selector retains the fastest eligible timing laps as its default.
A new Distance telemetry section lists actual telemetry-supported drivers by
phase, and offers an explicit choice of the two fastest supported drivers/laps
in each same-phase group. Each button names the drivers, phase, lap numbers and
times before changing the selection. It does not silently replace either driver
or the selected phase. Pairwise reconciliation still runs on the server; two
individually supported laps do not guarantee the pair will pass.

The publication audit additionally checks these discovery choices, their reverse
orientation and their regional/mini-sector sums. The coverage ledger retains
these results separately from fastest-eligible-phase pair counts.

The first locally verified 2026 example is China Q1: Norris lap 2 versus Gasly
lap 2 (`fastf1_2026_2_Q_1_2` / `fastf1_2026_2_Q_10_2`). It returns a distance
comparison and three supported observations. Norris/Ocon and Gasly/Ocon Q1 also
passed direct checks. A local result is not a deployed result: the latest frozen
release and hosted verification receipt in [the coverage record](21-archive-coverage.md)
determine what is actually live.

Australia initially has only one distance-capable lap, Russell Q1 lap 7, so it
cannot provide a two-driver same-phase distance comparison. Mexico retains real
speed/control samples but no qualifying lap passes the present continuous
alignment gates; it remains timing-only. Source sample existence alone is not
evidence for reliable distance-based local gains. No elapsed-time plot is
misrepresented as a common-distance comparison.

## Checks at the implementation checkpoint

Python suite passes (one Windows symlink skip); 31 browser-unit checks pass;
contracts, typecheck and production build pass. The China audit checks all 396
fastest-eligible phase pairs (timing-only), and separately verifies the explicit
Q1 Norris/Gasly telemetry choice. Local browser checks confirm that clicking the
choice renders all five graph rows, the source orange/blue team colours and turn
labels. At 390 × 844 in light mode, keyboard activation moves focus to the
result and the page has no horizontal overflow. This is local QA, not a hosted
deployment receipt.
