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
- Delta is B minus A in milliseconds. Positive favours A. A is cyan; B is orange. A/B swap changes signs and labels, never the canonical reference/grid.
- Import the full session roster and all eligible laps. Phase belongs to each lap; cross-phase comparison requires explicit opt-in and persistent context. No curated driver-pair limit remains.
- Distinguish telemetry from sector-only results. Estimated 100 m mini-sectors are derived from telemetry; status/color codes are not timing durations. Sector-only mode has discrete crossing deltas, no interpolated corner claims.
- Corner-speed classes use the frozen reference and versioned thresholds. Retain coverage, gross gains/losses, mixed complexes and uncertainty before producing class conclusions.
- Unknown numeric data is `null`, never zero. No NaN/Infinity in JSON. Gear and brake are discrete channels.
- Preserve raw reconciliation errors. Never force curves to agree with timing and then claim independent validation.
- All three observation slots require evidence; display fewer observations when necessary.
- UI examples and fixtures must be labelled synthetic. The opt-in design preview is isolated from API results and real-data exports. No production fake driver times, maps, claims, or silent fallback data.
- Keep downloaded data, access tokens and credentials outside Git. A cache is disposable; an exported analysis must carry provenance.
- Changes in algorithms require methodology version changes and regression checks. Changes in schema require generation and compatibility review.

## Verification

Run meaningful tests for changed behavior. For contract/API changes run Python tests, `npm run contracts:check`, `npm run typecheck`, and `npm run build`. For visual/interaction work inspect the changed UI at desktop and mobile sizes and complete the ticket's keyboard checks. CI has no live FastF1 network dependency.

## Current scope

The user has prioritized recorded session/phase-best results before individual laps and telemetry. Follow `docs/16-results-first-milestone.md`: R01 imports classifications and event-specific rosters/teams; R02 adds actual run/lap selection through the existing T01–T12 gates. R01 is not completion of real telemetry ingestion. Preserve the synthetic preview and never infer distance traces or corner claims from classification bests alone.

The approved design/scope decision is `docs/17-approved-ui-and-telemetry-rollout.md`: sports-editorial landing (A), G1 stacked overlays, and telemetry only for verified sessions/channels in 2018–2026. Earlier years retain timing comparisons. Monza/Silverstone/Suzuka are validation pilots, not a permanent three-circuit coverage limit. Year/source support never proves an individual session or channel is verified. Keep bulk telemetry out of Git and the Vercel bundle.

The scaffold already contains session selectors, cached result rendering and a synthetic ECharts preview. Extend those components in T06–T09 instead of rebuilding them. `docs/11-implementation-workflow.md` gives the requested model/effort workflow; it does not replace ticket acceptance checks.
