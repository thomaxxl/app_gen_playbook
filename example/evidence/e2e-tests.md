# End-To-End Tests

Verification date:

- 2026-03-13

Command:

- `npm run test:e2e`

Result:

- `1 passed`

Environment note:

- the browser smoke suite required elevated host execution because the default
  sandbox could not bind the Vite preview port (`listen EPERM` on
  `127.0.0.1:5173`)

Interpretation:

- `example/run.sh` composes the backend and frontend successfully
- the app loads under `/admin-app/#/Landing`
- the smoke flow reaches the `Gate` resource view without console errors,
  page errors, or failed local network responses
