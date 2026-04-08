# Phase 4 - Backend Design And Rules Mapping

Lead: Backend

## Goal

Map the domain contract into backend models, SAFRS exposure, rules, lifecycle,
and tests.

## Activities

- start from the Product Manager resource inventory and resource behavior
  matrix, user stories, and traceability matrix, not only the glossary and
  rule narrative
- verify that journey-critical transitions, validations, and recovery paths
  have backend support and use journey IDs when reviewing rule and event
  coverage for approval, exception, or multi-step flows
- map conceptual business concepts, relationships, lifecycle models, and
  business events to backend structures explicitly
- record every non-1:1 mapping between conceptual concepts and backend
  models/resources
- distinguish business events from implementation choices such as rule
  triggers, audit rows, RPCs, or integration events
- classify which product concepts become exposed SAFRS resources
- treat persisted database-backed product or operator concepts as SAFRS
  resources by default unless an explicit documented exception applies
- run the SAFRS decision tree for every new data need:
  - persisted row data => SAFRS resource
  - DB relationship => ORM relationship plus SAFRS relationship URL/include
  - derived resource field => `jsonapi_attr`
  - explicit action => `jsonapi_rpc`
  - anything else => documented exception such as `JABase`
- define which concepts remain internal, singleton/settings-style, deferred,
  or explicitly omitted
- design SQLAlchemy models and relationships
- treat mapped SQLAlchemy ORM models and relationships as the default
  implementation lane for persisted DB-backed resources
- define which relationships must be exposed through SAFRS for
  list/show/include/filter/drill-down behavior
- define per-resource readonly and mutability policy
- map approved rule IDs to LogicBank patterns, backend enforcement, and tests
- classify each approved requirement as schema constraint, transactional rule,
  or transport concern before choosing a rule lane
- evaluate each approved rule ID against `Rule.copy`, `Rule.formula`,
  `Rule.sum`, `Rule.count`, `Rule.constraint`, and declarative chaining before
  approving advanced/custom alternatives
- default ambiguous parent/reference propagation to `Rule.copy` unless live
  propagation is explicitly required
- if the requirement implies request/audit rows or response-bearing wrapper
  semantics, load `skills/logicbank-request-pattern/SKILL.md`
- if the requirement implies allocate/distribute/split behavior, load
  `skills/logicbank-allocation/SKILL.md`
- define derived vs stored fields
- define per-resource query commitments
- define any backend read-model, aggregate, or metadata endpoints required by
  the approved UI data-sourcing contract
- define bootstrap/seed behavior
- define startup order
- define backend test scenarios
- confirm query features relied upon by the frontend
- confirm non-starter substitutions before implementation starts

## Outputs

- `runs/current/artifacts/backend-design/model-design.md`
- `runs/current/artifacts/backend-design/relationship-map.md`
- `runs/current/artifacts/backend-design/rule-mapping.md`
- `runs/current/artifacts/backend-design/bootstrap-strategy.md`
- `runs/current/artifacts/backend-design/resource-exposure-policy.md`
- `runs/current/artifacts/backend-design/query-behavior.md`
- `runs/current/artifacts/backend-design/test-plan.md`

## Exit criteria

- every PM resource is classified as exposed, internal, singleton/settings,
  deferred, or omitted
- concept-to-model mapping is explicit wherever the mapping is not 1:1
- every exposed resource has an explicit mutability policy
- every approved rule ID maps to backend implementation and backend tests
- every approved rule ID records the chosen LogicBank lane or justified
  exception before coding starts
- backend design decisions do not have to guess about workflow depth because
  `user-stories.md` and `traceability-matrix.md` already record scenario,
  permission, and acceptance context
- journey-critical approval, exception, and recovery paths have explicit
  backend support and are not left as UX-only assumptions
- every derived persisted field records any schema prerequisite, migration, or
  backfill plan before coding starts
- every frontend-visible field maps to backend truth
- every frontend-needed query behavior is either committed or explicitly out
  of scope
- every approved API-backed UI surface has a backend delivery lane instead of
  a frontend hardcoded-data fallback
- every appropriate DB-backed table and relationship has a SAFRS exposure
  decision, and any non-SAFRS exception is explicitly justified
- every custom endpoint proposal records why ordinary SAFRS resource,
  relationship, include, `jsonapi_attr`, or `jsonapi_rpc` did not fit
- every appropriate DB-backed table and relationship has an ORM implementation
  decision, and any raw-SQL or non-ORM exception is explicitly justified
- no ambiguous lifecycle behavior remains
- every required non-starter template replacement is identified before
  implementation starts
- the `runs/current/artifacts/backend-design/` package is marked
  `ready-for-handoff` or `approved`
