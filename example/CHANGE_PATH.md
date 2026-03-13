# SPA Path Change Notes

Status: historical note only. The current airport app and playbook now use
`/admin-app/` again as the active SPA base path.

This note captures the concrete work needed to change the generated frontend
path from `/admin-app/` to `/spa/`.

## App Changes Implemented

The generated app was updated in these places:

- [app/frontend/vite.config.ts](frontend/vite.config.ts)
  Changes:
  - Vite `base` changed from `/admin-app/` to `/spa/`.
  - The dev-server rewrite middleware now maps `/spa` and `/spa/*` back to the
    Vite root during development and preview.
  - The helper name was renamed from `adminAppDevBase` to `spaDevBase` so the
    code does not preserve stale semantics.
- [app/frontend/playwright.config.ts](frontend/playwright.config.ts)
  Changes:
  - The web-server readiness URL changed to `http://127.0.0.1:5173/spa/`.
- [app/frontend/tests/smoke.e2e.spec.ts](frontend/tests/smoke.e2e.spec.ts)
  Changes:
  - Browser navigation changed from `/admin-app/#/...` to `/spa/#/...`.
- [app/frontend/tests/vite.config.test.ts](frontend/tests/vite.config.test.ts)
  Changes:
  - The expected Vite base path changed to `/spa/`.
- [app/run.sh](run.sh)
  Changes:
  - The printed frontend and landing URLs now point to `/spa/`.
- [app/README.md](README.md)
  Changes:
  - User-facing URLs now point to `/spa/`.
  - The description of preview mode now explains `/spa/` instead of
    `/admin-app/`.

## App Regeneration Side Effects

Changing the canonical SPA path also changes generated artifacts:

- `app/frontend/vite.config.js`
- `app/frontend/playwright.config.js`
- `app/frontend/dist/index.html`
- built asset URLs under `app/frontend/dist/assets/`

Those files should not be hand-edited. Rebuild the frontend after changing the
TypeScript sources.

## Verification Needed After The Change

These checks should be rerun any time the SPA base path changes:

1. `npm run test` in `app/frontend`
2. `npm run build` in `app/frontend`
3. `npm run test:e2e` in `app/frontend`
4. manual spot-check:
   - `/spa/`
   - `/spa/#/Landing`
   - `/spa/#/Gate`
   - `/ui/admin/admin.yaml`

## one_shot_gen Playbook Updates Still Needed

The playbook currently hardcodes `/admin-app/` in many places. To make `/spa/`
the new canonical path, these source documents should be updated.

### Architecture Contracts

- [specs/architecture/README.md](../specs/architecture/README.md)
- [specs/architecture/overview.md](../specs/architecture/overview.md)
- [specs/architecture/route-and-entry-model.md](../specs/architecture/route-and-entry-model.md)
- [specs/architecture/test-obligations.md](../specs/architecture/test-obligations.md)
- [specs/architecture/decision-log.md](../specs/architecture/decision-log.md)
- [runs/current/role-state/architect/context.md](../runs/current/role-state/architect/context.md)

Required change:
- Replace `/admin-app/` with `/spa/`.
- Replace `/admin-app/#/Landing` with `/spa/#/Landing`.
- Replace any resource examples like `/admin-app/#/Gate` with `/spa/#/Gate`.
- Update any statements that call `/admin-app/` the canonical or only allowed
  SPA base path.

### Product And UX Artifacts

- [specs/product/workflows.md](../specs/product/workflows.md)
- [specs/product/custom-pages.md](../specs/product/custom-pages.md)
- [specs/product/acceptance-criteria.md](../specs/product/acceptance-criteria.md)
- [specs/product/acceptance-review.md](../specs/product/acceptance-review.md)
- [specs/ux/navigation.md](../specs/ux/navigation.md)

Required change:
- Update the documented user entry path to `/spa/#/Landing`.
- Update acceptance wording and navigation examples to use `/spa/`.

### Frontend Contracts

- [specs/contracts/frontend/routing-and-paths.md](../specs/contracts/frontend/routing-and-paths.md)
- [specs/contracts/frontend/build-and-deploy.md](../specs/contracts/frontend/build-and-deploy.md)
- [specs/contracts/frontend/validation.md](../specs/contracts/frontend/validation.md)
- [specs/contracts/frontend/custom-views.md](../specs/contracts/frontend/custom-views.md)
- [specs/contracts/frontend/dependencies.md](../specs/contracts/frontend/dependencies.md)

Required change:
- Replace the Vite `base` examples with `/spa/`.
- Replace build and deploy examples from `/admin-app/assets/...` to
  `/spa/assets/...`.
- Replace validation steps so the browser opens `/spa/` and `/spa/#/Landing`.
- Replace any proxy, same-origin, or smoke-test assumptions that explicitly say
  `/admin-app/`.

### Templates

- [templates/app/frontend/vite.config.ts.md](../templates/app/frontend/vite.config.ts.md)
- [templates/app/frontend/tests/vite.config.test.ts.md](../templates/app/frontend/tests/vite.config.test.ts.md)
- [templates/app/frontend/tests/smoke.e2e.spec.ts.md](../templates/app/frontend/tests/smoke.e2e.spec.ts.md)
- [templates/app/frontend/playwright.config.ts.md](../templates/app/frontend/playwright.config.ts.md)
- [templates/app/frontend/config.ts.md](../templates/app/frontend/config.ts.md)
- [templates/app/frontend/Landing.tsx.md](../templates/app/frontend/Landing.tsx.md)
- [templates/app/project/README.app.md](../templates/app/project/README.app.md)
- [templates/app/project/run.sh.md](../templates/app/project/run.sh.md)
- [specs/architecture/domain-adaptation-template.md](../specs/architecture/domain-adaptation-template.md)
- [templates/app/backend/run_with_spa.py.md](../templates/app/backend/run_with_spa.py.md)

Required change:
- Update the generated base path, rewrite middleware, test expectations, README
  examples, and launcher output to `/spa/`.
- In the backend SPA-mount template, change redirects, mounts, and route
  decorators from `/admin-app` and `/admin-app/assets` to `/spa` and
  `/spa/assets`.

### Docker And Same-Origin Packaging Docs

- [specs/contracts/deployment/README.md](../specs/contracts/deployment/README.md)
- [templates/app/deployment/README.md](../templates/app/deployment/README.md)
- [templates/app/deployment/nginx.conf.md](../templates/app/deployment/nginx.conf.md)

Required change:
- Change nginx redirects and SPA locations from `/admin-app/` to `/spa/`.
- Change packaged asset paths from `/admin-app/assets/` to `/spa/assets/`.
- Change root redirect guidance from `/admin-app/` to `/spa/`.

## Recommended Playbook Improvement

The playbook should stop hardcoding the SPA path across many files.

Recommended approach:

- Introduce one canonical variable such as `SPA_BASE_PATH=/spa/`.
- Reference that variable in architecture docs, frontend contracts, templates,
  Docker examples, Playwright snippets, and generated project docs.
- Keep a single validation checklist that derives all examples from the same
  base path instead of repeating literal strings in multiple documents.

Without that change, future path updates will continue to require a broad,
error-prone search-and-replace across contracts, templates, tests, and deploy
docs.
