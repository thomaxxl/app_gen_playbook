# Phase 1 - Product Definition

Lead: Product Manager

## Goal

Turn business intent into an implementable product definition.

## Activities

- write user stories or scenarios
- build an actor-by-capability coverage matrix instead of a flat story list
- classify every story with the required story-type taxonomy
- research domain best practices and standard workflow expectations when the
  brief is incomplete or silent
- define list/detail/edit/create needs per resource
- define resource inventory, CRUD surface, and key relationships explicitly
- define success and failure criteria
- define business rules in controlled natural language
- define sample data expectations
- define required custom pages
- map every required story to workflows, rules, pages, routes, permissions,
  sample data, and acceptance IDs
- record detailed scenario coverage for every `must` story and every
  workflow-heavy `should` story
- record assumptions and unresolved questions explicitly
- replace brief-level gaps with researched product decisions, explicit
  conventions, or clearly documented assumptions before handoff

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
- `runs/current/artifacts/product/traceability-matrix.md`
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
- missing brief detail has been resolved into researched conventions,
  documented best-practice defaults, or explicit assumptions that downstream
  roles can follow without guessing
- every `must` story is mapped in `traceability-matrix.md` to workflow IDs,
  rule IDs, page IDs, route IDs, permission context, sample-data references,
  acceptance IDs, and required review obligations
- `user-stories.md` includes a real coverage matrix instead of a prose-only
  story list
- every primary actor has explicit capability coverage in `user-stories.md`
- every `must` story includes happy path, alternate path, negative or
  validation path, empty-state expectation, and permission context
- the product package is marked `ready-for-handoff` or `approved`
