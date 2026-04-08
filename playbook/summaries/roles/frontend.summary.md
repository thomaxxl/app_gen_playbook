# Frontend Role Summary

Use this role for UX artifacts, frontend implementation, runtime wiring,
React-admin resource registration, entry-page behavior, relationship UI, and
frontend validation, including preview screenshot capture plus Frontend
signoff on screenshot content.

That includes run-owned visual-direction work and draft/mockup flow critique,
not just page wiring. Frontend is expected to recommend an appropriate visual
scheme for the app and to critique weak draft flow choices such as poor menu
placement, weak CTA sizing, or bad form arrangement before implementation
locks them in.

Always load:

- `global-core.md`
- `process-core.md`
- one stage-specific Frontend read set:
  - `../../process/read-sets/frontend-design-core.md`
  - `../../process/read-sets/frontend-implementation-core.md`
  - `../../process/read-sets/frontend-change-delta.md`

This role controls UX artifacts and frontend code. It does not invent product
rules, backend semantics, or packaging policy.

It is also responsible for compiling the run-owned UX artifacts into the
executable frontend view model at `app/frontend/src/generated/uxModel.ts`.

For database-driven MUI layout and related-data decisions, load:

- `../../../skills/mui-db-admin-ux/SKILL.md`

Load backend or feature-pack material only when the current task requires it
and the load plan allows it.

Full docs:

- `../../roles/frontend.md`
- `../../../specs/contracts/frontend/README.md`
