# Decision Log

## 2026-03-15 - Treat CMDB as a non-starter domain

- Decision: use the non-starter adaptation lane rather than rename-only
- Alternatives considered: force the starter trio shape onto the domain
- Reason: `Service`, `ConfigurationItem`, and `OperationalStatus` are not
  rename-only substitutions of the starter example
- Downstream consequences: explicit resource classification and relationship
  inference matter more than starter-name replacement

## 2026-03-15 - Keep `OperationalStatus` as a first-class managed resource

- Decision: `OperationalStatus` remains a real managed reference resource
- Alternatives considered: hardcode operational posture rules into the
  application layer
- Reason: copied fields and validation rules are defined from managed status
  rows
- Downstream consequences: CRUD, relationship tabs, and copied-field rules all
  depend on the status resource being visible and editable

## 2026-03-15 - Use relationship tabs as baseline generated UI

- Decision: relationship tabs and related-record popups are part of the
  baseline UI for this example
- Alternatives considered: show only scalar FK fields
- Reason: operational admins need related-item visibility without leaving the
  current record
- Downstream consequences: shared-runtime relationship synthesis and dialog
  rendering are required for the example to be considered valid
