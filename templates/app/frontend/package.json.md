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
    "safrs-jsonapi-client": "https://codeload.github.com/thomaxxl/safrs-jsonapi-client/tar.gz/484c8f7b3195b31b8c56e4abc2641e8fa1ab12cb",
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
published registry release. Do not switch it to a git dependency in generated
apps. If the selected artifact is missing the built outputs referenced by its
own package metadata, replace it with a validated tarball or registry release
before continuing.

See `../../../playbook/process/compatibility.md` for the declared local runtime
baseline.
