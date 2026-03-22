# Database Changes

Portable summary of the database-shape implications emphasized by the
playbook:

- derived targets must be real mapped model attributes
- aggregates need explicit persisted target columns
- request/audit and allocation patterns may require new tables and junctions
- when a run adds derived columns, the design must record schema
  prerequisites, migration needs, and backfill expectations
