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

Custom pages and dashboards SHOULD use the app's approved data-provider or API
client layer, not ad hoc local constants, for dynamic data retrieval.

When a surface needs backend-computed aggregates or non-CRUD operational
views, the frontend MUST rely on an approved backend read-model or metadata
contract rather than reconstructing or inventing those values locally.

## Source of truth

The run-owned authoritative mapping lives in:

- `../../runs/current/artifacts/architecture/data-sourcing-contract.md`

If the current implementation need is not covered there, the frontend MUST
escalate to Architect or Backend instead of hardcoding substitute data.
