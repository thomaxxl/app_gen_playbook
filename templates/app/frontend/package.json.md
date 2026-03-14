# `frontend/package.json`

See also:

- [../../../specs/contracts/frontend/dependencies.md](../../../specs/contracts/frontend/dependencies.md)

Use a pinned dependency set. Do not rely on transitive dependencies for routing
or YAML parsing.

```json
{
  "name": "my-app-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": {
    "node": ">=24.0.0"
  },
  "scripts": {
    "dev": "vite",
    "check": "tsc -b",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@emotion/react": "11.14.0",
    "@emotion/styled": "11.14.1",
    "@mui/icons-material": "7.0.1",
    "@mui/material": "7.0.1",
    "react": "19.1.0",
    "react-admin": "5.8.0",
    "react-dom": "19.1.0",
    "react-router-dom": "6.30.1",
    "safrs-jsonapi-client": "<REPLACE_WITH_VERIFIED_GITHUB_RELEASE_TGZ_URL>",
    "yaml": "2.8.1"
  },
  "devDependencies": {
    "@testing-library/react": "16.3.0",
    "@types/node": "24.3.0",
    "@types/react": "19.1.2",
    "@types/react-dom": "19.1.2",
    "@vitejs/plugin-react": "4.3.4",
    "@playwright/test": "1.53.1",
    "jsdom": "25.0.1",
    "typescript": "5.8.2",
    "vite": "6.2.2",
    "vitest": "2.1.8"
  }
}
```

Add `d3@7.9.0` when the app includes charts or graph views.

The `engines.node` field is intentional. The starter frontend assumes a Node
24 runtime with the pinned Vite `6.2.2` toolchain. If a project documents a
deliberate compatibility deviation, update this field and the pinned frontend
toolchain together instead of mixing incompatible versions ad hoc.

The `safrs-jsonapi-client` entry MUST remain an immutable tarball URL or a
published registry release. For this playbook, prefer a GitHub release asset
URL from `thomaxxl/safrs-jsonapi-client`. Do not switch it to a git dependency
or a raw `codeload` source archive in generated apps. If the selected artifact
is missing the built outputs referenced by its own package metadata, replace it
with a validated release asset before continuing.

`<REPLACE_WITH_VERIFIED_GITHUB_RELEASE_TGZ_URL>` is an intentional unresolved
token. A generated app is incomplete until it is replaced with a real verified
release asset URL.

See `../../../playbook/process/compatibility.md` for the declared local runtime
baseline.
