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
10. `AppIcon.tsx.md`
11. `PageHero.tsx.md`
12. `PageHeader.tsx.md`
13. `EmptyState.tsx.md`
14. `ErrorState.tsx.md`
15. `FormSection.tsx.md`
16. `SectionBlock.tsx.md`
17. `QuickActionCard.tsx.md`
18. `SummaryCard.tsx.md`
19. `SchemaDrivenAdminApp.tsx.md`
20. `shared-runtime/admin/schemaContext.tsx.md`
21. `shared-runtime/admin/resourceMetadata.ts.md`
22. `shared-runtime/relationshipUi.tsx.md`
23. `shared-runtime/admin/createSearchEnabledDataProvider.ts.md`
24. `shared-runtime/resourceRegistry.tsx.md`
25. `observerRouteContracts.ts.md`
26. `ObserverPages.tsx.md`
27. `resourcePages.ts.md`
28. `App.tsx.md`
29. `Home.tsx.md`
30. `generated/resources/Collection.tsx.md` only for starter-style resource wrappers
31. `generated/resources/Item.tsx.md` only for starter-style resource wrappers
32. `generated/resources/Status.tsx.md` only for starter-style resource wrappers
33. `Landing.tsx.md` only when the run explicitly enables a starter no-layout page
34. `CustomDashboard.tsx.md` when the app needs a non-starter custom page
35. `D3Visualization.tsx.md` if the app needs charts or figures
36. `shared-runtime/files/README.md`
37. `shared-runtime/files/uploadAwareDataProvider.ts.md`
38. `shared-runtime/files/fileValueAdapters.ts.md`
39. `shared-runtime/files/fileFieldHelpers.ts.md`
40. `fs-promises.ts.md`
41. `vite.config.ts.md`
42. `vitest.config.ts.md`
43. `playwright.config.ts.md`
44. `tests/SchemaDrivenAdminApp.smoke.test.tsx.md`
45. `tests/schemaContext.test.ts.md`
46. `tests/dataProvider.integration.test.ts.md`
47. `tests/resourceMetadata.test.ts.md`
48. `tests/createSearchEnabledDataProvider.test.ts.md`
49. `tests/uploadAwareDataProvider.test.ts.md` if the app supports uploads
50. `tests/vite.config.test.ts.md`
51. `tests/smoke.e2e.spec.ts.md`
52. `tests/ui-previews.e2e.spec.ts.md`
53. `tests/qa-screenshots.e2e.spec.ts.md`
54. `../project/run.sh.md`
55. `../project/README.app.md`

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
  `../../../runs/current/artifacts/architecture/resource-naming.md`, or use an
  explicit observer-resource registry such as `observerRouteContracts.ts.md`
  when the app is a run observer over `run_dashboard`.
- `resourcePages.ts.md` MUST register the actual resource wrapper set for the
  current app, not the starter trio by default.
- For non-starter domains, the Frontend role MUST apply
  `../../../playbook/process/frontend-nonstarter-checklist.md` before treating
  the starter frontend templates as sufficient.
- `Home.tsx.md` is required for every generated app. It is the standard
  sidebar-visible in-admin landing page.
- `theme.ts.md`, `PageHero.tsx.md`, `PageHeader.tsx.md`, `EmptyState.tsx.md`,
  `ErrorState.tsx.md`, `FormSection.tsx.md`, `SectionBlock.tsx.md`,
  `QuickActionCard.tsx.md`, `SummaryCard.tsx.md`, and `AppIcon.tsx.md` define
  the starter UI shell. Generated pages SHOULD reuse them unless the
  run-owned UX artifacts explicitly require a different shell.
- `AppIcon.tsx.md` is the visible icon wrapper swap point. When
  `font-awesome-icons` is enabled, the Frontend role SHOULD adapt that wrapper
  instead of hard-coding a second icon-family path in each page template.
- `Home.tsx.md` is now the primary entry-page scaffold. It MUST implement the
  run-owned `landing-strategy.md` artifact rather than remaining a thin
  placeholder.
- Delivered `Home`, custom pages, and generated resource routes MUST read as
  usable product surfaces. They MUST NOT ship as contract/recovery/debug
  viewers that expose internal integration state to end users.
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
- when the app needs large formatted prose blocks, the frontend SHOULD use
  `react-markdown` rather than injected HTML. Keep secure defaults: no raw
  HTML parsing, no `rehype-raw`, and explicit safe external-link handling.
- `tests/resourceMetadata.test.ts.md` and `tests/schemaContext.test.ts.md`
  are part of the baseline relationship contract because sparse-schema apps
  must prove tab-group preservation and relationship fallback behavior.
- `tests/dataProvider.integration.test.ts.md` is part of the baseline data
  loading contract because the frontend MUST prove more than bootstrap: it
  MUST show that the real provider path preserves row data.
- `tests/ui-previews.e2e.spec.ts.md` is the reviewable screenshot companion to
  the smoke gate. It SHOULD save success-case PNG files that Product can
  inspect after browser-capable runs.
- `tests/qa-screenshots.e2e.spec.ts.md` is the final-QA screenshot pass. It
  SHOULD capture every review-plan route required for live QA and write the
  QA screenshot manifest used by the Phase 8 QA gate.
- For non-starter domains, `CustomDashboard.tsx.md` SHOULD be the default
  custom-page starting point. `Landing.tsx.md` remains the starter-domain
  example.
- The upload helper files under `shared-runtime/files/` are part of the
  baseline shared runtime. They MUST remain present even when the app has no
  upload fields so `schemaContext.tsx` can import them safely.
- If the app supports uploads, the upload-aware provider unit test MUST also
  be added to the generated frontend test suite.
