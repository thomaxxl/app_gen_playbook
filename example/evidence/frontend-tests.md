# Frontend Tests

Verification date:

- 2026-03-13

Results:

- `npm run test`: `4` files passed, `9` tests passed
- `npm run build`: success

Observed warnings:

- Vite reports a large production bundle warning for the admin shell chunk

Interpretation:

- the schema adapter, metadata lookup, search wrapper, and admin bootstrap
  smoke tests passed
- the production build succeeds under the current `/admin-app/` base path
