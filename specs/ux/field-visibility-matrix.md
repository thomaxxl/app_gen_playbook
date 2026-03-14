owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/business-rules.md
unresolved:
  - replace with run-specific visibility matrix
last_updated_by: playbook

# Field Visibility Matrix Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/field-visibility-matrix.md`.

## Required matrix columns

The real artifact MUST define, per resource field:

| Resource | Field | Label | Section/group | Help text | Placeholder or prompt intent | Inline validation hint | Frontend mirror rule ID | List | Show | Create | Edit | Readonly | Hidden | Display format | Searchable | Sortable | Reference-label behavior | Widget intent | Form span | Rows | Content or microcopy notes | Reason when non-default |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | replace | replace | replace | replace | replace | BR-001 or none | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | replace | yes/no | yes/no | replace | replace | 3/4/6/12 | 3/5/etc | replace | replace |

## Required rules

The real artifact MUST record:

- view-specific visibility decisions
- readonly or computed-field behavior
- reference-label expectations for related resources
- any non-default widget or formatting intent
- any non-default form width or textarea height intent
- whether the field should be compact, standard, or wide in desktop forms
- helper text or prompt guidance where the default generated form is not
  self-explanatory
- inline validation or content notes when UX clarity depends on them
- any frontend validation mirror rule IDs for mirrored feedback
- the reason whenever the field behavior differs from default generated CRUD
