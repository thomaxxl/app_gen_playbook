# Frontend Scaffold

This file defines the minimal file tree for a runnable starter frontend.

Load this file when creating the frontend skeleton from scratch or checking
whether the shipped templates are complete.

## Required files

```text
frontend/
  index.html
  package.json
  tsconfig.json
  tsconfig.app.json
  tsconfig.node.json
  vite.config.ts
  vitest.config.ts
  playwright.config.ts
  src/
    App.tsx
    Home.tsx
    theme.ts
    PageHero.tsx
    PageHeader.tsx
    EmptyState.tsx
    ErrorState.tsx
    FormSection.tsx
    SectionBlock.tsx
    QuickActionCard.tsx
    SummaryCard.tsx
    config.ts
    main.tsx
    vite-env.d.ts
    generated/
      resourcePages.ts
      resources/
        <one wrapper file per resource named in ../../architecture/resource-naming.md>
    shared-runtime/
      SchemaDrivenAdminApp.tsx
      relationshipUi.tsx
      resourceRegistry.tsx
      admin/
        schemaContext.tsx
        resourceMetadata.ts
        createSearchEnabledDataProvider.ts
      files/
        uploadAwareDataProvider.ts
        fileValueAdapters.ts
        fileFieldHelpers.ts
    shims/
      fs-promises.ts
  tests/
    SchemaDrivenAdminApp.smoke.test.tsx
    schemaContext.test.ts
    createSearchEnabledDataProvider.test.ts
    uploadAwareDataProvider.test.ts   # required only if the app supports uploads
    vite.config.test.ts
    smoke.e2e.spec.ts
```

## Template source

These files are shipped under `templates/app/frontend/`:

- `index.html.md`
- `package.json.md`
- `tsconfig.json.md`
- `tsconfig.app.json.md`
- `tsconfig.node.json.md`
- `vite.config.ts.md`
- `vitest.config.ts.md`
- `playwright.config.ts.md`
- `main.tsx.md`
- `theme.ts.md`
- `vite-env.d.ts.md`
- `config.ts.md`
- `App.tsx.md`
- `Home.tsx.md`
- `PageHero.tsx.md`
- `PageHeader.tsx.md`
- `EmptyState.tsx.md`
- `ErrorState.tsx.md`
- `FormSection.tsx.md`
- `SectionBlock.tsx.md`
- `QuickActionCard.tsx.md`
- `SummaryCard.tsx.md`
- `Landing.tsx.md` when the run explicitly includes a starter no-layout page
- `generated/resources/Collection.tsx.md`
- `generated/resources/Item.tsx.md`
- `generated/resources/Status.tsx.md`
- `resourcePages.ts.md`
- `SchemaDrivenAdminApp.tsx.md`
- `shared-runtime/relationshipUi.tsx.md`
- `shared-runtime/admin/schemaContext.tsx.md`
- `shared-runtime/admin/resourceMetadata.ts.md`
- `shared-runtime/admin/createSearchEnabledDataProvider.ts.md`
- `shared-runtime/resourceRegistry.tsx.md`
- `shared-runtime/files/uploadAwareDataProvider.ts.md`
- `shared-runtime/files/fileValueAdapters.ts.md`
- `shared-runtime/files/fileFieldHelpers.ts.md`
- `fs-promises.ts.md`
- `tests/SchemaDrivenAdminApp.smoke.test.tsx.md`
- `tests/schemaContext.test.ts.md`
- `tests/resourceMetadata.test.ts.md`
- `tests/createSearchEnabledDataProvider.test.ts.md`
- `tests/uploadAwareDataProvider.test.ts.md`
- `tests/vite.config.test.ts.md`
- `tests/smoke.e2e.spec.ts.md`

Optional upload-related template:

- `tests/uploadAwareDataProvider.test.ts.md`

## Required build scripts

The starter frontend must support:

- `npm run dev`
- `npm run check`
- `npm run test`
- `npm run test:e2e`
- `npm run build`

`npm run build` should run type-checking before the Vite production build.

## Notes

- The frontend scaffold must be complete enough to run without first generating
  a hidden Vite starter app elsewhere.
- `Home.tsx` is required even when `Landing.tsx` is omitted or replaced.
- `theme.ts`, `PageHero.tsx`, `PageHeader.tsx`, `EmptyState.tsx`,
  `ErrorState.tsx`, `FormSection.tsx`, `SectionBlock.tsx`,
  `QuickActionCard.tsx`, and `SummaryCard.tsx` are part of the starter UI
  shell.
- `Landing.tsx` is optional and MUST be added only when the run-owned UX
  artifacts explicitly require a no-layout page.
- Additional project-specific files are allowed, but the required files above
  are the minimum contract for the starter playbook.
- The `shared-runtime/files/` helper files are baseline runtime files. They
  must compile even when the app has no upload fields and should no-op in that
  case.
- `shared-runtime/relationshipUi.tsx` is a baseline runtime file. It MUST be
  present even when a given app has only a few relationships, because the
  generated list/show pages depend on it for foreign-key rendering.
- The generated page shell SHOULD reuse the starter UI shell files unless the
  run-owned UX artifacts document a different layout system.
- For non-starter domains, the wrapper files under `generated/resources/` MUST
  be replaced with one file per resource declared in
  `../../architecture/resource-naming.md`.
- The starter `Collection`, `Item`, and `Status` wrapper templates are worked
  examples, not a universal file-name contract for every app.
