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
    "react-router-dom": "6.30.3",
    "safrs-jsonapi-client": "<REPLACE_WITH_VERIFIED_GITHUB_RELEASE_TGZ_URL>",
    "yaml": "2.8.1"
  },
  "devDependencies": {
    "@testing-library/react": "16.3.0",
    "@types/node": "24.3.0",
    "@types/react": "19.1.2",
    "@types/react-dom": "19.1.2",
    "@vitejs/plugin-react": "4.3.4",
    "@playwright/test": "1.58.2",
    "jsdom": "25.0.1",
    "typescript": "5.8.2",
    "vite": "6.2.2",
    "vitest": "2.1.9"
  }
}
```

Add `d3@7.9.0` when the app includes charts or graph views.

Add the Font Awesome package set only when the `font-awesome-icons` feature
pack is enabled for the run:

```json
"@fortawesome/react-fontawesome": "3.2.0",
"@fortawesome/fontawesome-svg-core": "7.2.0",
"@fortawesome/free-solid-svg-icons": "7.2.0"
```

Optional advanced frontend packages MUST remain capability-gated. They MUST
NOT be added to the generated `package.json` unless the matching feature pack
is enabled and the run-owned `runtime-bom.md` records the exact pins.

Approved optional package pins:

```json
"motion": "12.36.0",
"react-virtuoso": "4.18.3",
"@dnd-kit/react": "0.3.2",
"@dnd-kit/helpers": "0.3.2",
"@xyflow/react": "12.10.1",
"lexical": "0.41.0",
"@lexical/react": "0.41.0",
"@lexical/rich-text": "0.41.0",
"@lexical/history": "0.41.0",
"@lexical/link": "0.41.0",
"@lexical/list": "0.41.0",
"@lexical/utils": "0.41.0",
"embla-carousel-react": "8.6.0"
```

Optional only when the feature-owned profile enables them:

```json
"@lexical/html": "0.41.0",
"@lexical/markdown": "0.41.0",
"@lexical/table": "0.41.0",
"embla-carousel-autoplay": "8.6.0"
```

The `engines.node` field is intentional. The starter frontend assumes a Node
24 runtime with the pinned Vite `6.2.2` toolchain. If a project documents a
deliberate compatibility deviation, update this field and the pinned frontend
toolchain together instead of mixing incompatible versions ad hoc.

The authoritative starter baseline remains this template plus
`../../../specs/contracts/frontend/dependencies.md`. A tracked example app or
generated app that drifts from that baseline MUST be treated as maintenance
debt until the playbook is deliberately repinned.

The `safrs-jsonapi-client` entry MUST remain an immutable tarball URL or a
published registry release. For this playbook, prefer a GitHub release asset
URL from `thomaxxl/safrs-jsonapi-client`. Do not switch it to a git dependency
or a raw `codeload` source archive in generated apps. If the selected artifact
is missing the built outputs referenced by its own package metadata, replace it
with a validated release asset before continuing.

If the first `npm install` on a newly generated app still requires an
immediate `npm audit fix --force`, treat that as a stale playbook baseline and
repin the template dependency set instead of documenting `audit fix` as normal
generated-app setup.

`<REPLACE_WITH_VERIFIED_GITHUB_RELEASE_TGZ_URL>` is allowed only in the
template source. The generated `app/frontend/package.json` MUST replace it
with the real verified release asset URL recorded in
`../../../runs/current/artifacts/architecture/runtime-bom.md` before install.

See:

- `../../../playbook/process/runtime-baseline.md`
- `../../../playbook/process/dependency-materialization.md`
- `../../../playbook/process/compatibility.md`
