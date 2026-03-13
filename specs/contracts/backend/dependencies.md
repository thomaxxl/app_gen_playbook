# Backend Dependencies

This file defines the backend dependency set for the starter app pattern used
by this playbook.

## Scope decision

The backend spec is FastAPI-only.

Flask is out of scope for this guide set.

## Required dependencies

Pinned packages:

- `fastapi==0.135.1`
- `uvicorn==0.41.0`
- `SQLAlchemy==2.0.48`
- `PyYAML==6.0.3`
- `pytest==9.0.2`
- `httpx==0.28.1`
- `safrs`

Logic/rules dependency:

- optional temporary local checkout override via `LOCAL_LOGICBANK_PATH`

## Install command

```bash
pip install \
  safrs \
  fastapi==0.135.1 \
  uvicorn==0.41.0 \
  SQLAlchemy==2.0.48 \
  PyYAML==6.0.3 \
  pytest==9.0.2 \
  httpx==0.28.1
if [[ -n "${LOCAL_LOGICBANK_PATH:-}" ]]; then
  pip install --no-deps "$LOCAL_LOGICBANK_PATH"
else
  pip install --no-deps logicbank
fi
```

## Notes

- SAFRS should be installed as a normal pip package, not from git.
- If a project needs stricter reproducibility, pin to a published PyPI release
  such as `safrs==<chosen-version>` after selecting and validating that
  version.
- LogicBank currently uses a local-checkout override only when
  `LOCAL_LOGICBANK_PATH` is set because the required fix is not yet in a
  published release.
- This local-path LogicBank override is temporary. Switch back to the normal
  published pip package when the next fixed release is available.
- Current validated example:
  `LOCAL_LOGICBANK_PATH=/home/t/lab/LogicBank`
- Use `--no-deps` when installing the local LogicBank checkout so it does not
  override the backend SQLAlchemy version selected for SAFRS compatibility.
- If the local LogicBank checkout is unavailable or unset, the implementation
  SHOULD install the published package with
  `pip install --no-deps logicbank`.
- Expect SQLAlchemy deprecation warnings under the current LogicBank stack.
- Delete/cascade behavior involving rule-managed child relationships must be
  tested explicitly; do not assume default passive-delete behavior is safe.
- See `../../playbook/process/compatibility.md` for the overall local runtime
  profile.
