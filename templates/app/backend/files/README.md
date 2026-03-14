# Backend File Templates

These snippets correspond to:

- [../../../../specs/contracts/files/README.md](../../../../specs/contracts/files/README.md)
- [../../../../specs/contracts/backend/README.md](../../../../specs/contracts/backend/README.md)

Copy them only when the generated app supports uploaded files or logical media
serving.

Suggested copy order:

1. `models.py.md`
2. `storage.py.md`
3. `schemas.py.md`
4. `service.py.md`
5. `api.py.md`
6. `../test_uploads.py.md`

These files are intentionally optional. Apps that do not support uploaded
files MUST NOT copy them gratuitously.
