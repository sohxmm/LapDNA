# Current handoff

## Active owner decision — Step 0 complete; stop before Step 1

The owner explicitly approved [view tiers](23-view-tiers.md), superseding the
older alignment/coverage restrictions only for Tier 0/Tier 1. Tier 2 corner
observation gates remain byte-for-byte unchanged. The measurement checkpoint is
complete: [the report](23-gate-attribution.md) covers 217 sessions and 66,125
indexed laps; first/all failures, distributions, conditional checks and pair
context are in the coverage ledger and `config/gate-attribution-laps.jsonl.gz`.
Of 14,840 timing-eligible laps without graphs, 13,393 first fail the native gap
gate. All 25,271 eligible laps have in-lap car observations; 25,232 have both
edges bracketed within the existing ±1 s crop. These are feasibility findings,
not implemented Tier 0 coverage. Seven runtime files/ten Tier 2 function bodies
are byte-unchanged. Python, contracts, typecheck, 31 client tests and build pass.
Reproduce using `scripts/attribute_telemetry_gates.py` followed by
`scripts/render_gate_attribution.py`; the latter also accepts `--lap-id`.
**Stopped for owner report review before Step 1.** The deployed v5
application, contracts, selection rules and numerical behaviour are unchanged
by Step 0. Read that decision before following the older remaining-work text.

Updated 10 November 2026. Use **C:/Users/soham/OneDrive/Desktop/LapDNA**, remote
https://github.com/sohxmm/LapDNA.git, main branch. The Documents checkout is an
older copy. The user authorized remaining verified imports, repairs, commits,
pushes and Vercel deployment. Credentials and raw caches stay private/ignored.

## Actual live scope

All **217 past Q/actual SQ candidates in 2018–2026** are imported, audited and
deployed at https://lapdna.vercel.app; no past import candidate is unresolved.
Future sessions wait for actual source publication. Import coverage does not
mean every lap/pair can produce distance graphs.

2026 has 20 Q/six SQ imports. Twelve sessions have verified graph choices,
across China, Miami, Canada, Austria, Britain, Belgium, Netherlands, Italy,
Singapore and USA. [Coverage](21-archive-coverage.md) records exact phases and
the full year/session ledger. Mexico remains timing-only under unchanged native
gap/reference gates; both primary and OpenF1 composite attempts were checked.

Recorded results separately contain 1,169 Q and 24 SQ classifications across
1950–2026. F1DB v2026.20.0 adds Brazil's 22-driver qualifying, preserving all
1,192 prior session driver/position/status/phase-time records. Mexico keeps
HAM/LEC +119 ms Q3, -9 ms Q2 and LAW DSQ. Native rosters are event-specific,
including substitutes; never construct drivers/teams from a current-year list.

## Product and analysis

Sports-editorial landing → year → calendar → studio. Persistent blue dark and
off-white light themes. React/TypeScript/Vite with one ECharts Canvas stack;
Python owns selection, alignment, delta, quality, regions/classes and evidence.
Team colours come from each event; A solid/B dashed, including teammates.

Defaults retain the fastest eligible timing pair in the highest shared phase.
The Distance telemetry section explicitly names supported drivers/laps/phases;
choosing it can change the pair and earlier/slower laps with full disclosure.
Successful explicit comparisons move focus/scroll to the result. Independent
phases require opt-in and persistent context. Never silently change a timing
best to manufacture graphs. Pair checks still apply to telemetry-ready laps.

Supported pairs show speed, throttle, gear, measured binary brake and B−A delta
over shared distance, numbered turns, approximate performance map, estimated
100 m bins, ranked regions, corner-speed classes and up to three observations.
Positive delta favours A. Missing channels/spans stay null; brake is not pressure.
Timing-only output has recorded sector crossing points/table, no continuous
distance curve or local claims. PNG cards, evidence JSON and exact current-source
links work. Findings are calculated deterministically per comparison/cache miss;
there is no runtime LLM or synthetic production fallback.

Contracts 1.4.0 (legacy Q 1.2/1.3 reads), pipeline `native-sessions-4`, methods
`distance-v5-fastf1-native` / `distance-v5-openf1-native-composite`. Monza has an
authored disjoint profile; other layouts use approximate ±120 m marker windows
with merged complexes. These are not surveyed entry/apex/exit boundaries or
causal driver/car conclusions. No validity, gap or raw residual gate was relaxed.

## Sources, operations and evidence

Pinned FastF1 3.9.2 decodes original compressed car/position rows before default
filling; actual primary/mirror URLs and hashes identify delivery. Optional
weather may remain unknown. Missing annotations retain timing-only output.
2023 provider SS maps to actual SQ1–3. Reviewed 2026 Brazil/Sepang label aliases
require corroborating date/round/circuit identity; original metadata is retained.
See [the repair checkpoint](22-2026-telemetry-checkpoint.md).

`import_archive.py` resumes 2026 backwards, respecting SDK limits and the shared
450-attempt/hour ledger. `complete_archive.py` acquires/audits/freezes/releases;
`--publish-current` releases ready data independently. Auth expiry stops for
local renewal; never prompt for or expose credentials in chat.

The native audit checks 70,382 fastest-eligible same-phase pairs plus reversals:
26,751 telemetry and 43,631 sector-only results; 464 explicit discovery choices
are checked separately. Arbitrary actual-lap pairs are checked on demand.
Python tests pass with one Windows symlink skip; 31 client tests, contracts,
typecheck and build pass. Existing lazy-ECharts size advisory is non-fatal.
Hosted inventory, comparisons/reversals/exact IDs/colours, Australia 2024's
19-driver roster and current Brazil/Mexico recorded facts are verified.

Current application source `5e117098727475a20394359f6a7a8d0adf8316a8`, deployment `dpl_DW72dC1W4D9bEgCvNYJpLNLUGU8R`;
native catalogue `a6dd7043ee2ba38f46fcdf54e06f3f291afc27dce4b5ba1dcb6b099aa64c47d9`. Native inputs/runtime/contracts/frontend match
the full `fb91de24` audit exactly; the recorded-results refresh reuses that
verified native audit and is independently checked. [Hosting](12-hosting.md)
records the private receipts and browser proof.

## Remaining work

T11 is complete for the current past-session snapshot, not future source data.
T12 retains durable historical cross-method/revision lookup: old replaced-source
links can refuse. Keep exact current source/method identity; never translate
silently. Inferred run labels, optional RPM/DRS plots, clustering and runtime
LLM wording remain deferred. Public source sample existence does not guarantee
reliable continuous distance analysis; partial-gap support would need a reviewed
new method and regression evidence, not a larger threshold for coverage.
