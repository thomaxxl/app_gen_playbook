# Feature Packs

This directory contains optional capability packs.

These packs are NOT core contracts.

They MUST be loaded only when the run-owned capability profile enables them.

Primary gating artifacts:

- `../../runs/current/artifacts/architecture/capability-profile.md`
- `../../runs/current/artifacts/architecture/load-plan.md`

Rules:

- disabled feature packs MUST NOT be loaded
- undecided feature packs MUST NOT be used as design input
- enabled feature packs MAY reference lower-level support contracts under
  `../contracts/`
- a feature pack MUST declare:
  - feature name
  - load condition
  - owning roles
  - dependent core contracts

Maturity rule:

- `uploads/` is the current fully documented implementation feature pack
- `ux-measurement/` is a documented optional UX review and validation pack,
  but it does not imply prebuilt starter instrumentation templates
- `d3-custom-views/`, `reporting/`, and `background-jobs/` are placeholder
  packs only
- placeholder packs MUST remain `disabled` or `undecided` in the capability
  profile unless the current run explicitly expands them into real
  run-specific feature work
- agents MUST NOT treat placeholder pack names as proof that the feature is
  already fully specified

Segmentation rule:

- feature-pack segmentation controls reading, planning, copy scope, and
  activation
- it MAY coexist with baseline no-op extension points in core templates
- agents MUST rely on the feature-pack docs to determine whether a feature is
  fully isolated or merely activation-gated

Available packs:

- [uploads/README.md](uploads/README.md)
- [ux-measurement/README.md](ux-measurement/README.md)
- [d3-custom-views/README.md](d3-custom-views/README.md)
- [reporting/README.md](reporting/README.md)
- [background-jobs/README.md](background-jobs/README.md)
