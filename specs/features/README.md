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
  - maturity level
  - segmentation model

The canonical feature catalog is:

- [catalog.md](catalog.md)

Placeholder packs MUST remain `disabled` or `undecided` in the capability
profile unless the current run explicitly expands them into real run-specific
feature work.

Segmentation rule:

- feature-pack segmentation controls reading, planning, copy scope, and
  activation
- it MAY coexist with baseline no-op extension points in core templates
- agents MUST rely on the feature-pack docs to determine whether a feature is
  fully isolated or merely activation-gated

See also:

- `../../playbook/process/segmentation-model.md`

Available packs:

- [uploads/README.md](uploads/README.md)
- [ux-measurement/README.md](ux-measurement/README.md)
- [d3-custom-views/README.md](d3-custom-views/README.md)
- [reporting/README.md](reporting/README.md)
- [background-jobs/README.md](background-jobs/README.md)
