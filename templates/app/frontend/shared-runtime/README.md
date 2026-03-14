# Shared Runtime Templates

These snippets are the vendored frontend runtime required by the starter app.

Copy them into:

- `frontend/src/shared-runtime/`

Required files:

- `admin/schemaContext.tsx.md`
- `admin/resourceMetadata.ts.md`
- `admin/createSearchEnabledDataProvider.ts.md`
- `resourceRegistry.tsx.md`

Optional upload-related files:

- `files/uploadAwareDataProvider.ts.md`
- `files/fileValueAdapters.ts.md`
- `files/fileFieldHelpers.ts.md`

These are part of the archive so the starter frontend does not depend on
hidden repo-local code outside `app_gen_playbook/templates/`.
