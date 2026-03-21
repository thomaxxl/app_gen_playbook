---
name: safrs-api-design
description: Use when backend or architecture work touches persisted DB-backed API design in a SAFRS-based app: SQLAlchemy model exposure, relationships, include paths, jsonapi_attr, jsonapi_rpc, or deciding whether a custom endpoint is justified. This skill exists to stop FK-first or ad hoc endpoint design from replacing normal SAFRS resource and relationship surfaces.
---
# SAFRS API Design

Use this skill when the task is any of the following:

- design or review a backend API for persisted DB-backed entities
- decide how related records should be exposed
- check whether a custom endpoint is allowed in a SAFRS app
- map frontend related-record needs to backend API shape
- expose computed or operational data without inventing a new ad hoc route
- review a generated app that seems to expose database information on the wrong endpoint

This skill is guidance. Enforcement still belongs in playbook contracts, policy, task bundles, validation, and quality gates.

## Non-negotiable default

For persisted DB-backed tables and relationships that users or operators need to list, show, filter, sort, include, or drill into, the canonical API lane is:

1. real SQLAlchemy ORM models and relationships
2. real SAFRS exposure
3. normal SAFRS resource, relationship, and include semantics

Custom read-model, ops, summary, or service endpoints may supplement that surface, but they must not silently replace it.

Do not invent sibling endpoints that re-expose related database data outside the owning resource when SAFRS already has a standard lane for that need.

Bad pattern:

- `/api/orders/{id}/customer_summary`
- `/api/item_status_info/{id}`
- `/api/project_members_lookup`

when the real need is one of these:

- an ORM relationship
- a SAFRS relationship endpoint
- `include=...`
- a computed resource field via `@jsonapi_attr`
- an explicit action via `@jsonapi_rpc`

## Decision order

Resolve every request in this order.

### 1. Real resource

Question:

- Is this persisted row data that should exist as a first-class entity?

If yes:

- map it as a real SQLAlchemy model
- expose it through SAFRS
- make it discoverable in live `/jsonapi.json`

### 2. Real relationship

Question:

- Is this data really a relationship between exposed resources?

If yes:

- define a real SQLAlchemy relationship on the model
- let SAFRS generate the relationship path
- document the relationship name exactly as the ORM name
- use the relationship path and/or `include=...` as the canonical read surface

Do not treat a scalar foreign key as the main relationship API.
A scalar foreign key may remain a write convenience, but ordinary relational reads should come from the actual SAFRS relationship surface.

### 3. Include path

Question:

- Does the frontend or another consumer simply need related data embedded with the parent resource?

If yes:

- prefer `include=relationship_name`
- allow nested include paths only when the full ORM relationship chain exists
- document the include path in query behavior and test it live

Do not create a custom endpoint just because the UI wants one screen with parent and related data together.

### 4. Computed resource field

Question:

- Does the API need a derived field that logically belongs on the resource representation?

If yes:

- use `@jsonapi_attr`
- keep it on the resource instead of inventing a side endpoint
- remember that filtering and sorting are not automatic for `@jsonapi_attr`; use a real column or an explicit query strategy when those behaviors are required

Good fits:

- labels
- counters already derivable from resource state
- masked or facade fields
- human-readable summaries that belong with the resource

### 5. Explicit action or operation

Question:

- Is the API need an operation rather than a resource or relationship read?

If yes:

- use `@jsonapi_rpc`
- choose class-level RPC for collection-scoped actions
- choose instance-level RPC for object-scoped actions

Good fits:

- retry sync
- send mail
- bulk transition
- re-run a workflow step

### 6. Stateless or custom endpoint

Question:

- Is the need truly not a resource, relationship, include, computed attribute, or RPC?

Only then consider:

- JABase / stateless SAFRS endpoint
- custom read-model endpoint
- custom ops endpoint

This requires an explicit architecture exception.

Use this lane for things like:

- cross-resource dashboard aggregates that do not belong to one resource
- service-style integrations
- non-ORM operational APIs
- responses that are intentionally not resource-shaped

Do not use this lane merely because the author did not model the relationship.

## Required inputs when using this skill

Load the smallest set that matches the task, then apply this skill.

At minimum, prefer these inputs when they exist:

- the current role summary and stage-specific read set
- the active backend or architect task bundle
- `runs/current/artifacts/architecture/data-sourcing-contract.md`
- `runs/current/artifacts/architecture/resource-classification.md`
- `runs/current/artifacts/architecture/integration-boundary.md`
- `runs/current/artifacts/backend-design/model-design.md`
- `runs/current/artifacts/backend-design/resource-exposure-policy.md`
- `runs/current/artifacts/backend-design/relationship-map.md`
- `runs/current/artifacts/backend-design/query-behavior.md`
- `runs/current/artifacts/backend-design/test-plan.md`
- the live `/jsonapi.json` or live OpenAPI document if implementation already exists

When the choice is unclear, review the SAFRS documentation for:

- Quickstart FastAPI
- Relationships and Includes
- JSON encoding and decoding
- RPC
- Instances without a SQLAlchemy model

## Workflow

### Step 1. Inventory the real data need

Write down:

