# Frontend Non-Starter Checklist

Use this checklist when the Architect classifies the run as `rename-only` or
`non-starter`.

The Frontend role MUST use this checklist before treating the starter frontend
templates as sufficient.

## Required checks

- replace starter resource wrapper files with one wrapper per resource named
  in `runs/current/artifacts/architecture/resource-naming.md`
- rebuild `frontend/src/generated/resourcePages.ts` from the run-owned naming
  artifact instead of keeping the starter trio
- remove the starter `Landing.tsx` route unless
  `runs/current/artifacts/ux/custom-view-specs.md` explicitly requires a
  no-layout page
- remove starter `Home.tsx` CTA assumptions and replace them with
  app-specific primary navigation actions
- replace starter smoke assertions and seeded data expectations with
  app-specific routes and records
- verify custom pages against:
  - `runs/current/artifacts/ux/custom-view-specs.md`
  - `runs/current/artifacts/ux/navigation.md`
  - `runs/current/artifacts/ux/screen-inventory.md`
- confirm any singleton or settings concept follows
  `runs/current/artifacts/architecture/resource-classification.md`
- confirm any reference-only resource menu behavior follows
  `runs/current/artifacts/product/resource-behavior-matrix.md`

## Completion rule

The Frontend role MUST NOT declare the frontend starter templates "good
enough" for a non-starter run until every applicable checklist item is either:

- completed, or
- explicitly rejected with a reason recorded in the run-owned UX artifacts
