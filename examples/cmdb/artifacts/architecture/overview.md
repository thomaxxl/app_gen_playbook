# Architecture Overview

## Purpose

CMDB Operations Console is a SAFRS/FastAPI admin app for managing services,
configuration items, and operational-status definitions.

## Chosen app framing

The preserved example is framed as an internal operations/admin tool with
derived rollups and relationship-heavy inspection flows.

## Main resources

- `Service`
- `ConfigurationItem`
- `OperationalStatus`

## House-style fit

This example uses the non-starter lane. It keeps the playbook runtime and UX
contracts but replaces the starter domain and naming entirely.

## Frontend shape

- schema-driven React-Admin CRUD pages remain the default shell
- `/app/#/Home` is the required in-admin entry page
- `/app/#/Landing` is a custom no-layout dashboard route
- relationship tabs and related-record popups are baseline generated behavior

## Backend shape

- FastAPI + SAFRS + SQLite
- bootstrap seeds services, configuration items, and operational statuses
- derived service rollups and copied status fields are LogicBank-managed

## Rules shape

- LogicBank derives service counts and risk totals
- LogicBank copies operational fields from `OperationalStatus` to
  `ConfigurationItem`
- LogicBank enforces production verification and risk-score constraints

## Singleton versus first-class resource decisions

No singleton/settings resource is used in this example. `Service` and
`OperationalStatus` remain first-class resources because the app exposes and
manages both directly.

## Custom pages

- `Home.tsx` for the required in-admin entry page
- `Landing.tsx` for dashboard-style CMDB summary

## Out-of-scope architectural decisions

- no external CMDB sync
- no multi-tenant ownership model
- no public-facing site
