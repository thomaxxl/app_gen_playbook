# Frontend Templates

These snippets correspond to:

- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)
- [../../../README.md](../../../README.md)
- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)

They show the canonical starter frontend shape for the starter app:

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
7. `theme.ts.md`
8. `vite-env.d.ts.md`
9. `main.tsx.md`
10. `PageHero.tsx.md`
11. `PageHeader.tsx.md`
12. `EmptyState.tsx.md`
13. `ErrorState.tsx.md`
14. `FormSection.tsx.md`
15. `SectionBlock.tsx.md`
16. `QuickActionCard.tsx.md`
17. `SummaryCard.tsx.md`
18. `SchemaDrivenAdminApp.tsx.md`
19. `shared-runtime/admin/schemaContext.tsx.md`
20. `shared-runtime/admin/resourceMetadata.ts.md`
21. `shared-runtime/relationshipUi.tsx.md`
22. `shared-runtime/admin/createSearchEnabledDataProvider.ts.md`
23. `shared-runtime/resourceRegistry.tsx.md`
24. `generated/resources/Collection.tsx.md`
25. `generated/resources/Item.tsx.md`
26. `generated/resources/Status.tsx.md`
27. `resourcePages.ts.md`
28. `App.tsx.md`
29. `Home.tsx.md`
30. `Landing.tsx.md` only when the run explicitly enables a starter no-layout page
31. `CustomDashboard.tsx.md` when the app needs a non-starter custom page
32. `D3Visualization.tsx.md` if the app needs charts or figures
33. `shared-runtime/files/README.md`
34. `shared-runtime/files/uploadAwareDataProvider.ts.md`
35. `shared-runtime/files/fileValueAdapters.ts.md`
36. `shared-runtime/files/fileFieldHelpers.ts.md`
37. `fs-promises.ts.md`
38. `vite.config.ts.md`
39. `vitest.config.ts.md`
40. `playwright.config.ts.md`
41. `tests/SchemaDrivenAdminApp.smoke.test.tsx.md`
42. `tests/schemaContext.test.ts.md`
43. `tests/dataProvider.integration.test.ts.md`
44. `tests/resourceMetadata.test.ts.md`
45. `tests/createSearchEnabledDataProvider.test.ts.md`
46. `tests/uploadAwareDataProvider.test.ts.md` if the app supports uploads
47. `tests/vite.config.test.ts.md`
48. `tests/smoke.e2e.spec.ts.md`
49. `../project/run.sh.md`
50. `../project/README.app.md`

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
- `theme.ts.md`, `PageHero.tsx.md`, `PageHeader.tsx.md`, `EmptyState.tsx.md`,
  `ErrorState.tsx.md`, `FormSection.tsx.md`, `SectionBlock.tsx.md`,
  `QuickActionCard.tsx.md`, and `SummaryCard.tsx.md` define the starter UI
  shell. Generated pages SHOULD reuse them unless the run-owned UX artifacts
  explicitly require a different shell.
- `Home.tsx.md` is now the primary entry-page scaffold. It MUST implement the
  run-owned `landing-strategy.md` artifact rather than remaining a thin
  placeholder.
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
- `tests/dataProvider.integration.test.ts.md` is part of the baseline data
  loading contract because the frontend MUST prove more than bootstrap: it
  MUST show that the real provider path preserves row data.
- For non-starter domains, `CustomDashboard.tsx.md` SHOULD be the default
  custom-page starting point. `Landing.tsx.md` remains the starter-domain
  example.
- The upload helper files under `shared-runtime/files/` are part of the
  baseline shared runtime. They MUST remain present even when the app has no
  upload fields so `schemaContext.tsx` can import them safely.
- If the app supports uploads, the upload-aware provider unit test MUST also
  be added to the generated frontend test suite.
