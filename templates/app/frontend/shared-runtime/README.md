# Shared Runtime Templates

These snippets are the vendored frontend runtime required by the starter app.

Copy them into:

- `frontend/src/shared-runtime/`

Required files:

- `admin/schemaContext.tsx.md`
- `admin/resourceMetadata.ts.md`
- `admin/createSearchEnabledDataProvider.ts.md`
- `relationshipUi.tsx.md`
- `resourceRegistry.tsx.md`

The baseline frontend test lane MUST also include:

- `../tests/schemaContext.test.ts.md`
- `../tests/dataProvider.integration.test.ts.md`

Optional upload-related files:

- `files/uploadAwareDataProvider.ts.md`
- `files/fileValueAdapters.ts.md`
- `files/fileFieldHelpers.ts.md`

These are part of the archive so the starter frontend does not depend on
hidden repo-local code outside `app_gen_playbook/templates/`.

`relationshipUi.tsx.md` is a required baseline helper because generated
list/show pages MUST render foreign keys and related summaries the same way as
the Northwind reference runtime.

That runtime is relationship-first on the read side:

- prefer embedded related objects from `include=...`
- otherwise prefer canonical parent relationship routes
- only then fall back to id-based fetches

Do not invent helper endpoints such as `/api/order_customer_summary` when
`Order.customer` should already exist as a SAFRS relationship or include path.

`admin/resourceMetadata.ts.md` is equally critical: it MUST synthesize
relationship metadata from normalized schema, `fkToRelationship`, and raw
`admin.yaml` so sparse-schema apps do not collapse back to raw-id-only UI.

A generated app that omits `relationshipUi.tsx.md` or replaces the baseline
relationship runtime with plain `ReferenceField`-only rendering is invalid.

The relationship runtime is intentionally split into two layers:

- `admin/resourceMetadata.ts.md` for metadata construction
- `resourceRegistry.tsx.md` plus `relationshipUi.tsx.md` for rendering

Do not collapse those layers into ad hoc per-page logic. Generated list/show
pages MUST consume the synthesized relationship metadata instead.
