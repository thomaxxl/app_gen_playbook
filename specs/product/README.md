# Product Artifact Templates

This directory contains generic product-artifact templates for the playbook.

Rules:

- These files are playbook source and MUST remain generic.
- Product Manager run output MUST be written under
  `../../runs/current/artifacts/product/`.
- `../../example/` MAY be consulted as a runnable reference app, but it MUST
  NOT replace run-owned product artifacts.
- For a fresh run, `../../example/` and `../../app/` MUST NOT be used as
  product inputs unless the task explicitly requests comparison or
  maintenance.

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
- `acceptance-criteria.md`
- `sample-data.md`
- `assumptions-and-open-questions.md`
- `acceptance-review.md`
