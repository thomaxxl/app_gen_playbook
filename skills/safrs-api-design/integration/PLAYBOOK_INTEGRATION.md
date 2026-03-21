# Integrating the `safrs-api-design` Skill into `app_gen_playbook`

This skill should be added as guidance, not as the only enforcement point.
The playbook already has SAFRS-first intent in contracts, backend role rules, and quality blockers.
The integration goal is to make the skill load reliably during the phases where authors are most likely to invent the wrong API shape, and then tie the skill's outputs into contracts, policy, and validation.

## 1. Copy the skill into the repo

Copy this directory to:

- `skills/safrs-api-design/`

The minimum required file is `SKILL.md`.
The supporting docs in `reference/`, `templates/`, and `integration/` are optional but useful.

## 2. Auto-load it through the existing backend read paths

Do not change the loading protocol.
Use the existing read-set and task-bundle structure.

### Required edits

Add this startup read to both backend Tier 1 core read sets:

- `playbook/process/read-sets/backend-design-core.md`
- `playbook/process/read-sets/backend-implementation-core.md`

Suggested line to add near the backend contract reads:

- `../../../skills/safrs-api-design/SKILL.md`

Why here:

- backend Phase 4 and Phase 5 task bundles already always load these read sets
- the backend change-delta read set already delegates to these stage-specific read sets
- this keeps loading narrow and respects the current retrieval-first structure

### Recommended edit for change work

No structural change is required in `backend-change-delta.md` because it already routes change work through either `backend-design-core.md` or `backend-implementation-core.md`.

If maintainers want the skill to be explicitly visible in change instructions too, add one short sentence to `playbook/process/read-sets/backend-change-delta.md` saying that SAFRS-backed DB API changes must also load `skills/safrs-api-design/SKILL.md` through the selected stage-specific read set.

## 3. Load it for the Architect where exceptions are approved

Recommended reads to update:

- `playbook/process/read-sets/architect-authoring-core.md`
- `playbook/process/read-sets/architect-review-core.md`

Suggested line:

- `../../../skills/safrs-api-design/SKILL.md`

Why:

- the Architect owns integration boundaries and exception approval
- the Architect review phase is where custom endpoint substitutions should be rejected before delivery

## 4. Mention the skill in the role files that already carry the policy intent

### Backend role

Update `playbook/roles/backend.md`.

There is already a rule telling Backend to review SAFRS docs and local examples for `jsonapi_attr` and `jsonapi_rpc` before inventing a workaround.
Strengthen that section so it says the backend role must load and apply `skills/safrs-api-design/SKILL.md` whenever a DB-backed resource, relationship, computed field, or custom endpoint decision is in scope.

Add one blunt sentence like this:

> For DB-backed API design in a SAFRS-based app, the backend role MUST use `skills/safrs-api-design/SKILL.md` before approving any custom endpoint that could replace a normal SAFRS resource, relationship, include path, `jsonapi_attr`, or `jsonapi_rpc` lane.

### Architect role

Update `playbook/roles/architect.md`.

Add one sentence near the existing SAFRS integration-boundary rule:

> When approving a non-SAFRS or non-relationship lane for persisted DB-backed data, the Architect MUST require the SAFRS lane analysis defined by `skills/safrs-api-design/SKILL.md` and a completed exception record.

## 5. Strengthen the contract language so the skill is not optional advice

### Backend data sourcing contract

Update `specs/contracts/backend/data-sourcing.md`.

Keep the existing default lane statement, but add:

- custom endpoints may supplement but must not replace canonical SAFRS resource and relationship surfaces for ordinary DB-backed data
- authors must use the SAFRS skill before inventing an alternative lane
- every exception must explain why the need is not satisfied by resource, relationship, include, `jsonapi_attr`, or `jsonapi_rpc`

### Backend validation contract

Update `specs/contracts/backend/validation.md`.

Add explicit validation expectations for:

- relationship route proof
- include-path proof
- `jsonapi_attr` proof when used
- `jsonapi_rpc` proof when used
- exception-record proof for custom DB-backed endpoints

### Quality gates

`playbook/process/quality-gates.md` already blocks replacing ordinary SAFRS resources or relationships with custom summary endpoints.
Do not move that rule into the skill.
Instead, add a requirement that the quality evidence pack include the SAFRS lane audit or reference the exception record when a custom DB-backed endpoint is present.

## 6. Tie the skill to run-owned artifacts

The skill becomes much more effective if the normal backend-design artifacts force authors to record the SAFRS lane explicitly.

Recommended artifact changes:

### `backend-design/model-design.md`

Add fields for:

- real SAFRS model
- ORM relationship names
- `jsonapi_attr` list
- `jsonapi_rpc` list
- exception reference

### `backend-design/resource-exposure-policy.md`

Add fields for:

- canonical SAFRS resource path
- supplemental custom endpoints
- why standard SAFRS is insufficient

### `backend-design/relationship-map.md`

Add fields for:

- canonical relationship URL
- canonical include path
- relationship visibility
- relationship item mode
- replacement contract when not exposed

### `backend-design/query-behavior.md`

Require every include path to reference a declared ORM relationship chain.

### `backend-design/test-plan.md`

Require live proof and test proof for:

- relationship routes
- include paths
- `jsonapi_attr`
- `jsonapi_rpc`
- any approved exception lane

## 7. Extend policy enforcement

Right now the policy file `specs/policy/requirements/backend-core.yaml` has one broad SAFRS/ORM rule.
Keep that rule, but add narrower rules so the checker can fail more precise cases.

Recommended additions:

- DB-backed relationships use real ORM + SAFRS relationship exposure by default
- custom DB-backed endpoints require an exception record
- required include paths must map to real ORM relationships
- frontend must not depend on a custom DB relationship endpoint when the canonical SAFRS relation exists

## 8. Keep the frontend contract aligned

The backend skill will not be enough if the frontend contract still nudges authors toward FK-first reads.

Recommended contract edits:

- keep scalar FK values as write convenience if needed
- make relational reads prefer `include=...` and relationship endpoints
- allow fallback `getOne` by related id only as fallback, not as the primary relationship model
- forbid inventing custom endpoints just to show related DB data on a page that already has a parent resource

## 9. Minimal integration plan if maintainers want the smallest safe change

If you want the smallest change that still matters, do exactly this:

1. add `skills/safrs-api-design/`
2. add `../../../skills/safrs-api-design/SKILL.md` to:
   - `backend-design-core.md`
   - `backend-implementation-core.md`
   - `architect-authoring-core.md`
   - `architect-review-core.md`
3. update `playbook/roles/backend.md` and `playbook/roles/architect.md` to require the skill for DB-backed API-lane decisions
4. update `specs/contracts/backend/data-sourcing.md` so the skill is mandatory before a custom DB-backed endpoint is approved
5. update `specs/contracts/backend/validation.md` so relationship/include/attr/rpc proof is required

That is enough to turn the skill from optional repo decoration into part of the actual playbook path.
