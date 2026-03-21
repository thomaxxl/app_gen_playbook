---
name: logicbank-rules-design
description: Use when designing, implementing, or reviewing backend business logic for SQLAlchemy-backed apps so approved business rules default to LogicBank Rule.* patterns and documented LogicBank event hooks instead of ad hoc endpoint, service, bootstrap, or frontend enforcement.
---

# LogicBank Rules Design

Use this skill when the task touches any of the following:

- `runs/current/artifacts/backend-design/rule-mapping.md`
- `app/rules/**`
- backend derivations, constraints, lifecycle, transactional validation, or rule-oriented tests
- proposed custom Python logic for write paths, side effects, or multi-table business behavior

## Core stance

For SQLAlchemy-backed write logic, start with LogicBank's declarative rule DSL.

Do **not** start by writing imperative logic in:
- FastAPI / Flask endpoints
- service-layer mutation helpers
- bootstrap / seed scripts
- frontend form validation
- manual SQL triggers or raw-SQL mutation handlers
- custom ORM event wrappers that bypass documented LogicBank patterns

Those places may call into or rely on the backend rule layer, but they are **not** the default rule-definition lane.

## Required rule decision order

For each approved business rule ID, evaluate these lanes in order and record the result in `rule-mapping.md`.

### 1) Snapshot propagation from parent to child -> `Rule.copy`
Use `Rule.copy` when the business meaning is:
- copy a parent value into the child at transaction time
- preserve the copied value even if the parent changes later
- persist denormalized history, price, code, or label snapshots

Typical examples:
- item unit price copied from product unit price
- child status code copied from a status table
- invoice line tax rate snapped from the tax table at order time

### 2) Live derived column -> `Rule.formula`
Use `Rule.formula` when the business meaning is:
- compute a mapped target column from current row values
- recompute when upstream values change
- express a live derivation instead of a transaction-time snapshot

Typical examples:
- line amount = quantity * unit_price
- ready flag = all prerequisite conditions satisfied
- derived status / score / eligibility based on current state

Use `calling=...` when the rule is still fundamentally a formula but the expression is clearer as a Python function.

### 3) Parent aggregate -> `Rule.sum` or `Rule.count`
Use:
- `Rule.sum` for totals
- `Rule.count` for row counts and child-existence tracking

Typical examples:
- order amount total from line amounts
- customer balance from open orders
- item count on parent collections
- count-based flags such as “has children”, “has blockers”, or “has severity-5 notices”

When the aggregate is conditional, declare the qualification in the rule rather than inventing separate imperative recompute logic.

### 4) Invalid state rejection -> `Rule.constraint`
Use `Rule.constraint` when the rule means:
- reject a transaction if a condition is violated
- roll back invalid writes
- enforce derived/aggregate-dependent invariants

Typical examples:
- balance must not exceed credit limit
- completed rows require a completion timestamp
- shipped orders must have at least one line item
- product cannot be orderable if blocking notices exist

When a rule depends on a derived value, derive the value declaratively first, then constrain it.

### 5) Chained multi-table behavior -> combine declarative rules
Do not collapse a rule set into one large endpoint method merely because multiple tables are involved.

Prefer chains such as:
- `copy` -> `formula` -> `sum` -> `constraint`
- `count` -> `formula` -> `constraint`
- `copy` + `sum` + `constraint`

If the business logic spans multiple rows/tables, that is a signal to look **harder** at LogicBank, not to abandon it.

### 6) State-transition logic -> usually `old_row` plus declarative rules
If the rule depends on what changed, first check whether it can be expressed with:
- `Rule.formula(..., as_expression=...)`
- `Rule.formula(..., calling=...)`
- `Rule.constraint(..., as_condition=...)`

and use `old_row` where appropriate.

Only move beyond the declarative lane if the requirement truly cannot be modeled as a declarative derivation or constraint.

### 7) Advanced LogicBank behavior -> documented exception lane
If the need is truly outside the starter subset, consider upstream LogicBank / API Logic Server advanced patterns such as:
- events / side effects
- parent checks
- copy-row auditing
- allocation logic