- what the UI or caller needs to display or mutate
- whether the data is persisted or derived
- whether it belongs to a resource, relationship, attribute, or action
- whether filtering, sorting, include support, or item routes are required

Do not start by inventing endpoint names.

### Step 2. Choose the SAFRS lane first

Map the need to exactly one primary lane:

- resource
- relationship
- include
- `@jsonapi_attr`
- `@jsonapi_rpc`
- exception lane

If you choose the exception lane, you must write down why each earlier lane was rejected.

### Step 3. Update the run-owned artifacts

Record the decision in the normal backend-design artifacts.

At minimum:

- `model-design.md`: model exists, ORM relationship names, any `jsonapi_attr`, any `jsonapi_rpc`
- `resource-exposure-policy.md`: canonical resource path and any supplemental endpoints
- `relationship-map.md`: canonical relationship URL, include path, visibility choice, item-mode choice
- `query-behavior.md`: allowed include paths and whether they come from real ORM relationships
- `test-plan.md`: live proof for relationship routes, include paths, computed attrs, RPC endpoints, and exception evidence

### Step 4. Reject the common anti-patterns

Reject the design if any of these are true:

- a DB relationship is represented only by a scalar FK and a side endpoint
- related record tabs depend on a custom endpoint even though the relation exists in the domain
- a summary endpoint exists only because the author skipped the ORM relationship
- a fake `/jsonapi.json` exists without real SAFRS model exposure
- a normal DB-backed entity is delivered through raw SQL + hand-built JSON without an approved exception
- a hidden relationship is replaced with a custom endpoint rather than documented with SAFRS visibility controls

### Step 5. Verify the live API shape

For ordinary DB-backed resources and relationships, verify all of these:

- the resource exists in live `/jsonapi.json`
- the relationship path exists when the design says it is exposed
- the declared `include=...` path works live
- hidden relationships are hidden intentionally
- any `relationship_item_mode` choice matches the intended runtime behavior
- `@jsonapi_attr` fields appear on the resource where expected
- `@jsonapi_rpc` methods appear on the right collection or instance path

### Step 6. Produce a blunt verdict

State one of these outcomes clearly:

- keep the standard SAFRS resource/relationship design
- move the data into `@jsonapi_attr`
- move the operation into `@jsonapi_rpc`
- keep the custom endpoint, but only with a documented exception and replacement contract
- reject the current design because it replaced a normal SAFRS lane with an invented one

## Relationship rules

When a real relationship exists:

- the ORM relationship name is the source of truth
- the relationship must be documented exactly once in the relationship map
- include paths must use that same name
- the frontend should prefer relationship routes or `include=...` for relational reads
- scalar FK values may remain form inputs, but they are not the canonical read-side contract

If a relationship should not be public:

- hide or restrict it with SAFRS controls such as `relationship.expose = False`
- document the reason
- do not quietly omit it and then recreate the same data on a random custom endpoint

## What to do with computed data

Use `@jsonapi_attr` when the value belongs on the resource.

Examples:

- `display_name`
- `status_label`
- `masked_secret`
- `health_summary`

Do not use `@jsonapi_attr` as a substitute for a relationship.
If the field must support filtering or sorting, verify whether it really needs to be a real column instead.

## What to do with operational actions

Use `@jsonapi_rpc` when the caller is asking the server to do something.

Examples:

- `/Orders/add_order`
- `/People/{id}/send_mail`
- `/Imports/{id}/retry`

Do not use RPC to replace normal relationship reads or ordinary CRUD.

## Exception test

A custom endpoint is acceptable only when all of these are true:

- the need is not well represented as a resource
- it is not just a relationship read under a parent resource
- it is not satisfied by `include=...`
- it is not a resource field that belongs in `@jsonapi_attr`
- it is not an explicit action that belongs in `@jsonapi_rpc`
- the architecture and backend-design artifacts record the exception and replacement contract
- verification covers both the custom endpoint and the surrounding canonical SAFRS surface

Use `templates/architecture-exception-template.md` when you need that exception record.

## Minimum evidence expected from this skill

When this skill materially affects the design, expect to produce:

- a relationship map entry for each exposed DB relationship
- an include-path entry for each UI-visible relationship include
- at least one live proof of a relationship route or item route when relevant
- at least one live `include=...` proof for each required include path
- one test or proof for each `@jsonapi_attr` or `@jsonapi_rpc` introduced
- an exception record for any custom DB-backed endpoint that is not purely supplemental

Use `templates/relationship-proof-checklist.md` to structure that proof.

## Quick examples

### Example: order page needs customer details

Correct lane:

- `Order.customer` ORM relationship
- SAFRS relationship path for `customer`
- `include=customer` when the UI wants one request

Incorrect lane:

- `/api/order_customer_summary/{order_id}`

### Example: resource needs a human-friendly health string

Correct lane:

- `@jsonapi_attr`

Incorrect lane:

- `/api/device_health_label/{id}`

### Example: user clicks “retry import”

Correct lane:

- `@jsonapi_rpc`

Incorrect lane:

- custom route created only because the author did not check RPC support first

### Example: dashboard shows global rollups across many resources

Possible exception lane:

- custom read-model or JABase endpoint

But only after documenting why the requirement is not a resource, relationship, include, attribute, or RPC concern.
