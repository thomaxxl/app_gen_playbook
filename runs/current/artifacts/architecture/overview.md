owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/brief.md
unresolved:
  - none
last_updated_by: architect

# Architecture Overview

## Purpose

This run delivers a dating-profile operations admin app that stays close to
the starter trio while replacing the domain vocabulary, business rules, and
Home entry content.

## Chosen app framing

- selected framing: text-first dating-profile operations app
- rejected framing: consumer swipe/messaging product
- carried-forward assumptions:
  - the app is internal and schema-driven
  - three resources are enough for v1
  - discoverability is the main domain status concept

## Main resources

- `MatchPool`: aggregate parent for profile groups
- `MemberProfile`: primary operational record
- `ProfileStatus`: discoverability reference/status catalog

## House-style fit

- lane: `rename-only`
- rationale:
  - the resource structure still matches parent + child + status
  - no extra transactional resource is needed
  - custom logic remains modest and rule-friendly

## Frontend shape

- standard schema-driven CRUD shell: yes
- required custom routes or dashboards:
  - `Home` page only
- in-admin entry route:
  - `/admin-app/#/Home`

## Backend shape

- expected backend:
  - FastAPI + SAFRS + SQLAlchemy + LogicBank + SQLite
- bootstrap shape:
  - close to starter
  - pool/profile/status sample records seeded on empty DB

## Rules shape

- LogicBank rules expected: yes
- derived/constraint-heavy areas:
  - copied status fields on `MemberProfile`
  - `MatchPool` aggregates
  - discoverable approval constraint

## Singleton versus first-class resource decisions

- `MatchPool` could have been a hidden enum or singleton grouping config
  surface; it remains a first-class CRUD resource because operations staff
  need multiple named pools with visible aggregates
- `ProfileStatus` remains a first-class reference resource instead of a
  hard-coded enum so the CRUD contract stays explicit

## Custom pages

- `Home` is the only custom page and remains inside the React-admin shell
- no `Landing.tsx` route is required

## Out-of-scope architectural decisions

- auth and authorization
- background jobs
- file uploads and stored-file metadata subsystem
- packaged same-origin deployment verification
