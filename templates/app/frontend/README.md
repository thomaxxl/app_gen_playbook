# Frontend Templates

These snippets correspond to:

- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)
- [../../../README.md](../../../README.md)
- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)

They show the canonical thin frontend shape for the starter app:

- app-local shell files stay small
- shared schema-driven behavior lives in `src/shared-runtime/`
- resources are explicit even when the internals are schema-driven
- D3 stays in focused visualization components instead of the admin shell
- each template corresponds to one concrete target file; cross-file wiring
  belongs in the dedicated file that owns it

All target paths are relative to the generated app root:

- `app/frontend/`

Suggested copy order:

1. `index.html.md`
2. `package.json.md`
3. `tsconfig.json.md`
4. `tsconfig.app.json.md`
5. `tsconfig.node.json.md`
6. `config.ts.md`
7. `vite-env.d.ts.md`
8. `main.tsx.md`
9. `SchemaDrivenAdminApp.tsx.md`
10. `shared-runtime/admin/schemaContext.tsx.md`
11. `shared-runtime/admin/resourceMetadata.ts.md`
12. `shared-runtime/relationshipUi.tsx.md`
13. `shared-runtime/admin/createSearchEnabledDataProvider.ts.md`
14. `shared-runtime/resourceRegistry.tsx.md`
15. `generated/resources/Collection.tsx.md`
16. `generated/resources/Item.tsx.md`
17. `generated/resources/Status.tsx.md`
18. `resourcePages.ts.md`
19. `App.tsx.md`
20. `Home.tsx.md`
21. `Landing.tsx.md` only when the run explicitly enables a starter no-layout page
22. `CustomDashboard.tsx.md` when the app needs a non-starter custom page
23. `D3Visualization.tsx.md` if the app needs charts or figures
24. `shared-runtime/files/README.md`
25. `shared-runtime/files/uploadAwareDataProvider.ts.md`
26. `shared-runtime/files/fileValueAdapters.ts.md`
27. `shared-runtime/files/fileFieldHelpers.ts.md`
28. `fs-promises.ts.md`
29. `vite.config.ts.md`
30. `vitest.config.ts.md`
31. `playwright.config.ts.md`
32. `tests/SchemaDrivenAdminApp.smoke.test.tsx.md`
33. `tests/schemaContext.test.ts.md`
34. `tests/resourceMetadata.test.ts.md`
35. `tests/createSearchEnabledDataProvider.test.ts.md`
36. `tests/uploadAwareDataProvider.test.ts.md` if the app supports uploads
37. `tests/vite.config.test.ts.md`
38. `tests/smoke.e2e.spec.ts.md`
39. `../project/run.sh.md`
40. `../project/README.app.md`

Implementation entrypoint reads:

- before Phase 5 implementation, read `../../README.md`
- read `../../../playbook/process/frontend-nonstarter-checklist.md` when the
  run is `rename-only` or `non-starter`
- read the enabled feature-template README entrypoints before copying any
  feature-owned template files

Notes:

- For non-starter domains, the three starter wrapper files are examples, not a
  fixed universal file list. The implementation MUST create one wrapper file
  per resource declared in
  `../../../runs/current/artifacts/architecture/resource-naming.md`.
- `resourcePages.ts.md` MUST register the actual resource wrapper set for the
  current app, not the starter trio by default.
- For non-starter domains, the Frontend role MUST apply
  `../../../playbook/process/frontend-nonstarter-checklist.md` before treating
  the starter frontend templates as sufficient.
- `Home.tsx.md` is required for every generated app. It is the standard
  sidebar-visible in-admin landing page.
- `shared-runtime/relationshipUi.tsx.md` is part of the baseline runtime. It
  defines the Northwind-style foreign-key display, relationship dialog, and
  show-tab behavior that generated pages MUST reuse.
- `shared-runtime/admin/resourceMetadata.ts.md` MUST synthesize usable
  relationship metadata even when the normalized schema is partial.
- `shared-runtime/resourceRegistry.tsx.md` MUST also implement responsive form
  layout heuristics so generated create/edit pages do not default to one
  full-width input per row.
- the default generated form should visually resemble a typical admin form:
  mostly three standard fields per row, with compact scalar fields narrower
  and multiline fields full-width.
- `tests/resourceMetadata.test.ts.md` and `tests/schemaContext.test.ts.md`
  are part of the baseline relationship contract because sparse-schema apps
  must prove tab-group preservation and relationship fallback behavior.
- For non-starter domains, `CustomDashboard.tsx.md` SHOULD be the default
  custom-page starting point. `Landing.tsx.md` remains the starter-domain
  example.
- The upload helper files under `shared-runtime/files/` are part of the
  baseline shared runtime. They MUST remain present even when the app has no
  upload fields so `schemaContext.tsx` can import them safely.
- If the app supports uploads, the upload-aware provider unit test MUST also
  be added to the generated frontend test suite.
