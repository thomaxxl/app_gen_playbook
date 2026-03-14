# Shared Runtime File Templates

These snippets correspond to:

- [../../../../../specs/features/uploads/README.md](../../../../../specs/features/uploads/README.md)
- [../../../../../specs/contracts/files/README.md](../../../../../specs/contracts/files/README.md)
- [../../../../../specs/contracts/frontend/runtime-contract.md](../../../../../specs/contracts/frontend/runtime-contract.md)

Copy them into:

- `frontend/src/shared-runtime/files/`

These runtime helpers are part of the baseline shared runtime because
`schemaContext.tsx` imports them directly. They MUST compile and no-op cleanly
when the app has no upload fields.

This is intentional. In this playbook, uploads are segmented primarily through
reading, capability gating, and activation rules rather than by requiring a
zero-footprint frontend runtime when uploads are disabled.

Baseline runtime files:

- `uploadAwareDataProvider.ts.md`
- `fileValueAdapters.ts.md`
- `fileFieldHelpers.ts.md`

Upload-specific test coverage is required only when the app supports
upload-backed fields:

- `../../tests/uploadAwareDataProvider.test.ts.md`
