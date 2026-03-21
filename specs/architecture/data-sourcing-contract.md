owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - ../product/acceptance-criteria.md
  - ../product/workflows.md
  - ../product/custom-pages.md
  - ../architecture/route-and-entry-model.md
unresolved:
  - replace with run-specific data ownership and retrieval decisions
last_updated_by: playbook

# Data Sourcing Contract Template

This file is a generic template. The Architect role MUST create the run-owned
version at `../../runs/current/artifacts/architecture/data-sourcing-contract.md`.

## Purpose

The real artifact MUST make data ownership explicit across Architecture,
Frontend, and Backend.

It exists to prevent user-visible runtime data from being silently hardcoded
into frontend JavaScript when that data should come from the backend.

## Classification rules

The real artifact MUST classify every user-visible data requirement for entry
pages, custom views, dashboards, generated CRUD summaries, and other
non-trivial surfaces as exactly one of:

- `api-resource`
  standard resource data fetched through the normal API/resource lane
- `api-read-model`
  backend-computed or aggregated dynamic data exposed for UI consumption
- `api-meta`
  dynamic non-resource metadata exposed by the backend or JSON:API payloads
- `frontend-static-config`
  static labels, route maps, icon maps, chart options without live values,
  display-only configuration, and fixed explanatory copy
- `frontend-local-ui-state`
  transient client-only state such as open panels, unsaved form state, local
  filters, selected tabs, and optimistic in-flight UI state

Anything that varies by database contents, workflow progress, run state, time,
user, permissions, environment health, queue depth, verification status,
history, or backend-derived calculations MUST NOT be classified as
`frontend-static-config`.

If a user-visible or operator-visible datum is naturally owned by a persisted
database-backed table row or relationship, the default classification is
`api-resource`.

For such data, the default backend implementation lane is also a mapped
SQLAlchemy ORM model and relationship. The Architect MAY approve a different
implementation lane only when the run-owned artifacts record the reason and
replacement contract.

The Architect MAY classify such data as `api-read-model` or `api-meta` only
when the run-owned artifacts record why ordinary SAFRS resource exposure is not
the right primary contract for that surface.

For any persisted DB-backed entity or relationship that users or operators need
to list, inspect, filter, sort, include, or drill into, the real artifact MUST
also record why the need was not satisfied by:

- the normal SAFRS resource endpoint
- the normal SAFRS relationship endpoint
- `include=...`
- `@jsonapi_attr`
- `@jsonapi_rpc`

`JABase` or another stateless/service endpoint is an explicit exception lane
and requires a named architecture exception.

## Required table

The real artifact MUST include a table with at least these columns:

| Surface | User-visible datum or section | Classification | Authoritative source contract | Retrieval path | Freshness or invalidation notes | Frontend-built fallback allowed | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | api-resource/api-read-model/api-meta/frontend-static-config/frontend-local-ui-state | replace | replace | replace | yes/no with reason | replace |

## Required sections

The real artifact MUST define:

- which surfaces are backed only by CRUD resources
- which surfaces require backend-computed read models, aggregate endpoints, or
  API metadata
- which DB-backed tables and relationships default to SAFRS resource exposure
  and which documented exceptions are allowed to bypass that default
- for every documented exception, which canonical SAFRS lane was rejected and
  why
- when SAFRS-native mechanisms such as `jsonapi_attr` or `jsonapi_rpc` are the
  preferred way to expose dynamic non-column or operational data
- which values MAY stay static in the frontend bundle
- which values are local UI state only and MUST NOT be mistaken for backend
  truth
- what the frontend should do when a required dynamic data source is missing or
  blocked
- whether caching or stale-while-revalidate behavior is acceptable per surface
- which contracts must be updated together when a surface's data needs change

## Delivery rule

If the approved UX requires dynamic or ephemeral data and the backend does not
yet expose it, the frontend MUST escalate the contract gap. It MUST NOT ship a
hardcoded substitute as if it were live application data.
