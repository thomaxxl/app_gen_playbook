# Decision Log

## 2026-03-14 - Keep a rename-only lane

- Decision: treat the example as `rename-only` rather than `non-starter`
- Alternatives considered: force a broader non-starter architecture package
- Reason: the resource structure still fits the starter trio shape closely
- Downstream consequences: starter-based templates stay usable after systematic
  renaming

## 2026-03-14 - Keep `Gallery` as first-class CRUD

- Decision: `Gallery` remains a real managed resource
- Alternatives considered: singleton gallery settings
- Reason: the product supports multiple user-managed collections
- Downstream consequences: CRUD pages, rules, and navigation include `Gallery`

## 2026-03-14 - Make uploads a feature-gated capability

- Decision: uploads remain an optional feature pack rather than a core contract
- Alternatives considered: make file upload behavior part of every generated
  app
- Reason: many admin apps do not need file storage
- Downstream consequences: apps only load upload templates and contracts when
  enabled by the capability profile
