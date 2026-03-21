# Relationships and Includes

Use this note whenever the design touches foreign keys, joins, related-record
inspection, nested display, or drill-down behavior.

Required takeaway:

- real SQLAlchemy ORM relationships are the canonical source of SAFRS
  relationship URLs
- related DB-backed reads should use the parent resource relationship URL
  and/or `include=...` before any custom endpoint is considered
- if a relationship is intentionally not public, that must be a documented
  SAFRS decision, not an implicit omission followed by a substitute endpoint

Document for every relationship:

- the ORM relationship name
- the canonical relationship URL
- the canonical include path
- whether SAFRS hides it
- the chosen SAFRS relationship item mode when relevant
