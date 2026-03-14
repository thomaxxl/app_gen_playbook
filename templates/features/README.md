# Feature Templates

This directory contains feature-gated template entrypoints.

Core templates still live under:

- `../app/`

Feature template entrypoints live here so roles can load only the enabled
capability packs from the run-owned capability profile.

Rules:

- disabled feature-template packs MUST NOT be loaded
- feature-template packs MAY point at concrete target-file snippets under
  `../app/` when those snippets already exist there
- the feature entrypoint is the canonical load boundary, not the scattered
  target-path snippets

Maturity rule:

- `uploads/` is the only feature-template pack that is currently documented as
  implementation-ready
- the other feature-template packs remain placeholders and MUST stay disabled
  or undecided unless the current run expands them deliberately

Segmentation rule:

- the existence of a no-op extension point in a core template does not, by
  itself, enable the feature
- the feature remains disabled until the capability profile enables it and the
  feature-owned template entrypoint is loaded

Available packs:

- [uploads/README.md](uploads/README.md)
- [d3-custom-views/README.md](d3-custom-views/README.md)
- [reporting/README.md](reporting/README.md)
- [background-jobs/README.md](background-jobs/README.md)
