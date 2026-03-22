# Playbook Integration for `safrs-jsonapi-client-frontend`

## Goal

Make `safrs-jsonapi-client` the enforced frontend adapter lane for SAFRS / ApiLogicServer apps, the same way the playbook now enforces SAFRS-first backend lanes and LogicBank-first rules lanes.

## 1. Copy the skill into the repo

Copy this directory to:

```text
skills/safrs-jsonapi-client-frontend/
```

## 2. Load the skill from the frontend Tier 1 read sets

Add:

```text
../../../skills/safrs-jsonapi-client-frontend/SKILL.md
```

to:

- `playbook/process/read-sets/frontend-design-core.md`
- `playbook/process/read-sets/frontend-implementation-core.md`

The frontend change-delta path already routes back into those core read sets, so this covers normal change work too.

## 3. Also load it for Architect work

Add the same skill path to:

- `playbook/process/read-sets/architect-authoring-core.md`
- `playbook/process/read-sets/architect-review-core.md`

The Architect already reviews SAFRS-backend and LogicBank-lane exceptions. Frontend adapter exceptions should be reviewed in the same place.

## 4. Update role files

### `playbook/roles/frontend.md`
Add a hard rule that whenever the frontend work touches:
- React-admin dataProvider setup
- `admin.yaml` normalization
- relationship UI
- search wrappers
- custom SAFRS method calls

the role must load and apply `skills/safrs-jsonapi-client-frontend/SKILL.md`.

Also state clearly:
- `safrs-jsonapi-client` is the canonical adapter
- local shared-runtime code may wrap it but must not replace it
- direct component-level `fetch(...)` is forbidden for delivered backend reads
- `execute(resource, params)` is the default lane for SAFRS RPC / service calls

### `playbook/roles/architect.md`
Add one line requiring the frontend adapter skill when approving exceptions in frontend data-access or relationship-display design.

## 5. Update frontend contracts

### `specs/contracts/frontend/dependencies.md`
Keep the approved local-materialization rule, but add:
- package source must match the intended latest-checkout convention
- `runtime-bom.md`, `package.json`, and the local `tmp/` path must stay aligned
- the package is the canonical frontend adapter, not an optional add-on

### `specs/contracts/frontend/admin-yaml-contract.md`
Keep the current authoring contract, but add:
- adaptation to `safrs-jsonapi-client` must be a thin compatibility layer
- `tab_groups` must survive into package-normalized relationship metadata
- unsupported raw keys such as ad hoc `relationships` must not become a shadow contract unless the contract is expanded deliberately

### `specs/contracts/frontend/record-shape.md`
Expand the record-shape contract so it explicitly allows and preserves:
- `ja_type`
- `attributes`
- `relationships`

while keeping scalar FK ids as the canonical write shape.

### `specs/contracts/frontend/relationship-ui.md`
Keep the current read-order rule, but make it testable:
- embedded include data
- canonical parent relationship route
- id fallback

Require the runtime metadata surface to expose enough information to attempt the parent relationship route generically.

### `specs/contracts/frontend/validation.md`
Add required checks for:
- package install source
- package-backed provider creation
- search-wrapper compatibility with package record shape
- relationship-route proof
- `execute(resource, params)` proof for representative custom-method calls
- no delivered direct-fetch bypasses

## 6. Update frontend templates

### `templates/app/frontend/package.json.md`
Keep the approved local `tmp/safrs-jsonapi-client` install model.
Also align the source-policy, local path, and documented version wording so the dependency line is not confusing.

### `templates/app/frontend/shared-runtime/admin/adminSchema.ts.md`
This is the most important fix.

Do **not** keep a permanently separate local schema system if the package already has a schema model.

Replace the current implementation with one of these:
1. a thin adapter from playbook `admin.yaml` shape into the package's expected raw shape, then call the package normalizer
2. upstream package support for the playbook authoring shape, then delete the local adapter

Do not keep long-term logic that:
- ignores `tab_groups`
- invents unsupported raw keys as a parallel contract
- redefines relationship metadata independently of the package schema

### `templates/app/frontend/shared-runtime/admin/schemaContext.tsx.md`
Create the base provider from the package (`createDataProvider(...)` or `createDataProviderSync(...)`).
Keep only genuinely local extension layers such as:
- search wrapper, if still needed
- upload-aware wrapper
- app-local auth/header glue

Do not describe the schema loader, normalizer, and SAFRS adapter as purely local forever.

### `templates/app/frontend/shared-runtime/admin/createSearchEnabledDataProvider.ts.md`
Rewrite this as a thin wrapper around the package, not a stand-alone mini client.

At minimum it must:
- preserve package normalization / hydration
- preserve `ja_type`, `attributes`, `relationships`
- preserve included data behavior
- preserve `include=...`
- preserve total extraction behavior
- keep using the package as the base provider

The current note saying the template intentionally avoids `safrs-jsonapi-client` should be removed.

### `templates/app/frontend/shared-runtime/admin/resourceMetadata.ts.md`
Add enough metadata to support canonical parent relationship-route fetches, or derive that metadata from package schema objects instead of inventing a separate model.

### `templates/app/frontend/shared-runtime/relationshipUi.tsx.md`
Make the code match the prose.
Actually implement:
1. include-first
2. parent-relationship-route second
3. `getOne(...)` fallback third

Do not leave relationship-route handling as prose only.

## 7. Add policy requirements and validators

Extend `specs/policy/requirements/frontend-core.yaml` with requirements for:
- package-backed adapter lane
- package install source
- search-wrapper compatibility
- relationship-route consumption
- no direct-fetch bypass
- `execute(resource, params)` usage for custom SAFRS methods

Add validators that inspect actual frontend templates and generated app runtime files, not just contract prose.

## 8. Add evidence / test expectations

Require at least:
- one include-hydration proof
- one searched-list proof that still preserves related-record rendering
- one relationship-dialog/tab proof using canonical relationship metadata
- one representative `execute(resource, params)` proof
- one proof that the generated frontend did not add custom helper endpoints for ordinary SAFRS relationships

## 9. Preferred convergence direction

The cleanest end-state is:

- playbook authoring contract stays stable
- a thin adapter maps it into package input shape, or the package learns that shape directly
- the package remains the canonical normalized schema + provider
- local runtime code becomes extension glue, not a second client
