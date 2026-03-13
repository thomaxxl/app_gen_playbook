owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/custom-pages.md
unresolved:
  - replace with run-specific custom views
last_updated_by: playbook

# Custom View Specs Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/custom-view-specs.md`.

The real artifact MUST define:

- landing or dashboard routes
- data requirements
- interaction requirements
- layout expectations

If the app needs a landing page that joins several resources and resolves
multiple references to the same target type, use
`../architecture/nonstarter-worked-example.md` as the baseline example.
