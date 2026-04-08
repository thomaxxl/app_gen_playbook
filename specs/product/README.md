# Product Artifact Templates

This directory contains generic product-artifact templates for the playbook.

Rules:

- These files are playbook source and MUST remain generic.
- Product Manager run output MUST be written under
  `../../runs/current/artifacts/product/`.
- `../../examples/` MAY be consulted as a runnable reference-example library,
  but it MUST NOT replace run-owned product artifacts or become a hidden
  baseline source.
- For a fresh run, `../../examples/` and local `../../app/` MUST NOT be used
  as product inputs unless the task explicitly requests comparison or
  maintenance.
- `business-rules.md` is the single authoritative human-readable business-rule
  catalog for the run. Product templates MUST NOT create a second competing
  rule-intent file.
- `conceptual-domain-model.md` is the authoritative business-facing
  conceptual model for the run. It defines concepts, concept relationships,
  lifecycle/state models, and business events, and it MUST NOT be used as a
  disguised database, ORM, route, or endpoint design file.
- `problem-framing.md` is the authoritative Who / Why / What / How framing for
  the run. It captures the primary users, pain points, product promise, and
  UX alignment implications in business language, and it MUST NOT become a
  disguised route plan, backend design file, or component inventory.
- `ux-interview-questionnaire.md` is the authoritative user-experience
  question set for reviewer and walkthrough use. It translates pain points and
  key workflows into concrete user questions that QA can execute later, and it
  MUST NOT degrade into a test runner script or implementation task list.
- `user-journeys.md` is the authoritative human-readable journey catalog. It
  keeps end-to-end user-goal paths distinct from both independently testable
  stories and lower-level workflows, and it MUST NOT collapse into route
  inventory, page choreography, or backend process mapping.
- `user-stories.md` is the authoritative scope catalog. It MUST keep the story
  core user-facing and testable, carry both the breadth matrix and normalized
  capability-coverage table, and use the exact story index schema the coverage
  compiler validates. It is a required Phase 1 authoring input, not reference-only prose.
- `traceability-matrix.md` is the authoritative bridge from story scope to
  concepts, business events, workflows, rules, resources, pages, routes,
  permissions, sample data, and acceptance evidence. Its exact schema now
  includes `Concept IDs` and `Business Event IDs`, and it is a required Phase 1
  authoring input, not reference-only prose.
- `journey-quality-checklist.md` is the Product-owned readability/quality pass
  over the journey catalog. It records whether current-release journeys are
  concrete, end-to-end, recovery-aware, and aligned with the story/workflow
  set before Architecture and UX start from the Product package.
- `story-quality-checklist.md` is the Product-owned readability/quality pass
  over the story catalog. It is not a replacement for the story compiler, but
  it records whether current-release stories are concrete, testable, and free
  of hidden implementation leakage, and it is a required pre-handoff Phase 1
  artifact.
- `spec-kit-crosswalk.md` documents how the playbook's split product artifacts
  map onto the future spec-kit shape so later interop work does not become
  guesswork.
- routing-first agents SHOULD start from the Product Manager summary and task
  bundle before loading individual template files

Template and reference files:

- `input-interpretation.md`
- `research-notes.md`
- `brief.md`
- `problem-framing.md`
- `ux-interview-questionnaire.md`
- `user-journeys.md`
- `journey-quality-checklist.md`
- `conceptual-domain-model.md`
- `resource-inventory.md`
- `resource-behavior-matrix.md`
- `user-stories.md`
- `workflows.md`
- `domain-glossary.md`
- `business-rules.md`
- `custom-pages.md`
- `traceability-matrix.md`
- `story-quality-checklist.md`
- `spec-kit-crosswalk.md`
- `acceptance-criteria.md`
- `sample-data.md`
- `assumptions-and-open-questions.md`
- `acceptance-review.md`
