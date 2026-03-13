# Environment Notes

Verification date:

- 2026-03-13

Observed constraints:

- the host `python3` command resolves to `/home/t/lab/safrs-example/venv/bin/python3`
  in this shell environment
- the preferred backend `TestClient` verification path hangs on this host even
  for a direct `GET /healthz` probe
- the default sandbox cannot bind the Vite preview port used by
  `npm run test:e2e`

Chosen workarounds:

- backend verification used the documented fallback pytest route with
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and explicit `PYTHONPATH=.deps:src`
- the preferred backend `TestClient` suite is now gated behind
  `AIRPORT_OPS_ENABLE_TESTCLIENT=1` so the default backend pytest path does not
  hang on this host
- Playwright was rerun outside the sandbox so the frontend preview server
  could bind localhost normally
