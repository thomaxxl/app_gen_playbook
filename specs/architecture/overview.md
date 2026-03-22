owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - ../product/brief.md
  - ../product/conceptual-domain-model.md
unresolved:
  - replace with run-specific architecture overview
last_updated_by: playbook

# Architecture Overview Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/overview.md`.

## Purpose

State the chosen app framing in one short paragraph.

## Chosen app framing

The real artifact MUST state:

- the selected first-version framing
- what adjacent framings were rejected
- any architectural assumptions carried forward from Product Manager artifacts

## Main resources

The real artifact MUST name the main business resources and the reason they
exist.

## Domain areas and concept interpretation

The real artifact MUST define:

- the main domain areas carried forward from `conceptual-domain-model.md`
- any terminology split that affects architecture boundaries
- any concept that maps non-trivially into the application resource model

## Concept-to-resource mapping notes

The real artifact MUST record:

- concepts that become first-class resources
- concepts that become singleton/settings handling
- concepts that become supporting transaction records
- concepts that remain read-model/dashboard only
- any one-to-many or many-to-one mapping between conceptual concepts and app
  resources

## House-style fit

The real artifact MUST state whether the run is:

- starter
- rename-only
- non-starter

## Frontend shape

The real artifact MUST define:

- whether the app keeps the standard schema-driven CRUD shell
- required custom routes or dashboards
- the in-admin entry route

## Backend shape

The real artifact MUST define:

- the expected SAFRS/FastAPI backend shape
- whether bootstrap stays close to starter or needs project-specific changes

## Rules shape

The real artifact MUST define:

- whether LogicBank rules are expected
- which derived or constraint-heavy areas need later rule mapping

## Singleton versus first-class resource decisions

The real artifact MUST record any concept that could plausibly be modeled as:

- singleton/settings
- first-class CRUD resource

For each such concept, the real artifact MUST record the selected treatment,
reason, and downstream consequences.

## Custom pages

The real artifact MUST identify custom pages that affect architecture rather
than merely presentation.

## Out-of-scope architectural decisions

The real artifact MUST record intentionally deferred architectural choices.

The real artifact MUST NOT rely on a narrative-only summary. It MUST be
specific enough that later roles can stop guessing about:

- framing
- main resources
- frontend style
- backend style
- rules usage
- packaging model
