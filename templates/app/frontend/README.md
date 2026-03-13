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
12. `shared-runtime/admin/createSearchEnabledDataProvider.ts.md`
13. `shared-runtime/resourceRegistry.tsx.md`
14. `generated/resources/Collection.tsx.md`
15. `generated/resources/Item.tsx.md`
16. `generated/resources/Status.tsx.md`
17. `resourcePages.ts.md`
18. `App.tsx.md`
19. `Landing.tsx.md`
20. `CustomDashboard.tsx.md` when the app needs a non-starter custom page
21. `D3Visualization.tsx.md` if the app needs charts or figures
22. `fs-promises.ts.md`
23. `vite.config.ts.md`
24. `vitest.config.ts.md`
25. `playwright.config.ts.md`
26. `tests/SchemaDrivenAdminApp.smoke.test.tsx.md`
27. `tests/schemaContext.test.ts.md`
28. `tests/resourceMetadata.test.ts.md`
29. `tests/createSearchEnabledDataProvider.test.ts.md`
30. `tests/vite.config.test.ts.md`
31. `tests/smoke.e2e.spec.ts.md`
32. `../project/run.sh.md`
33. `../project/README.app.md`

Notes:

- For non-starter domains, the three starter wrapper files are examples, not a
  fixed universal file list. The implementation MUST create one wrapper file
  per resource declared in
  `../../../runs/current/artifacts/architecture/resource-naming.md`.
- `resourcePages.ts.md` MUST register the actual resource wrapper set for the
  current app, not the starter trio by default.
- For non-starter domains, `CustomDashboard.tsx.md` SHOULD be the default
  custom-page starting point. `Landing.tsx.md` remains the starter-domain
  example.
