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
- Unknown numeric data is `null`, never zero. No NaN/Infinity in JSON. Gear and brake are discrete channels.
- Preserve raw reconciliation errors. Never force curves to agree with timing and then claim independent validation.
- All three observation slots require evidence; display fewer observations when necessary.
- UI examples and fixtures must be labelled synthetic. No production fake driver times, maps, claims, or silent fallback data.
- Keep downloaded data, access tokens and credentials outside Git. A cache is disposable; an exported analysis must carry provenance.
- Changes in algorithms require methodology version changes and regression checks. Changes in schema require generation and compatibility review.

## Verification

Run meaningful tests for changed behavior. For contract/API changes run Python tests, `npm run contracts:check`, `npm run typecheck`, and `npm run build`. For visual/interaction work inspect the changed UI at desktop and mobile sizes and complete the ticket's keyboard checks. CI has no live FastF1 network dependency.

## Current scope

Only the scaffold and blueprint are complete. The first implementation ticket is T01. Follow `docs/06-implementation-plan.md`; do not treat described future features as existing functionality. Public deployment and raw-data redistribution are separate release tasks, not setup prerequisites.
