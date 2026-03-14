# Frontend Dependencies

This file defines the known-good frontend dependency set for the starter app
pattern used by this playbook.

## Node runtime

The starter frontend MUST use Node.js `24+`.

The currently validated starter stack for this playbook is the Node
`24+` / Vite `6.2.2` line. The implementation MUST NOT silently downgrade to
an older Node major line. If the frontend toolchain is repinned again, that
change MUST be recorded as a deliberate compatibility decision.

## Package scope

Required runtime dependencies:

- `react@19.1.0`
- `react-dom@19.1.0`
- `react-admin@5.8.0`
- `react-router-dom@6.30.1`
- `@mui/material@7.0.1`
- `@mui/icons-material@7.0.1`
- `@emotion/react@11.14.0`
- `@emotion/styled@11.14.1`
- `yaml@2.8.1`
- `safrs-jsonapi-client@https://github.com/thomaxxl/safrs-jsonapi-client/releases/download/<release-tag>/safrs-jsonapi-client-<package-version>.tgz`

Optional but standard for custom figures:

- `d3@7.9.0`

Required dev dependencies:

- `vite@6.2.2`
- `@vitejs/plugin-react@4.3.4`
- `typescript@5.8.2`
- `@types/node@24.3.0`
- `@types/react@19.1.2`
- `@types/react-dom@19.1.2`
- `vitest@2.1.8`
- `jsdom@25.0.1`
- `@testing-library/react@16.3.0`
- `@playwright/test@1.53.1`

## Install commands

Runtime:

```bash
npm install \
  react@19.1.0 \
  react-dom@19.1.0 \
  react-admin@5.8.0 \
  react-router-dom@6.30.1 \
  @mui/material@7.0.1 \
  @mui/icons-material@7.0.1 \
  @emotion/react@11.14.0 \
  @emotion/styled@11.14.1 \
  yaml@2.8.1 \
  https://github.com/thomaxxl/safrs-jsonapi-client/releases/download/<release-tag>/safrs-jsonapi-client-<package-version>.tgz
```

The placeholder `<release-tag>` / `<package-version>` pair MUST be replaced
with a real verified release asset before the generated app is considered
complete.

Optional charts/graphs:

```bash
npm install d3@7.9.0
```

Dev:

```bash
npm install -D \
  vite@6.2.2 \
  @vitejs/plugin-react@4.3.4 \
  typescript@5.8.2 \
  @types/node@24.3.0 \
  @types/react@19.1.2 \
  @types/react-dom@19.1.2 \
  vitest@2.1.8 \
  jsdom@25.0.1 \
  @testing-library/react@16.3.0 \
  @playwright/test@1.53.1
```

## Notes

- `react-router-dom` MUST be a direct dependency. The frontend MUST NOT rely
  on it being hoisted transitively by `react-admin`.
- The frontend MUST use the declared Node runtime and MUST NOT rely on
  whatever `node` happens to be present on the machine or in the base image.
- The current starter dependency set is intentionally pinned to a Node 24-
  validated Vite 6 stack.
- `safrs-jsonapi-client` MUST be pinned through an immutable tarball URL or a
  published registry release. For this playbook, the preferred source is a
  GitHub release asset from `thomaxxl/safrs-jsonapi-client`. The frontend MUST
  NOT use a git dependency or raw GitHub source archive for this package in
  the generated app.
- If the selected `safrs-jsonapi-client` artifact references built outputs
  such as `dist/` that are missing from the installed artifact, the agent MUST
  stop using that artifact and replace it with a validated tarball or
  published release before continuing.
- Before freezing the generated app dependency, the agent MUST verify that:
  - the referenced GitHub release exists
  - the referenced `.tgz` asset exists
  - the asset version and the package filename agree
- `yaml` MUST be a direct dependency because the runtime loads `admin.yaml`
  client-side.
- `@types/node` MUST be present because the scaffold includes
  `tsconfig.node.json`
  for `vite.config.ts`.
- `vitest`, `jsdom`, and `@testing-library/react` are part of the standard
  starter validation stack. The generated frontend MUST ship at least one
  bootstrap smoke test, one search/filter merge test, and one config test for
  the `/admin-app/` base path.
- `@playwright/test` is part of the required delivery gate. The generated
  frontend MUST ship at least one browser-level smoke suite that verifies the
  app under `/admin-app/` and fails on console errors or broken network
  requests.
- `d3` is optional at install time, but it is the standard choice for custom
  charts, trees, and SVG figures when those are required.
- See `../../playbook/process/compatibility.md` for the overall local runtime
  profile.
