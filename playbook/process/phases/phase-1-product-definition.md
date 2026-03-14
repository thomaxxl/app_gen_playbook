# Phase 1 - Product Definition

Lead: Product Manager

## Goal

Turn business intent into an implementable product definition.

## Activities

- write user stories or scenarios
- define list/detail/edit/create needs per resource
- define resource inventory, CRUD surface, and key relationships explicitly
- define success and failure criteria
- define business rules in controlled natural language
- define sample data expectations
- define required custom pages
- record assumptions and unresolved questions explicitly

## Outputs

- completed `runs/current/artifacts/product/input-interpretation.md` when
  input was sparse or partial
- completed `runs/current/artifacts/product/research-notes.md`
- completed `runs/current/artifacts/product/user-stories.md`
- `runs/current/artifacts/product/brief.md`
- `runs/current/artifacts/product/resource-inventory.md`
- `runs/current/artifacts/product/resource-behavior-matrix.md`
- `runs/current/artifacts/product/workflows.md`
- `runs/current/artifacts/product/domain-glossary.md`
- `runs/current/artifacts/product/business-rules.md`
- `runs/current/artifacts/product/custom-pages.md`
- `runs/current/artifacts/product/acceptance-criteria.md`
- `runs/current/artifacts/product/sample-data.md`
- `runs/current/artifacts/product/assumptions-and-open-questions.md`

## Exit criteria

- desired user-facing behavior is explicit
- business rules exist in human-readable controlled language
- `runs/current/artifacts/product/business-rules.md` is no longer a stub
- `runs/current/artifacts/product/business-rules.md` includes a rule index
- `runs/current/artifacts/product/business-rules.md` distinguishes defaults
  from app-specific behavior
- every known non-default business rule has a stable rule ID
- resource-level expectations are clear
- resource inventory and resource behavior matrix exist and are explicit enough
  for downstream roles to stop guessing about CRUD, search, menu exposure, and
  key relationships
- sample-data and assumptions artifacts exist
- the product package is marked `ready-for-handoff` or `approved`
