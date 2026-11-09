# Repository working agreement

Read `docs/10-handoff.md`, `docs/00-blueprint.md`, and the selected ticket in `docs/06-implementation-plan.md` before editing. This file applies throughout the repository.

## Execution

1. Implement the first uncompleted ticket whose dependencies are complete. Work on one bounded feature at a time.
2. Read the contract and the ticket's named documents. Do not redesign the stack, sign convention, alignment method, or scope while implementing a ticket.
3. If evidence contradicts a numerical assumption or an upstream API changes, record the finding and propose the smallest documented decision update. Never invent real telemetry to proceed.
4. Make the smallest coherent change, run the ticket's checks, and update the status and handoff with exact commands/results and remaining limitations.
5. Commit each completed feature with a descriptive imperative subject, such as `Add qualifying lap eligibility filters`. Push the commit to the configured GitHub branch after checks pass. Never force push, rewrite shared commits, commit secrets/raw caches, or attribute commits to tools/models. Use the existing Git identity.

## Boundaries

- Python owns data selection, alignment, quality, delta, segments and evidence. Browser code renders the supplied results.
- Pydantic owns the wire schema; regenerate OpenAPI/TypeScript with `npm run contracts`. Do not hand-edit generated files.
- Delta is B minus A in milliseconds. Positive favours A. Traces use source-provided event-specific team colours; A is solid and B dashed, including teammates. Missing colours use neutral styling. A/B swap changes signs and labels, never the canonical reference/grid.
- Import the full session roster and all eligible laps. Phase belongs to each lap; cross-phase comparison requires explicit opt-in and persistent context. No curated driver-pair limit remains.
- Distinguish telemetry from sector-only results. Estimated 100 m mini-sectors are derived from telemetry; status/color codes are not timing durations. Sector-only mode has discrete crossing deltas, no interpolated corner claims.
- Corner-speed classes use the frozen reference and versioned thresholds. Retain coverage, gross gains/losses, mixed complexes and uncertainty before producing class conclusions.
- Unknown numeric data is `null`, never zero. No NaN/Infinity in JSON. Gear and brake are discrete channels.
- Preserve raw reconciliation errors. Never force curves to agree with timing and then claim independent validation.
- All three observation slots require evidence; display fewer observations when necessary.
- Do not ship synthetic previews, fabricated graphs, demo routes or fake fallback data. Artificial fixtures are permitted only in automated tests. No production fake driver times, maps, claims, or silent fallback data.
- Known wet compounds are supported; missing rain context stays unknown. Preserve condition warnings and do not interpret rain reports as measured track grip. Never relax validity or numerical gates to increase coverage.
- Keep downloaded data, access tokens and credentials outside Git. A cache is disposable; an exported analysis must carry provenance.
- Changes in algorithms require methodology version changes and regression checks. Changes in schema require generation and compatibility review.

## Verification

Run meaningful tests for changed behavior. For contract/API changes run Python tests, `npm run contracts:check`, `npm run typecheck`, and `npm run build`. For visual/interaction work inspect the changed UI at desktop and mobile sizes and complete the ticket's keyboard checks. CI has no live FastF1 network dependency.

## Current scope

R01 recorded classifications remain available across 1950–2026. Verified native publications now include Monza, Suzuka and Silverstone 2024; read `docs/20-verified-telemetry-release.md` for the expansion. The original first pilot was Monza 2024; read `docs/19-monza-2024-pilot.md` for its source exception, exact counts, examples and limitations. It uses native OpenF1 car/position plus identity-matched pinned TracingInsights timing clocks/flags, now supplemented by the authenticated primary raw-presence FastF1 adapter verified at Monza 2018. Monza-local T01–T10 behavior does not satisfy T11's other circuits/archive expansion or T12's broader durable release work. Run labels, optional RPM/DRS graphs and runtime LLM wording remain deferred. Never infer distance traces or corner claims from classification bests alone.

The approved design/scope decision is `docs/17-approved-ui-and-telemetry-rollout.md`: sports-editorial landing (A), G1 stacked overlays, and telemetry only for verified sessions/channels in 2018–2026. Earlier years retain timing comparisons. Monza/Silverstone/Suzuka are validation pilots, not a permanent three-circuit coverage limit. Year/source support never proves an individual session or channel is verified. Keep bulk telemetry out of Git and the Vercel bundle.

Keep the shared editorial theme and persistent dark/light controls. Use the existing session selectors, ECharts stack, linked map/evidence state and export components rather than replacing them. The current method is `distance-v5-openf1-native-composite`, contract 1.3.0 with legacy 1.2.0 reads. Raw telemetry stays ignored; the compact generated `pilot_data` publication is bundled for verified sessions and regenerated before deployment. Its current immutable revision supports exact result regeneration; it is not durable multi-revision archive hosting. `docs/11-implementation-workflow.md` gives the requested model/effort workflow; it does not replace ticket acceptance checks.
