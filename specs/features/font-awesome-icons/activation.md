# Font Awesome Icons Activation

Enable `font-awesome-icons` only when the run explicitly chooses Font Awesome
as the visible app-facing icon family.

Activation requirements:

- `runs/current/artifacts/ux/iconography.md` MUST exist and name Font Awesome
  as the approved icon system
- the Architect MUST mark the capability as `enabled` in
  `runs/current/artifacts/architecture/capability-profile.md`
- the Architect MUST list this pack in the Frontend role section of
  `runs/current/artifacts/architecture/load-plan.md`

When enabled:

- the frontend MUST route visible app-facing icon usage through `AppIcon`
- starter templates MUST NOT add new direct icon-family imports for entry-page,
  sidebar, CTA, summary-card, or quick-action surfaces

Transitional note:

- direct `@mui/icons-material` usage MAY remain in internal starter files only
  if the run-owned `iconography.md` explicitly records that exception
