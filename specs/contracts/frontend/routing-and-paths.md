# Routing And Paths

This file defines the canonical frontend URL and base-path model.

## Canonical route model

The generated SPA is served under:

- `/admin-app/`

All in-app routes are hash-based under that base path:

- `/admin-app/#/Home`
- `/admin-app/#/Landing`
- `/admin-app/#/Collection`
- `/admin-app/#/Item/123/show`

This is the only route model to document for the starter frontend.

Do not describe root-based SPA routing as an equal alternative.

## Root URL

The root URL `/` is not the SPA.

It may:

- serve a simple landing page with links
- or redirect to `/admin-app/`

But the SPA itself lives under `/admin-app/`.

## Backend URLs used by the frontend

Canonical frontend contract URL:

- `/ui/admin/admin.yaml`

Canonical backend schema/docs URL:

- `/jsonapi.json`

Compatibility alias:

- `/swagger.json`

The generated frontend must not depend on `/openapi.json` for runtime behavior.

## Vite dev behavior

Vite dev must preserve the same public base path:

- `base: "/admin-app/"`

Expected dev URL:

- `http://127.0.0.1:5173/admin-app/#/Home`

Vite proxy targets:

- `/api`
- `/ui`
- `/jsonapi.json`
- `/swagger.json`

## Deep-link refresh behavior

Because the app uses hash routes, hard refreshes do not require per-route
server rewrites beyond serving the SPA entrypoint at `/admin-app/`.

Assets must resolve under:

- `/admin-app/assets/...`

Do not mix `/assets/...` and `/admin-app/assets/...` in the documented deploy
contract for generated frontends.

## Entry expectations

Every generated React-Admin app MUST provide:

- a `Home` page at `/admin-app/#/Home`
- a visible `Home` sidebar entry with icon

The starter scaffold MAY also provide:

- a no-layout `Landing` page at `/admin-app/#/Landing`

If both routes exist, `Home` SHOULD be treated as the primary in-admin entry
point.
