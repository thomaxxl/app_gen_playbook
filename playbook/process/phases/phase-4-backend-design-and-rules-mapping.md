# Phase 4 - Backend Design And Rules Mapping

Lead: Backend

## Goal

Map the domain contract into backend models, SAFRS exposure, rules, lifecycle,
and tests.

## Activities

- start from the Product Manager resource inventory and resource behavior
  matrix, not only the glossary and rule narrative
- classify which product concepts become exposed SAFRS resources
- treat persisted database-backed product or operator concepts as SAFRS
  resources by default unless an explicit documented exception applies
- define which concepts remain internal, singleton/settings-style, deferred,
  or explicitly omitted
- design SQLAlchemy models and relationships
- define which relationships must be exposed through SAFRS for
  list/show/include/filter/drill-down behavior
- define per-resource readonly and mutability policy
- map approved rule IDs to LogicBank patterns, backend enforcement, and tests
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
- every exposed resource has an explicit mutability policy
- every approved rule ID maps to backend implementation and backend tests
- every frontend-visible field maps to backend truth
- every frontend-needed query behavior is either committed or explicitly out
  of scope
- every approved API-backed UI surface has a backend delivery lane instead of
  a frontend hardcoded-data fallback
- every appropriate DB-backed table and relationship has a SAFRS exposure
  decision, and any non-SAFRS exception is explicitly justified
- no ambiguous lifecycle behavior remains
- every required non-starter template replacement is identified before
  implementation starts
- the `runs/current/artifacts/backend-design/` package is marked
  `ready-for-handoff` or `approved`
