# Frontend Data Sourcing Contract

This file defines what kinds of user-visible data MAY live in the frontend
bundle and what kinds MUST come from the backend.

## Core rule

User-visible data that is dynamic, ephemeral, or environment-specific MUST be
fetched from the backend through the approved API surface.

Examples include:

- domain records and related labels
- dashboard metrics, counts, summaries, and histories
- workflow status, blockers, verification state, and operational health
- queue depth, current phase, run summaries, and time-varying cards
- any value that can change because of backend state, time, permissions, or
  another actor's actions

## What MAY be static in frontend JavaScript

The frontend MAY keep only these classes of built-in values in the bundle:

- static route definitions and navigation metadata
- icon mappings
- page-shell composition
- fixed explanatory copy approved by product and UX
- field-order, section-order, and layout descriptors
- chart or visualization configuration that does not include live values
- local UI defaults such as selected tabs, expansion defaults, and empty local
  filters

## Forbidden delivery pattern

The frontend MUST NOT ship local literals that pretend to be live backend
truth, including:

- hardcoded record rows
- hardcoded blockers, queues, or activity timelines
- hardcoded summary cards or metric values
- hardcoded history summaries
- hardcoded workflow status or verification outcomes
- fallback datasets rendered as if they were the current environment's state

Tests, storybook fixtures, and clearly labeled non-delivery prototypes are not
the same as production delivery surfaces.

## Retrieval rule

Frontend components MUST fetch API-backed data through the app's approved
React-admin dataProvider layer.

This applies to:

- generated CRUD pages
- `Home.tsx`
- `Landing.tsx`
- dashboards
- custom views
- relationship dialogs and tabs
- any other frontend surface that retrieves backend/API data

Component-level `fetch(...)`, ad hoc API client wrappers, or one-off query
helpers are not the default contract for delivery code.

If a surface needs data that is not a standard CRUD call, the frontend MUST
extend or reuse the approved dataProvider contract for that API lane rather
than bypassing it from the component tree.

When a surface needs backend-computed aggregates or non-CRUD operational
views, the frontend MUST rely on an approved backend read-model or metadata
contract, and it MUST still retrieve that data through the approved
dataProvider contract rather than direct component-level fetch calls.

## Source of truth

The run-owned authoritative mapping lives in:

- `../../runs/current/artifacts/architecture/data-sourcing-contract.md`

If the current implementation need is not covered there, the frontend MUST
escalate to Architect or Backend instead of hardcoding substitute data.
