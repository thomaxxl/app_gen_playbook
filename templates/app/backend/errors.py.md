# `backend/src/my_app/errors.py`

See also:

- [../../../specs/contracts/backend/api-contract.md](../../../specs/contracts/backend/api-contract.md)
- [../../../specs/contracts/rules/boundaries-and-errors.md](../../../specs/contracts/rules/boundaries-and-errors.md)

Use this shared helper module for expected application failures that must leave
the backend as JSON:API `4xx` responses instead of leaking as `500`.

```python
from __future__ import annotations

from collections.abc import Iterable

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from safrs.errors import ValidationError

try:
    from logic_bank.util import ConstraintException
except Exception:  # pragma: no cover - LogicBank is optional in some starter slices.
    ConstraintException = None


def jsonapi_error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "jsonapi": {"version": "1.0"},
            "errors": [
                {
                    "status": str(status_code),
                    "title": "ValidationError",
                    "detail": detail,
                }
            ],
        },
    )


def expected_validation_error_types(
    extra_expected_error_types: Iterable[type[BaseException]] = (),
) -> tuple[type[BaseException], ...]:
    types: list[type[BaseException]] = [ValidationError]
    if ConstraintException is not None:
        types.append(ConstraintException)
    for exc_type in extra_expected_error_types:
        if exc_type not in types:
            types.append(exc_type)
    return tuple(types)


def raise_expected_validation_error(
    exc: BaseException,
    *,
    extra_expected_error_types: Iterable[type[BaseException]] = (),
) -> None:
    expected_types = expected_validation_error_types(extra_expected_error_types)
    if isinstance(exc, ValidationError):
        raise exc
    if isinstance(exc, expected_types):
        raise ValidationError(str(exc)) from exc
    raise exc


def install_expected_validation_error_handlers(
    app: FastAPI,
    *,
    extra_expected_error_types: Iterable[type[BaseException]] = (),
) -> None:
    async def handle_validation_error(
        _request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        return jsonapi_error_response(400, str(exc))

    async def handle_expected_exception(
        _request: Request,
        exc: BaseException,
    ) -> JSONResponse:
        return jsonapi_error_response(400, str(exc))

    app.add_exception_handler(ValidationError, handle_validation_error)

    for exc_type in expected_validation_error_types(extra_expected_error_types):
        if exc_type is ValidationError:
            continue
        app.add_exception_handler(exc_type, handle_expected_exception)
```

Notes:

- This is the canonical generated-backend seam for expected business-rule and
  validation failures.
- Keep the caught exception set narrow and explicit. Do not widen this helper
  to catch broad `Exception`.
- For custom FastAPI endpoints, `jsonapi_rpc`, or thin request wrappers, use
  `raise_expected_validation_error(...)` when an expected business failure
  needs to leave the backend in the same JSON:API `400` shape as SAFRS CRUD.
- If a run introduces an app-local validation class, register it through
  `extra_expected_error_types=(MyValidationError,)` instead of inventing a
  second error payload format.
