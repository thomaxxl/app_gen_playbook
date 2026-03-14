# Uploads Feature Templates: Backend

Use this entrypoint only when uploads are enabled.

Load these concrete snippets:

- `../../../app/backend/files/README.md`
- `../../../app/backend/test_uploads.py.md`
- `../../../app/backend/config.py.md`
- `../../../app/backend/fastapi_app.py.md`

These files remain under `templates/app/backend/` because they mirror their
final target paths, but they MUST be loaded through this feature entrypoint
rather than through the core backend template flow.
