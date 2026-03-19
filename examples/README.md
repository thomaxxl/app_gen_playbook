# Preserved Example Apps

This directory is the preserved example-app library for the playbook.

Each subdirectory is a standalone runnable example that may be consulted as
example code, formatting guidance, or implementation reference material when
the current task explicitly calls for comparison, maintenance, or example-code
reuse.

Current examples in this workspace:

- `cmdb/`
  Full generated CMDB operations console example, including preserved
  architecture artifacts under `cmdb/artifacts/architecture/`.
- `northwind_safrs_pa/`
  Minimal runnable Northwind deployment example that serves a built SPA at
  `/app/`. In this workspace it is a standalone nested repository, not part of
  the outer playbook repo history.

Rules:

- `examples/` is a reference library, not the normative source of truth for
  runtime, product, architecture, UX, or backend contracts.
- New example apps should be added as new subdirectories under `examples/`.
- Some example subdirectories may be tracked directly in the outer playbook
  repo, while others may be standalone nested repositories. The playbook
  should treat both as example-code sources when the task explicitly calls for
  comparison, maintenance, or example-code reuse.
- Tasks that refer to "the examples" should treat this directory as a library;
  do not assume there is only one canonical example app.
- When a task needs a specific example, name the subdirectory explicitly.
