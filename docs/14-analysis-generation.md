# How comparison analysis is generated

## What the current app does

The synthetic preview contains a fixed illustrative paragraph and a precomputed fictional metric fixture. It does not call an LLM. Real-result components currently read `artifact.analysis.text` and `artifact.observations` from the selected immutable comparison artifact. Different artifacts can contain different summaries; the browser does not ask a model to write a new one on every view.

The planned numerical engine computes the evidence for the exact selected laps, then produces deterministic templates from those facts. It is unfinished until the actual-import/alignment/evidence tickets pass. The current saved-artifact renderer is not evidence that those computations already exist.

## Can an LLM generate fresh analysis?

Yes. Use an optional narrative layer after numerical validation. Python remains responsible for distances, timings, support, class membership, uncertainty, quality and all gains. The LLM may explain and prioritize supported facts. It receives a compact evidence packet, not a screenshot that it must estimate numbers from.

For a new pair/lap selection, generate a fresh evidence packet. Reuse a narrative only when comparison ID, source revision, methodology, quality flags, prompt version, model and display language all match. An explicit Regenerate action can request different wording for the same facts. Calling a model on every cursor move or repeat page render adds cost and delay without adding evidence.

## Required evidence packet

- Exact driver identities, year, race, both qualifying phases and selected lap IDs.
- Recorded lap/sector times and verification scope.
- Reference and source revisions, raw timing residuals and warning/context flags.
- Native source-channel availability. Missing brake cannot support a braking statement.
- Region metrics with evidence IDs, supported ranges, native sample counts and sensitivity.
- Low/medium/high class totals, gross gains/losses, coverage, excluded windows and independent units.
- Permitted observations and explicit insufficient-evidence reasons.

Use driver identities in prose so A/B presentation swaps cannot change its meaning. Preserve cross-phase, missing-channel and data-quality qualifications in every output, including exported cards.

## Provider-independent response contract

A future narrative endpoint can return a `summary`, at most three findings with `evidence_ids`, `limitations`, comparison/method/prompt IDs and a generation mode of `template` or `llm`. Model outputs must reference existing evidence. The server rejects unknown evidence IDs, unsupported metrics, invented numbers and causal claims, then falls back to deterministic wording. An unavailable provider must not erase otherwise valid telemetry.

Structured model outputs help enforce a response shape, but factual correctness still needs application checks and adequate evidence. [Official structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

Keep provider keys server-side. Add bounded requests, explicit model configuration, output limits, timeouts, rate limits and usage accounting. No provider is currently configured, no key is stored in the browser and this scaffold makes no narrative API calls.

## Acceptance tests before enabling it

1. Change the selected laps and ensure the evidence/narrative identity changes.
2. Missing native brake, throttle or gear removes corresponding supported claims.
3. Perturb the text to include an unknown value or evidence ID; validation rejects it.
4. A partial category cannot become a statement about all high-speed corners.
5. Cross-phase and quality warnings survive both model and template paths.
6. Timeout, rate-limit, refusal or malformed output falls back to the same supported facts.
7. A regenerated narrative changes wording, never the underlying numbers.

This is an explicit next-stage option, not a hidden model dependency. Complete the real-data evidence engine first; then add the narrative layer to validated packets.
