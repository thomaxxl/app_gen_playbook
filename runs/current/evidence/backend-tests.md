# Backend Tests

- Passed: Python syntax compilation for backend app and test files via
  `python3 -m py_compile`
- Not run: `pytest` backend suite, because dependencies were not installed in
  this session
- Not run: in-process HTTP-path tests gated by
  `AIRPORT_OPS_APP_ENABLE_TESTCLIENT=1`