These are **not** the default starter lane in this playbook. Use them only when:
- the approved rule really needs them, and
- `rule-mapping.md` explicitly records why the starter subset was insufficient.

### 8) Custom Python outside LogicBank -> last resort
Only use custom Python as the primary rule implementation when:
- the requirement is not naturally expressible as documented LogicBank rules or approved advanced patterns, and
- the transaction still runs through the mapped ORM session / commit path, and
- the exception is documented with why LogicBank was insufficient.

## Mandatory semantic distinctions

### `copy` is not `formula`
Record the semantic choice explicitly:

- `Rule.copy` = **snapshot** semantics
- `Rule.formula` = **live recompute** semantics

Never treat them as interchangeable. If a run uses both, `rule-mapping.md` must say which rule IDs are snapshot semantics and which are live-propagation semantics.

### Aggregates are first-class modeled data
If a rule needs:
- a total
- a count
- a readiness flag based on child existence
- a severity count
- a blocker count

model the required target fields explicitly on mapped SQLAlchemy classes. Do not hide aggregate state in helper-only code paths or transient endpoint variables.

### Constraints belong on the transaction, not only on the transport
If a rule must reject invalid writes, the default enforcement lane is LogicBank on the shared ORM transaction path.

Frontend validation and custom endpoint checks may mirror the rule for usability, but they do **not** replace backend transactional enforcement.

## Required lifecycle and boundary discipline

### Activation shape
Use the canonical split:
- `declare_logic()` contains rule declarations
- `activate_logic(session_factory)` calls `LogicBank.activate(...)`

Do not activate LogicBank at import time.

### Startup order
The rule-sensitive startup order is:
1. create tables
2. validate static contract artifacts as required by the playbook
3. activate LogicBank on the app session factory
4. seed through the ORM after activation
5. expose SAFRS models / start serving requests

### Transaction boundary
Rule-triggering writes must go through:
- mapped SQLAlchemy models
- the app session factory
- normal flush / commit

Out of contract by default:
- raw SQL mutation paths
- SQLAlchemy bulk update/delete shortcuts that bypass row logic
- unmapped write paths

If a custom endpoint performs writes, it must use the same session factory and commit path as the normal backend.

## Required artifact updates

When using this skill, the backend author must update:

- `runs/current/artifacts/backend-design/model-design.md`
- `runs/current/artifacts/backend-design/rule-mapping.md`
- `runs/current/artifacts/backend-design/test-plan.md`

At minimum, `rule-mapping.md` must record:
- rule ID
- business fields involved
- chosen LogicBank pattern
- whether the behavior is snapshot vs live
- backend enforcement location
- API-visible failure behavior where applicable
- backend test coverage
- whether custom Python or advanced events are used
- why declarative rules were insufficient, if an exception was needed

## Required validation stance

Every approved rule set needs proof, not just prose.

Minimum expectations:
- at least one invalid-path rule test through the API surface
- at least one rule test through direct ORM commit
- coverage for create / update / delete / reparent / status-change stories when relevant
- proof that copied / formula / sum / count targets are populated correctly
- proof that constraint failures roll back cleanly
- proof that activation occurs on the real app session factory

Use `templates/rule-proof-checklist.md` when designing or reviewing that evidence.

## Anti-patterns to reject

Reject designs that:
- place credit-limit, readiness, or completion-state logic only in endpoint handlers
- recompute aggregates manually in CRUD handlers
- scatter identical rule logic across API, bootstrap, and UI code
- rely on frontend validation as the only enforcement
- use raw SQL recompute helpers for ordinary transactional derivations
- hide rule dependencies in helper code instead of mapped model attributes
- trust natural-language rule generation without checking the resulting `Rule.*` mapping
- use advanced LogicBank events when plain `Rule.copy`, `Rule.formula`, `Rule.sum`, `Rule.count`, or `Rule.constraint` would suffice

## Deliverables in this skill

- `reference/rule-selection-guide.md`
- `reference/activation-and-boundaries.md`
- `templates/rule-exception-template.md`
- `templates/rule-proof-checklist.md`
- `integration/PLAYBOOK_INTEGRATION.md`

Read those before widening the rule implementation beyond the normal declarative lane.
