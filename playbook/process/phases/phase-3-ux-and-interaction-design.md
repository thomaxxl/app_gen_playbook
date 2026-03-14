# Phase 3 - UX And Interaction Design

Lead: UX/UI + Frontend

## Goal

Design the user journey and page behavior before implementation diverges.

## Activities

- create screen inventory
- define navigation/menu structure
- define default entry, return-path, and page-header behavior
- define per-resource CRUD layouts
- define form grouping, content clarity, and field-level guidance
- define loading/error/empty states
- define success and destructive-confirmation behavior
- define responsive expectations and mobile fallbacks
- define accessibility-visible behavior and any higher-risk accessibility notes
- define custom-page behavior
- define relationship display patterns
- define any approved frontend validation mirrors and trace them to business
  rule IDs

## Outputs

- `runs/current/artifacts/ux/navigation.md`
- `runs/current/artifacts/ux/screen-inventory.md`
- `runs/current/artifacts/ux/field-visibility-matrix.md`
- `runs/current/artifacts/ux/custom-view-specs.md`
- `runs/current/artifacts/ux/state-handling.md`

## Exit criteria

- the UX package is traceable to the product artifacts it implements
- loading, empty, error, success, and recovery behavior are documented for the
  critical paths
- page-shell, page-header, and primary CTA decisions are documented for the
  main routes
- responsive behavior is documented for the critical flows
- accessibility baseline expectations and any non-default route-level notes are
  documented
- any mirrored frontend validation is traceable to approved business-rule IDs
- architect signs off on boundary compliance
- backend understands frontend data needs
- the `runs/current/artifacts/ux/` package is marked `ready-for-handoff` or
  `approved`
