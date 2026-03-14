# File Storage And Serving Contract

This file defines the backend and deployment contract for uploaded binaries and
their metadata.

## Core rule

- uploaded binary content MUST NOT be stored in the relational database
- file metadata MUST be stored in SQLAlchemy models
- business records MUST link to file metadata through normal SAFRS resources,
  scalar foreign keys, or attachment relationships

## File classes

The implementation MUST distinguish:

### Application static assets

Examples:

- built frontend assets
- bundled logos
- shipped documentation assets

These assets:

- MUST be treated as immutable at runtime
- SHOULD be served directly by nginx or ASGI static-file middleware
- MUST NOT be modeled as uploaded media records

### User-managed media

Examples:

- uploaded images
- uploaded PDFs
- derived thumbnails
- generated preview images

These assets:

- MUST be stored outside the relational database
- MUST have database metadata
- MUST be served through logical app URLs rather than raw storage paths

## Public route model

If an app supports uploaded media, it MUST use logical routes such as:

- `/media/{file_id}`
- `/media/{file_id}/variants/{variant_name}`

The app MUST NOT expose raw filesystem paths or storage keys to the frontend.

## Storage abstraction

The backend SHOULD start from a storage abstraction with operations equivalent
to:

- `write_temp(...)`
- `finalize(...)`
- `open(...)`
- `delete(...)`
- `exists(...)`
- `local_path(...)`
- `internal_redirect_path(...)`

The database MUST store backend-neutral object keys, not absolute OS paths.

Good:

```text
objects/7f/3a/01JQ.../original.webp
```

Bad:

```text
/var/app/data/media/objects/7f/3a/01JQ.../original.webp
```

## Required metadata models

If the app supports uploaded files, it SHOULD define at least:

- `StoredFile`
- `FileVariant`
- `FileAttachment` when the app needs galleries, ordered attachments, or
  reuse across records

Minimum `StoredFile` contract:

- stable primary key
- `storage_backend`
- `storage_key`
- `original_filename`
- `media_type`
- `media_kind`
- `byte_size`
- `status`
- lifecycle timestamps
- provisional ownership/tenant fields

Recommended statuses:

- `pending`
- `ready`
- `failed`
- `deleted`

## Linking patterns

The app MUST use one of these patterns:

### Direct single-file foreign key

Use for true one-to-one file fields such as:

- `avatar_file_id`
- `hero_image_file_id`
- `menu_pdf_file_id`

### Attachment join table

Use for:

- galleries
- ordered images
- reusable attachments
- extensible multi-file fields

The playbook MUST NOT force all file use cases through a join table if a
single stable file field is the real domain contract.

## Serving modes

The app SHOULD support:

- development serving through FastAPI `FileResponse`
- production serving through app lookup plus nginx byte serving

The serving mode SHOULD be controlled by a setting such as:

- `MEDIA_SERVE_MODE=app|nginx`

### Development

In development, the app MAY return `FileResponse` directly from the media
endpoint.

### Production

In production, the app SHOULD:

1. resolve file metadata in the app
2. decide which object key to serve
3. return `X-Accel-Redirect`
4. let nginx serve the actual bytes from an internal location

The public `/media/...` route MUST remain stable regardless of the underlying
storage path.

## Variants

For uploaded images, the app SHOULD support:

- `original`
- `thumb`
- `medium`

For PDFs, the app SHOULD keep the original unchanged and MAY add:

- `page_count`
- preview images such as first-page preview

## Deletion model

The default deletion model SHOULD be soft delete first.

The app SHOULD:

1. mark `status='deleted'`
2. set `deleted_at`
3. deactivate or remove active attachments
4. leave physical object deletion to a later cleanup/reconciliation task

## Ownership and tenancy metadata

Even before security enforcement exists, the file metadata schema SHOULD
include provisional fields such as:

- `owner_user_id`
- `uploaded_by_user_id`
- `tenant_id`
- `visibility_scope`

The attachment schema SHOULD likewise include:

- `owner_user_id`
- `attached_by_user_id`

These fields allow later authorization work without a schema redesign.

## Reconciliation

Because object storage and relational metadata are not one atomic system, the
backend SHOULD define a reconciliation path that can:

- delete stale temp files
- report old `pending` rows
- report `failed` rows with leftover objects
- report storage objects with no database row

## Backend module layout

If an app supports uploaded files, the backend SHOULD isolate the logic under a
module tree such as:

```text
backend/src/my_app/files/
  __init__.py
  api.py
  models.py
  service.py
  storage.py
  schemas.py
```

Additional modules such as `metadata.py` or `variants.py` MAY be added when
the app needs richer preview generation.
