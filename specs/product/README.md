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
- `user-stories.md` is the authoritative scope catalog. It MUST keep the story
  core user-facing and testable, carry both the breadth matrix and normalized
  capability-coverage table, and use the exact story index schema the coverage
  compiler validates.
- `traceability-matrix.md` is the authoritative bridge from story scope to
  workflows, rules, pages, routes, permissions, sample data, and acceptance
  evidence.
- `story-quality-checklist.md` is the Product-owned readability/quality pass
  over the story catalog. It is not a replacement for the story compiler, but
  it records whether current-release stories are concrete, testable, and free
  of hidden implementation leakage.
- routing-first agents SHOULD start from the Product Manager summary and task
  bundle before loading individual template files

Template files:

- `input-interpretation.md`
- `research-notes.md`
- `brief.md`
- `resource-inventory.md`
- `resource-behavior-matrix.md`
- `user-stories.md`
- `workflows.md`
- `domain-glossary.md`
- `business-rules.md`
- `custom-pages.md`
- `traceability-matrix.md`
- `story-quality-checklist.md`
- `acceptance-criteria.md`
- `sample-data.md`
- `assumptions-and-open-questions.md`
- `acceptance-review.md`
