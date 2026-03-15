owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Decision Log

## 2026-03-14 - Choose dating-profile operations framing

- decision: interpret the sparse brief as an internal dating-profile
  operations app
- alternatives considered:
  - consumer dating product
  - match-review transaction console
- reason:
  - best fit for schema-driven admin house style
- downstream consequences:
  - `MemberProfile` becomes the primary workflow resource
  - `Home` emphasizes profile review

## 2026-03-14 - Use rename-only lane

- decision: keep the parent + child + status trio shape
- alternatives considered:
  - expand to a non-starter pairing model
- reason:
  - the sparse brief does not justify extra workflow resources
- downstream consequences:
  - starter-style aggregate and copy rules remain valid
  - wrapper/resource replacement sweep is still required

## 2026-03-14 - Defer uploads

- decision: keep v1 text-first and disable uploads
- alternatives considered:
  - enable the uploads pack and stored-file subsystem
- reason:
  - uploads would materially broaden scope and are not necessary to satisfy
    the brief
- downstream consequences:
  - no stored-file resources
  - no upload-aware data-provider work

## 2026-03-14 - Home as dashboard

- decision: use `Home` as the primary entry dashboard and omit `Landing`
- alternatives considered:
  - `Home + Landing`
- reason:
  - one in-admin entry surface is enough for this resource-light app
- downstream consequences:
  - `Home` must expose summary cues and quick actions directly
