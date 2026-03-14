# Uploads Feature Templates: Backend

Use this entrypoint only when uploads are enabled.

Load these concrete snippets:

- `../../../app/backend/files/README.md`
- `../../../app/backend/test_uploads.py.md`
- `../../../app/backend/config.py.md`
- `../../../app/backend/fastapi_app.py.md`
- `fastapi_app.uploads.patch.md`

These files remain under `templates/app/backend/` because they mirror their
final target paths, but they MUST be loaded through this feature entrypoint
rather than through the core backend template flow.

Do not rely on manual uncommenting inside the core FastAPI template. Apply the
feature-owned patch snippet for the uploads router integration explicitly.
