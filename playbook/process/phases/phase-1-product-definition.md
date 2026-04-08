# Phase 1 - Product Definition

Lead: Product Manager

## Goal

Turn business intent into an implementable product definition.

## Activities

- define a business-facing conceptual domain model distinct from resources and
  database structure
- define the main business concepts, concept relationships, lifecycle/state
  models, and business events
- refine the Who / Why / What / How framing so later UX work can inherit a
  stable statement of users, pain points, outcomes, and intended experience
- turn those pain points and workflows into a user interview / walkthrough
  questionnaire that later roles can execute against the app
- distinguish business concepts from application resources, admin screens, and
  backend persistence structures
- write user stories or scenarios
- author `user-stories.md`, `traceability-matrix.md`, and
  `story-quality-checklist.md` from their exact template contracts rather than
  treating them as optional reference prose
- build an actor-by-capability coverage matrix instead of a flat story list
- normalize that breadth into a `Capability Coverage` table keyed by actor and
  capability band and treat that normalized table as the canonical breadth
  ledger
- classify every story with the required story-type taxonomy
- research domain best practices and standard workflow expectations when the
  brief is incomplete or silent
- define list/detail/edit/create needs per resource
- define resource inventory, CRUD surface, and key relationships explicitly
- define success and failure criteria
- define business rules in controlled natural language
- define sample data expectations
- define required custom pages
- keep the story core focused on user need, priority, why this priority, and
  independent test instead of mixing it with implementation mapping
- map every required current-release story to workflows, rules, resources,
  pages, routes, permissions, sample data, and acceptance IDs in
  `traceability-matrix.md`
- record a spec-kit-core scenario block for every current-release story
- record extended scenario-depth coverage for every current-release `P1` story
  and every current-release workflow-heavy `P2` story
- complete `story-quality-checklist.md` as the required pre-handoff quality
  pass before Architecture starts from the Product package
- record assumptions and unresolved questions explicitly
- replace brief-level gaps with researched product decisions, explicit
  conventions, or clearly documented assumptions before handoff

## Outputs

- completed `runs/current/artifacts/product/input-interpretation.md` when
  input was sparse or partial
- completed `runs/current/artifacts/product/research-notes.md`
- `runs/current/artifacts/product/conceptual-domain-model.md`
- `runs/current/artifacts/product/problem-framing.md`
- completed `runs/current/artifacts/product/user-stories.md`
- `runs/current/artifacts/product/ux-interview-questionnaire.md`
- `runs/current/artifacts/product/brief.md`
- `runs/current/artifacts/product/resource-inventory.md`
- `runs/current/artifacts/product/resource-behavior-matrix.md`
- `runs/current/artifacts/product/workflows.md`
- `runs/current/artifacts/product/domain-glossary.md`
- `runs/current/artifacts/product/business-rules.md`
- `runs/current/artifacts/product/custom-pages.md`
- `runs/current/artifacts/product/traceability-matrix.md`
- `runs/current/artifacts/product/story-quality-checklist.md`
- `runs/current/artifacts/product/acceptance-criteria.md`
- `runs/current/artifacts/product/sample-data.md`
- `runs/current/artifacts/product/assumptions-and-open-questions.md`

## Exit criteria

- desired user-facing behavior is explicit
- the product package explicitly states who the app is for, why it matters,
  what outcomes it must deliver, and how the experience should reduce the
  main pain points
- the business-facing conceptual model is explicit enough that downstream
  roles do not have to infer core concepts from CRUD resources alone
- important concept relationships, lifecycle states, and business events are
  explicit
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
- `problem-framing.md` includes a stable pain-point catalog and UX alignment
  implications instead of leaving the design intent implicit
- `ux-interview-questionnaire.md` exists and translates the main user pain
  points plus core workflows into stable question IDs QA can execute later
- every current-release story is mapped in `traceability-matrix.md` to
  workflow IDs, rule IDs, resource IDs, page IDs, route IDs, permission
  context, sample-data references, acceptance IDs, and required review
  obligations
- `user-stories.md` includes a real coverage matrix instead of a prose-only
  story list
- every primary actor has explicit capability coverage in `user-stories.md`
- every current-release story has explicit priority, why this priority, and an
  independent test
- every current-release story has a spec-kit-core story block with acceptance
  scenarios and edge cases
- every higher-depth story includes happy path, alternate path, negative or
  validation path, empty-state expectation, and permission context
- `story-quality-checklist.md` is complete, non-placeholder, and records
  whether the current-release story set is concrete, testable, breadth-complete,
  and free of hidden implementation leakage
- the product package is marked `ready-for-handoff` or `approved`
