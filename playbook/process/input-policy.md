# Input Policy

This file defines how the initial `INPUT.md` should be interpreted, especially
when the starting brief is sparse.

## Canonical location

The initial user brief belongs in:

- `runs/current/role-state/product_manager/inbox/INPUT.md`

That file must contain the actual incoming brief before the Product Manager
agent begins processing. A placeholder shell is not a valid starting input.

For a fresh run, seed that file from:

- `runs/current/role-state/product_manager/inbox/INPUT.example.md`

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
3. write `runs/current/artifacts/product/input-interpretation.md`
4. write `runs/current/artifacts/product/research-notes.md`
5. write `runs/current/artifacts/product/user-stories.md`
6. state that assumptions were required
7. avoid inventing advanced features unless the input suggests them
8. record all important assumptions in
   `runs/current/artifacts/product/assumptions-and-open-questions.md`

The Product Manager must also record:

- the chosen framing
- why it was chosen
- the major alternatives that were not selected
- the first-version scope boundary

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

## Blocking threshold

Open questions do not block handoff unless they prevent:

- naming the core users
- naming the core resources
- naming the core workflows

If those basics can be established coherently, the Product Manager should
handoff a researched first-version proposal instead of stopping the process.
