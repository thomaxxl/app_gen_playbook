# SAFRS-Family Bug Ledger

This playbook is also a SAFRS-family integration testbed.

When playbook development or a generated-app run exposes a likely upstream bug
in `safrs`, `safrs-jsonapi-client`, `logicbank`, or a closely related shared
dependency, record it here.

Do not normalize a local workaround as if the framework/client/rules-engine
behavior were acceptable. A temporary local containment may be used only to
confirm or isolate the bug. It does not clear a gate, does not become the
default baseline, and does not replace reporting the defect here.

## When To Log A Bug

Create or update an entry when any of these are true:

- SAFRS behavior appears broken, incomplete, or inconsistent with the intended
  contract
- `safrs-jsonapi-client` behavior forces app-local adapter work that looks like
  an upstream defect rather than app-specific configuration
- LogicBank behavior, callback shape, event timing, or nested-row behavior
  appears incorrect or inconsistent with the installed runtime
- a shared upstream package bug materially blocks backend, frontend, rules, or
  packaging work in the playbook

Do not use this ledger for ordinary generated-app bugs that are specific to one
run or one app implementation.

## Entry Template

Use this shape for each bug entry.

```md
## BUG-YYYYMMDD-<slug>

- Date:
- Component: `safrs` | `safrs-jsonapi-client` | `logicbank` | `<other>`
- Status: `open` | `investigating` | `upstream-filed` | `contained-for-diagnosis` | `resolved`
- Summary:
- Impact:
- First observed in:
- Expected behavior:
- Observed behavior:
- Minimal reproduction:
- Local evidence:
- Temporary containment:
- Upstream reference:
- Notes:
```

## Open Bugs

No tracked SAFRS-family bugs are recorded yet.
