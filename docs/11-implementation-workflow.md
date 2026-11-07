# Implementing LapDNA with GPT-6.1 Sol

Use the Desktop checkout and keep this repository as the shared memory between sessions. Open the folder as a project in Codex so implementation sees its AGENTS.md, contracts and handoff. The architecture is already specified; coding sessions should execute bounded tickets and report evidence when an assumption fails.

Current priority: the user requested [R01 recorded classifications first](16-results-first-milestone.md), now implemented for acceptance using Mexico 2026. Individual laps/runs are deferred to R02. The T01 prompt below applies when that next milestone starts; R01 is not native telemetry ingestion.

## Model and effort

**Project recommendation: GPT-6.1 Sol at High for most implementation tickets.** Extra High is appropriate for alignment/reconciliation and hard cross-panel state problems. Use Max for a stubborn numerical defect that benefits from deeper work on one problem. Use Ultra when a milestone has independent parts with frozen interfaces that can be implemented or checked in parallel.

Official documentation distinguishes Ultra's parallel subagent work from Max's deeper work on one task; availability depends on the client/settings. The API model lists low, medium, high, xhigh and max, so do not paste an assumed ultra API parameter into application code. [Codex model controls](https://learn.chatgpt.com/docs/models?surface=app), [GPT-6.1 Sol API model](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

The allocation below is a project-specific starting point, not an official guarantee or measured benchmark:

| Work | Recommended effort | Reason |
| --- | --- | --- |
| T01 adapter/import and T02 inventory | High | Mostly specified interfaces, source errors and eligibility edge cases |
| T03–T04 distance/reference/reconciliation | Extra High | Units, clocks, uncertainty and invariant checks need careful work |
| T05 evidence, classes, local engine | Extra High | Avoid double counting and unsupported prose |
| T06 selectors, phase defaults and cached requests | High | Contracts are fixed; test stale response and consent cases |
| T07–T09 chart/map/evidence interaction | High; Extra High for complex synchronization | Reuse the existing ECharts adapter and shared distance state |
| T10 export | High | Deterministic layout and provenance checks |
| T11 independent circuit validation | Ultra when source/reference interfaces are stable | Separate circuit review and independent test review can run in parallel |
| T12 packaging and routine fixes | High or Medium for a narrow known fix | Scope is explicit; run the release gates |

Do not default every small task to Ultra. More parallelism is useful only when ownership and interfaces are clear. An alignment function and its consumer changing the same schema simultaneously create integration work. Keep Astra available for a design change, unresolved scientific ambiguity, or an independent review of the final numerical method; Sol can implement and test the supplied design.

## Session 1

1. Open the Desktop LapDNA folder. Choose GPT-6.1 Sol, High.
2. Start from T01. Read handoff, overview, methodology, sources and the T01 ticket.
3. Ask for implementation of T01 only, with its real access check and no silent redesign.
4. Verify the handoff records exact commands/results and remaining limits; a narrow source probe does not complete the importer.
5. Continue to the next ticket only after its dependencies pass. A code skeleton is not evidence of a working real-data feature.

## Copyable ticket prompt

> Work in this LapDNA repository. Read AGENTS.md, docs/10-handoff.md and ticket T01 in docs/06-implementation-plan.md. Implement only that ticket and its named specifications. Preserve comparison/inventory contract 1.2.0, calendar contract 1.0.0, native-channel provenance, raw B-minus-A delta, fixed reference, per-lap phases and source capability distinctions. Read the 20-source audit, preserve raw missing-value masks and keep all labelled demo channels. Reuse existing code. Run the ticket's tests and required contract/type/build checks. Document actual source access and limitations; never substitute synthetic data for a failed import. Update status/handoff, inspect the diff, commit the small completed feature with a descriptive message, and push to the configured repository. If evidence contradicts the blueprint, report the exact finding and smallest decision needed before dependent implementation.

Replace T01 with the next ticket. The user has already authorized ordinary feature commits/pushes. Do not add tool/model attribution to commit subjects.

## Ultra milestone prompt

> Implement the selected milestone using separate owners for the already agreed interfaces: one owner for Python implementation, one for meaningful edge-case tests, and one for independent review/documentation. The parent owns integration. Freeze the schema before parallel edits, avoid overlapping file ownership, and merge only after each part's checks and the integrated checks pass. Do not dispatch different agents to redesign the same component.

For three-circuit validation, give each agent one circuit/profile and a common evidence-report template. The parent checks that thresholds and semantics remain identical. Do not ask each agent to select a new algorithm.

## Review checkpoints

After T04 inspect clocks, boundary coverage, scale factors, raw timing residuals, reference calibration and swap invariance. After T05 inspect supported/excluded class windows, mixed complexes, gross versus net, category coverage, and every observation's evidence. After T07–T09 use pointer and keyboard selection at desktop/mobile sizes and verify turn alignment. After T10 inspect actual PNGs and JSON, including cross-phase and insufficient-evidence cases.

A useful implementation summary states changed behavior, tests that passed, actual data checked, limitations, commit, and next ticket. Return architecture questions to the blueprint session only when evidence requires a decision; routine file/function choices are already assigned.
