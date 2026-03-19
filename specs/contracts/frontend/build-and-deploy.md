# Frontend Build And Deploy

This file defines the production build expectations for generated frontends.

## Required build outcome

`vite build` MUST produce a frontend that works when served under:

- `/app/`

The starter scaffold MUST also support:

- `npm run check`
- `npm run test`

with a TypeScript project reference setup rooted at:

- `tsconfig.json`
- `tsconfig.app.json`
- `tsconfig.node.json`

## Base path

The frontend MUST set:

- `base: "/app/"`

This ensures asset URLs are emitted under:

- `/app/assets/...`

## Required production URLs

- SPA: `/app/`
- required in-admin entry: `/app/#/Home`
- starter custom-route example: `/app/#/Landing`
- API: `/api`
- admin schema: `/ui/admin/admin.yaml`
- docs schema: `/jsonapi.json`

## nginx/server responsibility

The server MUST:

- serve the SPA entrypoint at `/app/`
- serve emitted assets from `/app/assets/`
- redirect or forward `/` to `/app/`
- redirect or forward `/index.html` to `/app/`
- proxy `/api`
- proxy `/ui`
- proxy `/jsonapi.json`
- optionally proxy `/swagger.json`

## Hard refresh

Because routing is hash-based, hard-refresh behavior is simple:

- the server only needs to return the SPA entrypoint for `/app/`
- the hash portion never reaches the server

## Root page

For packaged same-origin delivery, root `/` and `/index.html` MUST redirect or
forward to `/app/`. The default packaged starter MUST NOT ship the stock
nginx welcome page or a separate generic landing page in front of the admin app.

## Minimum automated checks

Before treating the frontend as deployable, the starter app MUST pass:

- `npm run check`
- `npm run test`
- `npm run build`
