# Phase 4 - Backend Design And Rules Mapping

Lead: Backend

## Goal

Map the domain contract into backend models, rules, lifecycle, and tests.

## Activities

- design SQLAlchemy models and relationships
- map plain-language rules to LogicBank patterns
- define derived vs stored fields
- define bootstrap/seed behavior
- define startup order
- define backend test scenarios
- confirm query features relied upon by the frontend

## Outputs

- `runs/current/artifacts/backend-design/model-design.md`
- `runs/current/artifacts/backend-design/relationship-map.md`
- `runs/current/artifacts/backend-design/rule-mapping.md`
- `runs/current/artifacts/backend-design/bootstrap-strategy.md`
- `runs/current/artifacts/backend-design/test-plan.md`

## Exit criteria

- every product rule maps to a backend implementation pattern
- every frontend-visible field maps to backend truth
- no ambiguous lifecycle behavior remains
- the `runs/current/artifacts/backend-design/` package is marked
  `ready-for-handoff` or `approved`
