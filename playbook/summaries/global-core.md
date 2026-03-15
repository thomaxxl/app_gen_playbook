# Global Core Summary

Load this for every role before any task-specific expansion.

This file states the invariant operating rules:

- segmentation exists to reduce context overload
- load only the current role's allowed core docs plus the current run's
  capability gates
- disabled or undecided feature packs MUST NOT be loaded, copied, or used as
  design input
- ownership stays strict: write only the current role's artifacts and local
  `app/` scope assigned to that role
- do not invent cross-layer product, architecture, UX, backend, or packaging
  decisions silently
- persistent run-owned artifacts must use the canonical metadata block
- record assumptions, handoffs, and verification in persistent artifacts or
  role `context.md`
- a generated app lives in local ignored `app/`; the playbook source is not a
  scratch space

This file does not define phase details, role-specific read sets, or optional
capability behavior.

Load next:

- `process-core.md`
- the current role summary
- the current role's Tier 1 read set
- `../process/context-budgets.md` when maintaining the playbook
