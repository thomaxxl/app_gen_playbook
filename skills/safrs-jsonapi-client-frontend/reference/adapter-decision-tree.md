# Adapter Decision Tree

Use this sequence for every frontend data-access decision.

## 1. Is the backend SAFRS / ApiLogicServer and the frontend React-admin?

If yes, the default answer is `safrs-jsonapi-client`.

Do not start by designing a local provider.

## 2. Is the current `admin.yaml` authoring shape identical to the package's expected raw input?

- If yes, call the package normalizer directly.
- If no, write a thin adapter that converts the playbook authoring contract into the package input shape.

The adapter must preserve:
- resource names
- `endpoint`
- `user_key`
- attributes
- search configuration
- `tab_groups`
- relationship ordering and labels
- relationship visibility

Do not answer this mismatch by creating a separate local schema format with separate semantics.

## 3. Does the UI need full-text `q` search?

- If no, use the package provider directly.
- If yes, prefer upstreaming or extending the package.
- If a local wrapper is temporarily required, it must still use package normalization and return package-compatible records.

## 4. Does the UI need related-record display?

Use this order:
1. embedded `include=...`
2. canonical parent relationship route
3. `getOne(...)` fallback by id

Do not skip step 2.

## 5. Does the UI need a SAFRS custom method or non-resource service call?

Use `dataProvider.execute(resource, params)`.

Do not do direct `fetch(...)` from the component tree.

## 6. Does the UI need upload-aware field handling?

Wrap the package-backed provider after the package provider is created.
Do not bypass the package provider for ordinary CRUD.

## 7. Are you about to add a custom local JSON:API parser, query builder, or record normalizer?

Stop and document the exception first.

Permitted reasons are narrow:
- package gap not yet supported upstream
- run-specific behavior that the package cannot express yet
- temporary compatibility shim while converging contracts

In every case:
- keep the package as the canonical base
- document the rejected canonical lane
- record rollback / upstreaming intent
- prove compatibility with the package record shape
