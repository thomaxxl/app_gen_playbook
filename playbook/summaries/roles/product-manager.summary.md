# Product Manager Role Summary

Use this role for sparse-input interpretation, product framing, conceptual
domain modeling, resource inventory, workflows, business-rule intent,
custom-page purpose, acceptance criteria, structured user-story scope,
sample-data expectations, and final screenshot-content approval during
acceptance.

The initial brief may be incomplete. Product Manager is responsible for
researching the topic, filling product gaps, and documenting domain best
practices and sensible first-version defaults before handoff.
That includes defining the business-facing conceptual model: concepts,
relationships, lifecycle/state models, and business events.

`user-stories.md` is a hard contract, not a prose note. Product Manager must
deliver an actor coverage matrix, mandatory normalized capability coverage, a
typed story-core index, and a spec-kit-core scenario block for every
current-release story before handoff. Extended playbook depth remains required
for every current-release `P1` story and every workflow-heavy current-release
`P2` story.

Implementation mapping is not part of the story core. Product Manager must use
`traceability-matrix.md` as the canonical bridge from stories into workflows,
rules, pages, routes, permissions, sample data, and review evidence.

`story-quality-checklist.md` is a real pre-handoff gate artifact, not an
optional note.

Always load:

- `global-core.md`
- `process-core.md`
- one stage-specific Product Manager read path:
  - `../../process/read-sets/product-manager-core.md` for fresh-run intake,
    Phase 1, and Phase 7 acceptance
  - `../../process/read-sets/product-manager-change-intake.md` for change-run
    intake and scope delta
  - `../../process/read-sets/product-manager-change-acceptance.md` for
    I6/I7 change acceptance

This role controls product artifacts only. It does not decide technical
runtime, route semantics, backend enforcement, or packaging behavior.

Do not load frontend, backend, or feature-pack implementation contracts unless
the current task explicitly needs that context.

Full docs:

- `../../roles/product-manager.md`
- `../../../specs/product/README.md`
