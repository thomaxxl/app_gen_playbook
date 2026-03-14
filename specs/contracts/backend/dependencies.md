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
- `python-multipart==0.0.20`
- `PyYAML==6.0.3`
- `pytest==9.0.2`
- `httpx==0.28.1`
- `safrs`

Logic/rules dependency:

- optional temporary local checkout override via `LOCAL_LOGICBANK_PATH`

Runtime/package freeze ownership:

- The Architect MUST freeze the intended backend package set in
  `../../runs/current/artifacts/architecture/runtime-bom.md` before
  implementation starts, or explicitly delegate a change proposal to Backend
  during Phase 4.
- The Backend role MAY propose a dependency deviation during Phase 4, but the
  deviation MUST be recorded in `runtime-bom.md` before implementation depends
  on it.

## Install command

```bash
pip install \
  safrs \
  fastapi==0.135.1 \
  uvicorn==0.41.0 \
  SQLAlchemy==2.0.48 \
  python-multipart==0.0.20 \
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
- Use `--no-deps` when installing the local LogicBank checkout so it does not
  override the backend SQLAlchemy version selected for SAFRS compatibility.
- If the local LogicBank checkout is unavailable or unset, the implementation
  SHOULD install the published package with
  `pip install --no-deps logicbank`.
- If a local dependency override is used, the run MUST record:
  - the reason for the override
  - the package affected
  - the local path or local artifact source
  - the expected removal condition
  in:
  - `../../runs/current/artifacts/architecture/runtime-bom.md`
  - the relevant role `context.md`
  - and any handoff note that depends on the override
- `python-multipart` is REQUIRED when the app exposes FastAPI multipart upload
  endpoints. The starter dependency set includes it so upload-capable apps do
  not need an undocumented extra install step.
- Expect SQLAlchemy deprecation warnings under the current LogicBank stack.
- Delete/cascade behavior involving rule-managed child relationships must be
  tested explicitly; do not assume default passive-delete behavior is safe.
- See `../../playbook/process/compatibility.md` for the overall local runtime
  profile.
