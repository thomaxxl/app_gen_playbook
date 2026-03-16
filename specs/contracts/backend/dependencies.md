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

- `logicbank`

Runtime/package freeze ownership:

- The Architect MUST freeze the intended backend package set in
  `../../../runs/current/artifacts/architecture/runtime-bom.md` before
  implementation starts, or explicitly delegate a change proposal to Backend
  during Phase 4.
- The Backend role MAY propose a dependency deviation during Phase 4, but the
  deviation MUST be recorded in `runtime-bom.md` before implementation depends
  on it.

## Install command

```bash
pip install \
  safrs \
  logicbank \
  fastapi==0.135.1 \
  uvicorn==0.41.0 \
  SQLAlchemy==2.0.48 \
  python-multipart==0.0.20 \
  PyYAML==6.0.3 \
  pytest==9.0.2 \
  httpx==0.28.1
```

## Notes

- SAFRS should be installed as a normal pip package, not from git.
- LogicBank should be installed as the normal published pip package.
- If a project needs stricter reproducibility, pin to a published PyPI release
  such as `safrs==<chosen-version>` after selecting and validating that
  version.
- `python-multipart` is REQUIRED when the app exposes FastAPI multipart upload
  endpoints. The starter dependency set includes it so upload-capable apps do
  not need an undocumented extra install step.
- Delete/cascade behavior involving rule-managed child relationships must be
  tested explicitly; do not assume default passive-delete behavior is safe.
- See `../../../playbook/process/compatibility.md` for the overall local runtime
  profile.
