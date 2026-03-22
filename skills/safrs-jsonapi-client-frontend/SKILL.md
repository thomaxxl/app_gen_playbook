# SAFRS JSON:API React-Admin Frontend Skill

## Purpose

Use this skill whenever the playbook is designing, implementing, reviewing, or validating a React-admin frontend that talks to a SAFRS / ApiLogicServer backend.

This skill exists to stop the frontend from inventing a parallel JSON:API client, a parallel schema format, or ad hoc relationship fetch behavior when `safrs-jsonapi-client` already provides the intended adapter layer.

## Default lane

For SAFRS / ApiLogicServer frontends, the canonical data-provider lane is:

1. materialize `safrs-jsonapi-client` from the approved latest-upstream checkout policy recorded in `runtime-bom.md`, normally into local `app/tmp/safrs-jsonapi-client`
2. use the package's `createDataProvider(...)` / `createDataProviderSync(...)`
3. use the package's `normalizeAdminYaml(...)` schema model as the canonical normalized schema shape
4. keep React-admin components behind the approved `dataProvider`
5. use `execute(resource, params)` for SAFRS RPC-style methods or raw JSON service calls

Do **not** hand-roll a separate JSON:API client unless the exception is documented.

## Hard rules

### 1. The package is the canonical adapter
If the backend is SAFRS / ApiLogicServer and the frontend is React-admin, `safrs-jsonapi-client` is the default adapter. Local wrappers may extend it, but they must not replace it.

### 2. Preserve the package record shape
Any wrapper must preserve the package-compatible normalized record shape:
- `id`
- `ja_type`
- `attributes`
- `relationships`
- flattened attributes at top level
- optional embedded relationship objects at `record[relationshipName]` or `record["rel_" + relationshipName]`

A wrapper that drops `ja_type`, `attributes`, `relationships`, or `included` hydration is not a compatible wrapper. It is a replacement client.

### 3. Preserve relationship metadata from the authoring contract
The playbook's `admin.yaml` authoring contract is allowed to differ from the package's current raw input shape, but the adapter layer must preserve:
- `endpoint`
- `user_key`
- searchable fields
- `tab_groups`
- relationship ordering
- relationship labels
- relationship visibility flags

If the current package normalizer expects a different raw shape, create a thin adapter that converts the playbook authoring shape into the package input shape. Do not replace the package schema model with a separate local schema system.

### 4. Search wrappers are an exception lane
`filter.q` is currently a package backlog item. If the run needs grouped full-text search before upstream support exists, a wrapper is allowed, but it must:
- delegate to package query builders where possible
- preserve package normalization / hydration
- preserve package record shape
- preserve `include=...`
- stay behind the same `dataProvider` boundary

Do not build a search-only mini client that returns a different record shape.

### 5. Relationship reads follow one order
For related-record display:
1. use embedded related objects from canonical `include=...`
2. otherwise use canonical SAFRS parent relationship routes
3. only then fall back to `dataProvider.getOne(...)` by id

The runtime must not invent side endpoints for ordinary DB-backed related data that SAFRS already exposes.

### 6. Use `execute(resource, params)` for custom methods
For `@jsonapi_rpc`, SAFRS custom methods, or non-resource JSON service calls, use the adapter's `execute(resource, params)` method instead of component-level `fetch(...)`.

### 7. No component-level API bypass
Frontend components must not call backend APIs directly for delivered app behavior. If the adapter shape is insufficient, extend the adapter or escalate the gap.

### 8. Install from the approved local materialization source
The generated app MUST install `safrs-jsonapi-client` from the approved local
checkout path recorded in `runtime-bom.md`, normally `file:../tmp/safrs-jsonapi-client`,
after the playbook materializes the approved latest-upstream checkout into `app/tmp/`.

Do not use:
- floating git dependencies
- raw source archives
- `codeload` snapshots
- a different local checkout than the approved repo source policy

## Required outputs and evidence

When this skill is used, the run should be able to point to:
- `runtime-bom.md` showing the approved package source
- frontend runtime files proving the package adapter is canonical
- proof that relationship tabs/dialogs use include / relationship-route / id-fallback order
- proof that search wrappers preserve package record shape
- proof that `tab_groups` remains authoritative for relationship UI
- proof that custom SAFRS methods use `execute(resource, params)` instead of component-level fetches

## Anti-patterns

Reject these patterns unless there is a written exception:
- a local JSON:API normalizer that ignores package schema semantics
- a search wrapper that only returns `{ id, ...attributes }`
- relationship UI that claims to prefer relationship routes but only implements `getOne(...)`
- custom pages that call `fetch(...)` because the adapter was not extended
- runtime logic that treats `tab_groups` as generator-only decoration
- direct dependence on unsupported raw `admin.yaml` keys not covered by the frontend contract
- package install URLs that point to raw source archives rather than packed release artifacts

## Review questions

Before approving a frontend data-access design, answer all of these:

1. Why is `safrs-jsonapi-client` not sufficient as the primary adapter?
2. If there is a wrapper, which package behaviors does it preserve verbatim?
3. Does the wrapper preserve `ja_type`, `attributes`, `relationships`, and included hydration?
4. How does the runtime preserve `tab_groups` and relationship ordering?
5. Where is the canonical parent relationship route used?
6. How are SAFRS RPC-style methods executed?
7. What tests prove the adapter behavior on:
   - include hydration
   - relationship tabs/dialogs
   - search with `q`
   - write flows
   - upload-aware wrapping, if enabled

## Files in this skill

- `reference/adapter-decision-tree.md`
- `reference/record-shape-contract.md`
- `templates/frontend-adapter-exception-template.md`
- `templates/frontend-adapter-proof-checklist.md`
- `integration/PLAYBOOK_INTEGRATION.md`
