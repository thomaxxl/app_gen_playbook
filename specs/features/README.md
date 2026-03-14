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

Available packs:

- [uploads/README.md](uploads/README.md)
- [d3-custom-views/README.md](d3-custom-views/README.md)
- [reporting/README.md](reporting/README.md)
- [background-jobs/README.md](background-jobs/README.md)
