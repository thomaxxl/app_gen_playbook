owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - input-interpretation.md
unresolved:
  - none
last_updated_by: product_manager

# Product Brief

## Problem Statement

Airport operations staff need a single place to manage gates, flights, and
departure status without relying on spreadsheets or disconnected updates.

## Primary Users

- operations supervisor
- gate coordinator
- dispatch analyst

## App Class

Admin CRUD app with business rules and a custom landing/dashboard page.

## Scope

- configure gates
- configure flight statuses
- create and update outbound flights
- assign flights to gates
- track scheduled departure, actual departure, and delay minutes
- show an airport operations landing page with departure and gate summaries

## Out Of Scope

- passenger servicing
- crew management
- baggage handling
- arrivals
- live third-party integrations
- notifications
- auth/permissions

## Success Definition

The app is successful if a coordinator can:

- open the landing page and immediately see delayed and departed flights
- navigate into CRUD screens for gates, flights, and statuses
- search flights by flight number or destination
- reassign a flight to a gate
- mark a flight as departed only when an actual departure time is present
- trust gate summary metrics to update automatically when flights change
