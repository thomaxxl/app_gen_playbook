# Rule Proof Checklist

Use this checklist while filling `rule-mapping.md`, `test-plan.md`, and backend verification evidence.

## Per rule ID

- Rule ID:
- Product requirement source:
- LogicBank pattern:
- Target fields:
- Supporting parent / child relationships:
- Snapshot or live semantics:
- API-visible failure behavior (if any):
- Backend tests:
- Frontend mirror mode (if any):

## Design proof

- [ ] The rule was first evaluated against `copy`, `formula`, `sum`, `count`, and `constraint`
- [ ] The selected pattern matches the business meaning
- [ ] Snapshot vs live semantics are stated explicitly
- [ ] All rule-facing fields exist as mapped SQLAlchemy attributes
- [ ] All referenced relationships exist on mapped SQLAlchemy models
- [ ] Aggregates are modeled explicitly, not hidden in helpers
- [ ] Custom Python is justified if used
- [ ] Advanced LogicBank behavior is justified if used

## Lifecycle proof

- [ ] `declare_logic()` contains rule declarations
- [ ] `activate_logic(session_factory)` performs activation
- [ ] Activation occurs during app startup, not import time
- [ ] Activation targets the real application session factory
- [ ] Seeding occurs after activation when seed writes should obey rules

## Execution proof

Check all that apply:

- [ ] create path tested
- [ ] update path tested
- [ ] delete path tested
- [ ] reparent path tested
- [ ] status / lifecycle transition tested
- [ ] API invalid-path tested
- [ ] ORM invalid-path tested
- [ ] rollback behavior confirmed
- [ ] aggregate maintenance confirmed
- [ ] snapshot semantics confirmed
- [ ] live recompute semantics confirmed

## Boundary proof

- [ ] The implementation states that raw SQL writes are out of contract unless explicitly approved
- [ ] The implementation states that bulk ORM shortcuts bypassing row logic are out of contract unless explicitly approved
- [ ] Custom write endpoints use the same session / commit path
- [ ] No endpoint or frontend code is the sole enforcement location for the rule

## Evidence links

- `rule-mapping.md` section:
- `test-plan.md` section:
- test file(s):
- `contract-samples.md` / other evidence:
- exception record, if any:
