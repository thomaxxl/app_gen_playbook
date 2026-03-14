# Uploads Feature Templates: Frontend

Use this entrypoint only when uploads are enabled.

Load these concrete snippets:

- `../../../app/frontend/shared-runtime/files/README.md`
- `../../../app/frontend/tests/uploadAwareDataProvider.test.ts.md`
- `../../../app/frontend/shared-runtime/admin/schemaContext.tsx.md`
- `../../../app/frontend/shared-runtime/admin/resourceMetadata.ts.md`
- `../../../app/frontend/shared-runtime/resourceRegistry.tsx.md`

The last three files are core runtime files that already contain upload-aware
integration points. They MUST be treated as upload-relevant only when the
capability profile enables uploads.
