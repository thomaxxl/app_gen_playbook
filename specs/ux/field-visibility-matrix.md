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

| Resource | Field | Label | List | Show | Create | Edit | Readonly | Hidden | Display format | Searchable | Sortable | Reference-label behavior | Widget intent | Form span | Rows | Reason when non-default |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | replace | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | replace | yes/no | yes/no | replace | replace | 3/4/6/12 | 3/5/etc | replace |

## Required rules

The real artifact MUST record:

- view-specific visibility decisions
- readonly or computed-field behavior
- reference-label expectations for related resources
- any non-default widget or formatting intent
- any non-default form width or textarea height intent
- whether the field should be compact, standard, or wide in desktop forms
- the reason whenever the field behavior differs from default generated CRUD
