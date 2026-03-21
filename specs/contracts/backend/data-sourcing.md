# Backend Data Sourcing Contract

This file defines the backend obligations for dynamic UI data.

## Core rule

If the approved UX or architecture requires dynamic or ephemeral user-visible
data, the backend MUST expose that data through an explicit API contract.

The frontend MUST NOT be forced to embed that data in JavaScript merely
because it is not a simple CRUD row.

## Allowed backend delivery forms

The backend MAY satisfy UI data needs through one of these approved lanes:

- standard JSON:API resources
- backend-computed read-model endpoints
- JSON:API top-level or resource-level `meta`
- dedicated operational endpoints when the data is not a good fit for CRUD
  resources

For persisted database-backed tables and relationships that are user-visible or
operator-visible, the default approved lane is the standard JSON:API resource
and relationship surface exposed through SAFRS. Read-model or operational
endpoints supplement that lane when needed, but MUST NOT silently replace it
without an explicit architecture exception.

The default implementation lane for those resources is also mapped SQLAlchemy
ORM models and relationships. A custom read-model endpoint does not justify
skipping the ORM for the underlying resource when ordinary resource delivery is
still appropriate.

In SAFRS-based backends, teams MUST review the mandatory SAFRS reference
material before approving:

- any DB-backed relationship design
- any computed attribute exposure design
- any custom endpoint proposal for data that touches a persisted DB-backed
  concept

In particular:

- `jsonapi_attr` is appropriate for dynamic or computed attributes that belong
  on a resource representation even when they do not come directly from a
  database column
- `jsonapi_rpc` is appropriate for explicit backend methods or operational
  retrieval paths that do not fit cleanly as CRUD fields

Use those capabilities when they fit the contract, instead of pushing the
frontend to hardcode substitute values.

Local workspace references currently include:

- `../../references/safrs/Quickstart-FastAPI.md`
- `../../references/safrs/API-Functionality.md`
- `../../references/safrs/Relationships-and-Includes.md`
- `../../references/safrs/JSON-encoding-and-decoding.md`
- `../../references/safrs/RPC.md`
- `../../references/safrs/Instances-without-a-SQLAlchemy-model.md`

## Backend-owned dynamic classes

The backend SHOULD own and expose:

- aggregates and summary cards
- workflow status and readiness decisions
- verification or operational summaries
- histories, timelines, and blocker projections
- join-heavy or authorization-sensitive views
- freshness-sensitive counts and health indicators

## Contract rule

When the run-owned
`../../../runs/current/artifacts/architecture/data-sourcing-contract.md`
classifies a surface as `api-resource`, `api-read-model`, or `api-meta`, the
backend MUST either:

- implement that contract, or
- explicitly hand back the gap before frontend delivery

It MUST NOT rely on the frontend to fabricate those values.

## Query and freshness rule

Backend design artifacts MUST record:

- the endpoint or resource that supplies the UI data
- expected filters, sorts, or include behavior when relevant
- freshness assumptions and cache invalidation expectations when relevant
- any explicit out-of-scope dynamic asks
