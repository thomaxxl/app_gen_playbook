# `backend/requirements.txt`

See also:

- [../../../specs/contracts/backend/dependencies.md](../../../specs/contracts/backend/dependencies.md)

```text
fastapi==0.135.1
uvicorn==0.41.0
SQLAlchemy==2.0.48
python-multipart==0.0.20
PyYAML==6.0.3
pytest==9.0.2
httpx==0.28.1
safrs
```

Notes:

- SAFRS should be installed as a normal pip package, not from git.
- If a project needs stricter reproducibility, pin SAFRS to a published PyPI
  version such as `safrs==<chosen-version>`.
- Install LogicBank separately with:
  - `pip install --no-deps "$LOCAL_LOGICBANK_PATH"` when a local override is
    explicitly provided
  - otherwise `pip install --no-deps logicbank`
- LogicBank currently uses a temporary local override through
  `LOCAL_LOGICBANK_PATH` only when that variable is set.
- Current validated example:
  `LOCAL_LOGICBANK_PATH=/home/t/lab/LogicBank`
- Switch back to the published pip package when the next fixed LogicBank
  release is available.
- See `../../../playbook/process/compatibility.md` for the required Python and
  local environment profile.
