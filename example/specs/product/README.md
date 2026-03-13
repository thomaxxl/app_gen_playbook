# Product Artifacts

This directory holds product-manager-owned artifacts for a project using this
playbook.

This directory README is reference guidance for the playbook. It is not itself
a run artifact and does not participate in artifact-status workflow.

Suggested files to fill in:

- `input-interpretation.md`
- `research-notes.md`
- `brief.md`
- `user-stories.md`
- `workflows.md`
- `domain-glossary.md`
- `business-rules.md`
- `acceptance-criteria.md`
- `custom-pages.md`
- `sample-data.md`
- `assumptions-and-open-questions.md`
- `acceptance-review.md`

These are inputs to architecture, frontend, and backend work.

The first three files are required when the initial input is Level A or B
(concept-only or partial brief), and still recommended for Level C.

Recommended metadata at the top of each artifact:

- `owner`
- `phase`
- `status`
- `depends_on`
- `unresolved`
- `last_updated_by`

Allowed `status` values:

- `stub`
- `draft`
- `ready-for-handoff`
- `approved`
- `blocked`
- `superseded`
