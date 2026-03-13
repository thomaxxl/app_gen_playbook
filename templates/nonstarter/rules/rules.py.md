# `backend/src/<package>/rules.py` for a non-starter app

Use this template when the app's rule set does not match the starter trio.

The implementation MUST derive its rule declarations from:

- `../../../runs/current/artifacts/product/business-rules.md`
- `../../../runs/current/artifacts/backend-design/rule-mapping.md`
- `../../../specs/contracts/rules/lifecycle.md`

The real file MUST define:

- `declare_logic()`
- `activate_logic(session_factory)`
- only documented `Rule.*` DSL calls
- no invented decorators or unsupported DSL
