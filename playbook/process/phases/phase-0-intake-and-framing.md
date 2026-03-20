# Phase 0 - Intake And Framing

Lead: Product Manager

## Goal

Establish the problem, user, scope, and app class, even when the starting
brief is sparse.

## Input source

Start from:

- `runs/current/input.md`

Use the seeded actionable copy at:

- `runs/current/role-state/product_manager/inbox/INPUT.md`

Classify that input using `../input-policy.md`.

## Activities

- classify input completeness level
- research the domain if the brief is sparse or ambiguous
- research baseline domain conventions, user expectations, and best-practice
  defaults when the brief does not specify them
- decide whether the app intent is explicit or inference-led
- choose the smallest coherent first-version framing that fits the house style
- identify primary users
- define top workflows
- identify core resources
- define initial scope and exclusions
- record rejected framing alternatives
- classify the app shape:
  - admin CRUD only
  - admin CRUD + business rules
  - admin CRUD + custom landing/reporting
  - more workflow-heavy transactional app
- note whether the request is clearly inside the starter house style or will
  require documented domain adaptation later

## Outputs

- `runs/current/artifacts/product/input-interpretation.md`
- `runs/current/artifacts/product/research-notes.md`
- initial `runs/current/artifacts/product/user-stories.md`
- initial `runs/current/artifacts/product/brief.md`
- initial `runs/current/artifacts/product/workflows.md`
- initial `runs/current/artifacts/product/domain-glossary.md`
- initial `runs/current/artifacts/product/assumptions-and-open-questions.md`

## Exit criteria

- user and scope are explicitly documented
- main resources are named
- critical workflows are identified
- sparse input has been actively interpreted rather than merely classified
- missing domain detail has been replaced with researched conventions,
  explicit first-version choices, or documented assumptions
- assumptions caused by sparse input are written down
- the proposed framing is stable enough to continue into Phase 1 without
  downstream guessing
