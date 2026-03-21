# Playbook Integration For `logicbank-rules-design`

This file explains how to make the skill part of the real playbook path instead of optional background reading.

## 1. Copy the skill into the repo

Copy this directory to:

```text
skills/logicbank-rules-design/
```

The entrypoint is:

```text
skills/logicbank-rules-design/SKILL.md
```

## 2. Load the skill in the Backend Tier 1 read sets

Add this file to both startup read sets:

- `playbook/process/read-sets/backend-design-core.md`
- `playbook/process/read-sets/backend-implementation-core.md`

Recommended added line:

```text
- `../../../skills/logicbank-rules-design/SKILL.md`
```

Reason:
- Phase 4 owns backend design and rules mapping
- Phase 5 owns backend implementation and rule enforcement
- if the skill is not in those read sets, it remains optional guidance and can be skipped

## 3. Load the skill for Architect review paths

Add the skill to:

- `playbook/process/read-sets/architect-authoring-core.md`
- `playbook/process/read-sets/architect-review-core.md`

Reason:
- the Architect approves cross-layer exceptions
- rule-lane exceptions often affect API shape, write-path behavior, and validation expectations
- the Architect should not approve endpoint/service logic as the default rule lane without first checking the LogicBank decision order

## 4. Update the Backend role file

Update `playbook/roles/backend.md` so it explicitly requires this skill whenever the task involves:

- `runs/current/artifacts/backend-design/rule-mapping.md`
- `app/rules/**`
- business-rule implementation choices
- custom Python write logic that might replace LogicBank
- advanced LogicBank event behavior

Recommended policy text to add:

> When mapping approved business-rule IDs to implementation, the Backend agent MUST load and apply `skills/logicbank-rules-design/SKILL.md` before choosing custom Python, endpoint-layer validation, raw-SQL recompute helpers, or advanced LogicBank events. The agent MUST first evaluate the rule against `Rule.copy`, `Rule.formula`, `Rule.sum`, `Rule.count`, `Rule.constraint`, and declarative chaining.

## 5. Update the Architect role file

Update `playbook/roles/architect.md` so the Architect requires a LogicBank-lane review before approving a rule exception.

Recommended policy text to add:

> When reviewing backend rule exceptions, the Architect MUST require documented evidence that the approved business rule was evaluated against the default LogicBank declarative lane before approving endpoint/service/event/custom-Python alternatives.

## 6. Tighten the rules contract, not just the skill

The skill improves guidance. The contracts and gates must still enforce the result.

### Update `specs/contracts/rules/README.md`
Add a requirement that this skill is loaded for any task that:
- resolves `rule-mapping.md`
- edits `app/rules/**`
- proposes custom Python rule behavior
- verifies LogicBank event / API behavior

### Update `specs/contracts/rules/patterns.md`
Add an explicit rule-decision order:
1. `copy`
2. `formula`
3. `sum`
4. `count`
5. `constraint`
6. declarative chaining
7. advanced LogicBank pattern with documented exception
8. custom Python as last resort

Also add explicit rejection of:
- endpoint-only enforcement
- manual aggregate recomputation in CRUD handlers
- frontend-only enforcement for transactional invariants

### Update `specs/contracts/rules/lifecycle.md`
Cross-reference this skill for activation / boundary discipline and note that custom endpoints must not bypass the shared ORM commit path.

### Update `specs/contracts/rules/validation.md`
Require proof for:
- snapshot vs live semantics where relevant
- aggregate maintenance across create / update / delete / reparent
- API invalid-path coverage
- ORM invalid-path coverage
- activation on the real session factory

### Update `specs/contracts/rules/logicbank-reference.md`
Keep that file as the advanced reference, but treat this skill as the default day-to-day rule-selection guide. The advanced reference should remain scoped, not the default first stop for ordinary rule design.

## 7. Strengthen the run-owned backend design artifacts

The skill is most useful if the run-owned artifacts are forced to record the rule-lane choice.

### Update `specs/backend-design/rule-mapping.md`
Extend the required traceability table to include fields such as:
- starter LogicBank pattern considered
- chosen LogicBank pattern
- snapshot vs live semantics
- advanced/custom exception required?
- why declarative rules were insufficient
- ORM-path proof
- API-path proof

### Update `specs/backend-design/model-design.md`
Require each derived persisted field to identify whether it is maintained by:
- `copy`
- `formula`
- `sum`
- `count`
- custom logic
- out of scope

### Update `specs/backend-design/test-plan.md`
Require each rule-bearing resource to identify:
- representative create/update/delete/reparent stories
- invalid mutation stories
- ORM-path evidence
- API-path evidence
- activation proof

## 8. Add gate-level enforcement

Add a policy check in `specs/policy/requirements/` so the gate can fail when ordinary transactional business rules are implemented primarily through endpoint/service logic without a documented exception.

The policy should fail when:
- `rule-mapping.md` omits the LogicBank pattern choice
- custom Python is used without a recorded reason
- aggregate maintenance is implemented manually for ordinary CRUD flows
- invalid transactional invariants are enforced only in the frontend or only in custom endpoints
- required API / ORM rule evidence is missing

## 9. Reflect the rule-first stance in phase docs

Update:

- `playbook/process/phases/phase-4-backend-design-and-rules-mapping.md`
- `playbook/process/phases/phase-5-parallel-implementation.md`

Add explicit language that:
- Phase 4 maps approved rule IDs to LogicBank patterns before coding
- Phase 5 implements those choices in the shared rule layer, not primarily in transport handlers

## 10. Keep the starter subset narrow by default

Upstream LogicBank / API Logic Server support more patterns than the playbook starter subset.

Do not silently widen the playbook contract just because upstream supports:
- events
- parent check
- copy-row
- allocation

Keep the default starter lane centered on:
- `Rule.copy`
- `Rule.formula`
- `Rule.sum`
- `Rule.count`
- `Rule.constraint`

Use the advanced patterns only with an explicit documented need.
