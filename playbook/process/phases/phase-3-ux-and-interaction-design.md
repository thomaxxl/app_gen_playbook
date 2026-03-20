# Phase 3 - UX And Interaction Design

Lead: UX/UI + Frontend

## Goal

Design the user journey and page behavior before implementation diverges.

## Activities

- create screen inventory
- define navigation/menu structure
- define landing strategy and primary entry CTA hierarchy
- define the hero/landing treatment that appears before any resource-grid
  content on the primary entry surface
- define default entry, return-path, and page-header behavior
- define per-resource CRUD layouts
- define form grouping, content clarity, and field-level guidance
- define loading/error/empty states
- define success and destructive-confirmation behavior
- define responsive expectations and mobile fallbacks only if the run
  explicitly chooses to care about mobile; otherwise mobile may be ignored for
  now
- define accessibility-visible behavior and any higher-risk accessibility notes
- define custom-page behavior
- define relationship display patterns
- define which screen and custom-view data is API-driven versus static UI
  configuration
- define any approved frontend validation mirrors and trace them to business
  rule IDs

## Outputs

- `runs/current/artifacts/ux/navigation.md`
- `runs/current/artifacts/ux/landing-strategy.md`
- `runs/current/artifacts/ux/iconography.md`
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
- the primary entry route, entry-page proof cues, and CTA hierarchy are
  documented in `landing-strategy.md`
- the entry strategy explicitly defines a hero/landing surface instead of
  defaulting to a raw React-admin grid as the first impression
- the visible icon system and icon mapping decisions are documented in
  `iconography.md` even when the run keeps the default icon wrapper behavior
- responsive/mobile behavior is documented only when the run explicitly keeps
  mobile in scope; otherwise mobile may be ignored and is non-blocking
- accessibility baseline expectations and any non-default route-level notes are
  documented
- any mirrored frontend validation is traceable to approved business-rule IDs
- architect signs off on boundary compliance
- backend understands frontend data needs
- screen and custom-view specs explicitly identify which user-visible data must
  come from the API
- the `runs/current/artifacts/ux/` package is marked `ready-for-handoff` or
  `approved`
