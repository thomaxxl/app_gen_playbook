# Rule Selection Guide

Use this guide when translating approved business-rule IDs into LogicBank implementation choices.

## Preferred lane matrix

| Requirement shape | Preferred LogicBank lane | Why | Typical proof |
| --- | --- | --- | --- |
| Store a parent value on a child at transaction time | `Rule.copy` | Snapshot semantics; parent updates should not silently rewrite history | Insert child, later change parent, confirm child snapshot remains correct |
| Compute a mapped derived column from current state | `Rule.formula` | Live derivation with automatic recompute | Update input fields and confirm target recomputes |
| Compute a more complex derivation but still a pure function of row / parent state | `Rule.formula(..., calling=...)` | Still declarative in meaning, clearer in Python | Unit or ORM test of function-backed formula |
| Maintain a parent total from children | `Rule.sum` | Automatic adjustment across insert/update/delete/reparent | Create/update/delete/reparent child and confirm parent total |
| Maintain a parent child-count / existence check | `Rule.count` | Automatic child-count maintenance | Insert/delete/reparent child and confirm count |
| Reject invalid writes | `Rule.constraint` | Transactional rollback and shared enforcement | API-path invalid write returns aligned error; ORM-path invalid write rolls back |
| Derived rule depends on another derived rule | Declarative chaining | LogicBank is designed for watch/react/chain dependencies | Evidence shows upstream/downstream values both update correctly |
| Transition-based derivation / validation | Formula / constraint with `old_row` or `calling=...` | Keeps state transition logic in rule layer | Update old vs new values and confirm transition outcome |
| Side effect after transactional logic | Advanced event lane | Keep side effects near rule engine, not in transport handlers | Event evidence, side-effect tests, documented rationale |
| Audit child-row creation or allocation workflow | Advanced upstream pattern | Supported upstream, but outside starter default | Explicit exception record plus targeted tests |

## Starter-default subset vs advanced subset

### Starter-default subset for this playbook
Use these first:

- `Rule.copy`
- `Rule.formula`
- `Rule.sum`
- `Rule.count`
- `Rule.constraint`

These are the default, normal, expected rule lanes.

### Advanced subset
These may be valid, but require an explicit note in `rule-mapping.md` describing why the starter subset was insufficient:

- event-driven logic
- parent-check style patterns
- copy-row auditing
- allocation / distribution logic
- other advanced rule-extensibility patterns

## Snapshot vs live decision test

Ask:

1. Should the value remain as it was when the transaction happened?
   - yes -> `Rule.copy`
2. Should the value keep reflecting current upstream state?
   - yes -> `Rule.formula`

Do not answer “both.” If the use case genuinely needs both, model two different fields and document them.

## Constraint design checklist

Before writing custom imperative validation code, ask:

- Can I derive the needed support field first?
- Can a `count` or `sum` represent the prerequisite state?
- Can the invalid state then be rejected with a single `Rule.constraint`?
- Does the rule need `old_row`?
- Does the rule need only a better formula function (`calling=...`) rather than a custom event?

If the answer to any of those is yes, stay in the declarative lane.

## Aggregate design checklist

When a requirement says:
- total
- balance
- subtotal
- child count
- blocker count
- readiness based on child rows
- severity counts
- “any”, “none”, “more than N”

treat that as a strong signal for `Rule.sum` or `Rule.count`, usually followed by a `Rule.constraint` or formula.

Avoid writing bespoke recompute helpers in endpoints or service methods for these cases.

## Side-effect design checklist

If the requirement is:
- send email
- publish message
- write audit row
- emit Kafka event
- call an external API

separate the decision from the side effect:

1. derive / validate the business condition declaratively if possible
2. use an advanced event hook only for the side effect
3. document why the side effect cannot remain outside the transaction-triggered logic flow

## Natural-language logic safety rule

Natural-language logic can accelerate rule drafting, but it is not the source of truth.

Always inspect the translated Python and verify:
- the chosen `Rule.*` pattern is correct
- snapshot vs live semantics are correct
- target mapped attributes exist
- parent relationships used by the rules exist
- the tests prove the intended behavior

## What does not belong in LogicBank

Do not try to force these into LogicBank unless they truly are transactional business rules:

- pure read-only API aggregation that does not participate in write-time integrity
- API presentation shaping
- frontend layout behavior
- route design
- reporting-only queries
- one-off administrative scripts that intentionally operate out of contract

Those may still need backend code, but they are not replacements for LogicBank rule enforcement on transactional invariants.
