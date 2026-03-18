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
