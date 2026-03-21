# LogicBank Reference Notes

This file is a scoped reference for maintainers and agents who are actively
implementing, verifying, or extending LogicBank-backed business rules.

It is not part of the default starter read set.

## Load boundary

The agent MUST load this file only when at least one of these is true:

- the current task is implementing `app/rules/rules.py`
- the current task is resolving `runs/current/artifacts/backend-design/rule-mapping.md`
- the current task is verifying actual LogicBank API signatures or engine
  behavior
- the current task is adding custom LogicBank events beyond the starter
  declarative subset
- the current task is debugging rule-execution drift that the starter
  `lifecycle.md`, `patterns.md`, `validation.md`, and
  `boundaries-and-errors.md` files do not already resolve

The agent MUST NOT load this file for:

- pure model-shape work with no rule behavior
- pure SAFRS exposure or route work
- frontend-only work
- Product wording or business-rule intent authoring
- general backend implementation when rule behavior is unchanged

This file exists to keep advanced LogicBank knowledge confined so it can later
move to a narrower role without widening the default backend read path.

`../../../skills/logicbank-rules-design/SKILL.md` is the default day-to-day
rule-selection guide. This file remains the advanced reference, not the first
stop for ordinary rule-mapping work.

## Source hierarchy

Use this precedence order when LogicBank docs disagree:

1. the playbook's generated-app contract under this `rules/` directory
2. the installed published `logicbank` package in the current backend runtime
3. the ApiLogicServer training docs under `/home/t/lab/ApiLogicServer-src`

The playbook remains the normative generated-app contract.

The installed published `logicbank` package is the truth for actual API
signatures and engine behavior.

The ApiLogicServer training material is a pattern library and warning source.
It MUST NOT become a second source of business meaning or generated-app
structure.

## Role boundary

The playbook keeps a three-layer business-logic split:

- human-readable rule intent:
  `../../../runs/current/artifacts/product/business-rules.md`
- executable mapping and traceability:
  `../../../runs/current/artifacts/backend-design/rule-mapping.md`
- technical LogicBank contract and implementation:
  this `rules/` contract directory plus `../../../templates/app/rules/`

This file MUST NOT be used to restate business meaning that belongs in the
Product artifacts.

## Starter subset

The starter playbook remains centered on:

- `LogicBank.activate(...)`
- `Rule.copy`
- `Rule.formula`
- `Rule.count`
- `Rule.sum`
- `Rule.constraint`

Do not widen the starter subset silently just because LogicBank supports
additional patterns.

## Rule-facing schema discipline

Every field referenced by starter LogicBank derivations MUST map to a real
SQLAlchemy model attribute.

In particular:

- every `Rule.copy` target MUST exist as a mapped column
- every `Rule.formula` target MUST exist as a mapped column unless the run
  explicitly documents a different supported pattern
- every `Rule.sum` and `Rule.count` target MUST exist as a mapped persisted
  parent column
- aggregate intermediates MUST be modeled explicitly rather than implied

The implementation MUST NOT hide required rule dependencies inside helper-only
code paths that LogicBank cannot observe.

## Copy versus formula

The distinction between `Rule.copy` and `Rule.formula` is semantically
important.

Use `Rule.copy` when the business meaning is:

- store the parent value at transaction time
- freeze or snapshot a value on the child row
- persist a denormalized reference that should not change merely because the
  parent later changes

Use `Rule.formula` when the business meaning is:

- always reflect the current state of referenced fields
- propagate parent-driven or row-driven derivation continuously
- recompute live derived state on relevant upstream changes

The backend rule mapping SHOULD record this distinction explicitly whenever the
run uses both patterns.

## Transaction boundary

LogicBank rules fire only through the mapped ORM session and the normal flush /
commit path.

That means:

- ORM writes through the app session are in contract
- raw SQL writes are out of contract
- bulk update/delete shortcuts that bypass normal row processing are out of
  contract
- at least one invalid-path test MUST go through the API
- at least one rule test MUST go through direct ORM commit

## Event usage

Events are advanced LogicBank behavior and MUST remain secondary to the
starter declarative subset.

When events are necessary, use this guidance:

- `early_row_event`
  for values that downstream formulas or constraints depend on in the same
  transaction path
- `row_event`
  for rare in-row post-formula logic
- `commit_row_event`
  for post-row-logic effects
- `after_flush_row_event`
  for actions that need DB-generated ids or flushed persistence state

If a run needs these patterns, the backend rule mapping MUST document why a
declarative `Rule.*` pattern was insufficient.

## Advanced patterns stay out of the starter core

The following remain advanced and MUST NOT be folded into the starter contract
by default:

- request / audit object patterns
- allocation / distribution patterns
- AI or probabilistic rules
- custom exception translation beyond the starter error surface
- multi-pack combinations that have not been validated explicitly

If a run needs one of those patterns, that requirement SHOULD be isolated in a
separate advanced contract or feature lane rather than widening the starter
rules contract.

## Known documentation hazards

When consulting upstream training material, be cautious about:

- stale navigation and file references
- examples that omit newer supported arguments such as `calling=...`
- contradictory import guidance
- helper examples that use the wrong `new_logic_row(...)` target type

If the training docs and the installed `logicbank` package disagree, trust the
installed package source.
