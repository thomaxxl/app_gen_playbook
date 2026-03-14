# Uploads And Frontend Integration Contract

This file defines the request flow and frontend/provider behavior for uploaded
files.

## Core upload rule

The app MUST use a two-step upload model unless the run-owned architecture
artifacts explicitly approve a different flow.

The preferred flow is:

1. create pending file metadata through SAFRS JSON:API
2. upload the bytes to a dedicated FastAPI multipart endpoint
3. attach the resulting file metadata to the business record through normal
   SAFRS mutation

The app MUST NOT try to push raw binary content through normal JSON:API SAFRS
create/update requests.

## Required backend boundary

SAFRS MUST own:

- CRUD for file metadata resources
- file relationships and file-related browsing
- normal business-record mutation that references file metadata ids or
  relationships

Custom FastAPI routes MUST own:

- multipart upload bodies
- direct file-download or redirect orchestration
- optional file-attachment convenience endpoints

## Recommended endpoint set

If the app supports uploads, it SHOULD define:

- `PUT /api/stored_files/{file_id}/content`
- `GET /media/{file_id}`
- `GET /media/{file_id}/variants/{variant_name}`

Optional endpoints:

- `POST /api/file_attachments`
- `DELETE /api/file_attachments/{attachment_id}`
- `DELETE /api/stored_files/{file_id}`
- `POST /api/uploads`

## Upload response shape

The multipart upload response SHOULD stay close to JSON:API file metadata
shape, for example:

```json
{
  "data": {
    "type": "stored_files",
    "id": "f_123",
    "attributes": {
      "original_filename": "menu.png",
      "media_type": "image/png",
      "media_kind": "image",
      "byte_size": 284392,
      "status": "ready",
      "download_url": "/media/f_123",
      "preview_url": "/media/f_123/variants/thumb"
    }
  }
}
```

The frontend MUST NOT receive raw filesystem paths.

## React-Admin field behavior

The UI SHOULD use React-Admin file-aware inputs such as:

- `FileInput`
- `ImageInput`

Newly selected files will appear in form state with `rawFile`. The generated
frontend MUST treat that as a data-provider responsibility, not as a view-only
concern.

In the starter runtime, generated upload fields are single-file widgets. The
starter contract DOES NOT define a generated multi-file upload field from one
attribute declaration.

## Required frontend provider behavior

If the app includes upload-backed fields, the frontend data provider MUST:

1. intercept `create`
2. intercept `update`
3. detect values containing `rawFile`
4. create pending file metadata through SAFRS
5. upload the binary with `multipart/form-data`
6. replace the temporary file value with stable metadata or the corresponding
   file foreign-key/relationship payload
7. delegate the final record save to the base provider

The upload-aware provider MUST wrap the normal SAFRS provider. The UI layer
MUST NOT attempt to perform uploads directly inside form components.

## Frontend value shapes

Stable existing-file value example:

```ts
{
  id: "01JQ...",
  title: "menu.png",
  src: "/media/01JQ...",
  media_type: "image/png"
}
```

New local file example:

```ts
{
  title: "menu.png",
  src: "blob:http://localhost/...",
  rawFile: File
}
```

## Business-field translation

The upload-aware provider MUST translate stable uploaded-file metadata into the
real business mutation contract.

Examples:

- single-file field:
  `hero_image` in form state becomes `hero_image_file_id` in the saved record
- relationship-based field:
  stable metadata becomes JSON:API relationship linkage
- attachment list:
  stable metadata drives `FileAttachment` create/update/delete operations

The upload-aware provider SHOULD derive its field mapping from raw
`admin.yaml` entries where:

- `type` is `file` or `image`
- `upload_target` identifies the persisted SAFRS field
- `purpose` is forwarded to the multipart endpoint when present

## admin.yaml and record-shape rule

Upload-backed business persistence MUST still be represented in the normal
metadata contract as:

- scalar file id fields such as `hero_image_file_id`
- or explicit relationships / attachment resources

The frontend MUST NOT model raw binary fields as normal persisted SAFRS scalar
attributes.

## Validation obligations

If the app supports uploads, backend verification MUST cover:

- pending file metadata creation
- multipart content upload
- logical media retrieval
- failure path that marks file status `failed`

If the app supports uploads, frontend verification MUST cover:

- file value materialization from `rawFile`
- successful upload-backed create or update flow
- visible error on failed upload

## Template consequence

If the app supports uploads, the implementation SHOULD add frontend runtime
helpers under:

```text
frontend/src/shared-runtime/files/
```

and backend file handling under:

```text
backend/src/my_app/files/
```
