# Input Policy

This file defines how the initial `INPUT.md` should be interpreted, especially
when the starting brief is sparse.

## Brief source of truth

The canonical stored brief for the run is:

- `runs/current/input.md`

The Product Manager's actionable inbox copy is:

- `runs/current/role-state/product_manager/inbox/INPUT.md`

Rules:

- `runs/current/input.md` MUST contain the actual incoming brief before the
  Product Manager begins processing
- `runs/current/role-state/product_manager/inbox/INPUT.md` MUST be seeded from
  `runs/current/input.md` for a fresh run
- `INPUT.example.md` is only a shell used to create the actionable inbox copy
- if `runs/current/input.md` and inbox `INPUT.md` differ, `runs/current/input.md`
  MUST be treated as authoritative until the inbox copy is refreshed

## Sparse input rule

Sparse input is expected and valid.

Sparse input:

- does not trigger a clarification loop by default
- does not block the pipeline by itself
- is a Product Manager responsibility to research and interpret

## Allowed input quality

The process must support:

- Level A: concept only
- Level B: partial brief
- Level C: high-level design

Examples:

- Level A: `chess app`
- Level B: short description with some users and workflows
- Level C: named resources, workflows, rules, pages, and constraints

## Assumption policy

When the input is sparse, the Product Manager agent must:

1. choose the smallest coherent app that fits the house style
2. research the domain and normalize terminology
3. enumerate 2-4 plausible framings before choosing one
4. score those framings against the house-style fit rubric below
5. write `runs/current/artifacts/product/input-interpretation.md`
6. write `runs/current/artifacts/product/research-notes.md`
7. write `runs/current/artifacts/product/resource-inventory.md`
8. write `runs/current/artifacts/product/user-stories.md`
9. state that assumptions were required
10. avoid inventing advanced features unless the input suggests them
11. record all important assumptions in
   `runs/current/artifacts/product/assumptions-and-open-questions.md`

The Product Manager must also record:

- the chosen framing
- the candidate framings considered
- why it was chosen
- the rejected alternatives and why they were not selected
- the first-version scope boundary
- explicit exclusions
- whether domain adaptation is likely later
- which points came from input, research, or assumptions

## Sparse-input framing rubric

Each candidate framing SHOULD be scored against:

- fit with schema-driven admin style
- likely resource count
- need for real-time or highly interactive UX
- rule complexity
- likely custom-page count
- bootstrap and test-data feasibility
- confidence from sparse input plus research

The Product Manager MUST prefer the smallest coherent framing that fits this
rubric without inventing a broader product than the input justifies.

## Research evidence rule

The Product Manager MUST distinguish:

- facts derived from the input
- conventions or facts derived from research
- assumptions introduced to keep the pipeline moving

Research notes MUST make that separation visible.

## House-style interpretation

Unless the input says otherwise, interpret the request as an app in this house
style:

- schema-driven admin app
- resource-oriented data model
- optional business rules
- optional custom landing/reporting pages

Do not silently reinterpret sparse input as a consumer social app, real-time
multiplayer system, or another larger product class unless the input demands
it.

Example:

- `restaurant app` SHOULD usually be framed first as a narrow operations admin
  candidate, such as reservations or menu management, before broader POS or
  delivery-platform interpretations are considered

## Blocking threshold

Open questions do not block handoff unless they prevent:

- naming the core users
- naming the core resources
- naming the core workflows

If those basics can be established coherently, the Product Manager should
handoff a researched first-version proposal instead of stopping the process.
