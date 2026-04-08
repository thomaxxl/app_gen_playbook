---
owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - problem-framing.md
  - user-stories.md
  - workflows.md
  - acceptance-criteria.md
unresolved:
  - replace with run-specific user interview and walkthrough questions
last_updated_by: playbook
---

# UX Interview Questionnaire

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/ux-interview-questionnaire.md`.

The run-owned artifact is the question set reviewers use to understand the
experience from a real user's perspective before implementation is frozen.

It is meant to answer questions such as:

- Can users orient themselves quickly?
- Can they find what they need without guessing?
- Can they complete the primary task flow cleanly?
- Where do friction, uncertainty, or trust gaps still appear?

This is a product-and-UX intent artifact, not a component list, route dump, or
test-script substitute.

## Purpose

The run-owned file MUST:

- translate user pain points into concrete interview or walkthrough questions
- give UX/UI and Frontend a sharper usability target than generic design
  interpretation
- give QA a structured question set to execute against the real app
- give Product acceptance a durable record of which user-experience questions
  the delivery had to answer

The Product Manager owns the artifact. Architect MUST pressure-test it for
critical workflow, navigation, search/findability, state-transition, and trust
or recovery gaps before UX design proceeds.

## Required top-level sections

The run-owned file MUST include these sections in this order:

1. `Purpose`
2. `Interview Scope`
3. `Primary User Perspectives`
4. `Question Set`
5. `Expected Signals`
6. `Execution Notes`
7. `Acceptance And Escalation Guidance`

## Section requirements

### `Interview Scope`

This section MUST identify:

- which release scope or workflows the questions cover
- which actors the questions are written for
- which user-facing journey areas are critical in the current release

### `Primary User Perspectives`

This section MUST name the user vantage points the walkthrough should simulate,
for example:

- first-time user
- returning operator
- approver or reviewer
- high-volume task performer

### `Question Set`

The run-owned file MUST include a normalized table with this exact shape:

| Question ID | Journey Area | Actor | Question | Why It Matters | Expected Evidence |
| --- | --- | --- | --- | --- | --- |
| `UXQ-001` | `navigation` | `<actor>` | `<question the reviewer should answer>` | `<why the question matters>` | `<what live signal or screen behavior should answer it>` |

Question IDs MUST stay stable so QA, Frontend, and Product acceptance can cite
them later.

The question set MUST cover, when relevant:

- orientation and first impression
- navigation and return-path clarity
- search and findability
- primary task completion
- error or empty-state recovery
- trust, proof, or reassurance cues

### `Expected Signals`

This section MUST explain what good answers should look like in the delivered
experience. Keep it user-facing. Do not turn it into implementation tickets.

### `Execution Notes`

This section MUST tell QA how to execute the questionnaire as a live
walkthrough, including:

- whether to use a seeded persona or story set
- which starting routes or entry points are valid
- which questions require live interaction rather than static screenshot review

### `Acceptance And Escalation Guidance`

This section MUST explain:

- which unanswered or failed questions are release blockers
- which findings should reopen Frontend, Product, Architect, Backend, or DevOps
- which questions are advisory only

## Relationship to other product artifacts

The run-owned file MUST stay aligned with:

- `problem-framing.md`
- `user-stories.md`
- `workflows.md`
- `acceptance-criteria.md`

If those artifacts evolve, the questionnaire MUST be updated so the questions
still reflect the intended user experience.

## Worked direction example

The playbook stays generic, but a run-owned questionnaire MAY include domain
questions like these when the brief calls for them:

| Question ID | Journey Area | Actor | Question | Why It Matters | Expected Evidence |
| --- | --- | --- | --- | --- | --- |
| `UXQ-001` | `navigation` | `shopper` | `Can I tell where to start and where to go next without reading support text?` | Weak orientation causes drop-off before task completion | Landing and page hierarchy make the next step obvious |
| `UXQ-002` | `search` | `shopper` | `Can I find the right item quickly when I know roughly what I want?` | Findability is often the deciding usability factor | Search and filtering reduce the result set predictably |
| `UXQ-003` | `primary-workflow` | `shopper` | `Can I complete checkout without confusion or hidden requirements?` | Primary-flow friction is a release blocker | The checkout path exposes progress, validation, and completion clearly |
