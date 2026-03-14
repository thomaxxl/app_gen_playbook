owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - input-interpretation.md
  - research-notes.md
unresolved:
  - none
last_updated_by: product_manager

# Airport Ops Control Brief

## Problem statement

Airport duty managers need a compact admin app to manage departure gates,
scheduled flights, and operational statuses without relying on scattered
spreadsheets or free-text updates.

## Primary users

- airport duty manager
- gate coordinator
- operations supervisor

## App class

Schema-driven admin app with one dashboard page, three resources, and a small
set of backend-enforced operational rules.

## In-scope behavior

- manage gates and their static metadata
- create, edit, search, and review flights assigned to gates
- manage reusable flight-status definitions
- surface active-flight and delay metrics on dashboard pages
- enforce delay-reason and departure-timestamp rules

## First-version scope boundary

The first version supports internal airport-operations coordination for
departures only. It does not attempt to become a passenger app, airline
system, or real-time ATC console.

## Out-of-scope behavior

- check-in and boarding-pass issuance
- baggage or cargo workflows
- runway sequencing
- aircraft maintenance
- billing and vendor procurement
- external feed ingestion

## Explicit exclusions

- no uploads
- no reporting feature pack
- no background jobs
- no D3 custom views
- no same-origin packaging work in this run
