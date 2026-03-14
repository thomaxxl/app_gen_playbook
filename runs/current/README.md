# Current Run

This directory is the neutral active-run workspace.

It contains:

- [input.md](input.md)
- [remarks.md](remarks.md)
- [artifacts/README.md](artifacts/README.md)
- [role-state/README.md](role-state/README.md)
- [evidence/README.md](evidence/README.md)

Brief rule:

- `input.md` is the canonical stored brief for the run
- `role-state/product_manager/inbox/INPUT.md` is the seeded actionable copy
  for the Product Manager
- if they differ, `input.md` MUST be treated as authoritative until the inbox
  copy is refreshed

The preserved generated example remains outside this directory in:

- [../../example/README.md](../../example/README.md)

The generated-app working tree for the active run is:

- local gitignored `../../app/`

Rules:

- `input.md` MUST be replaced with the next real brief before execution
- `remarks.md` MUST stay run-local and neutral until the next run produces new
  findings
- the Product Manager or run initializer SHOULD create local `../../app/`
  before implementation begins
- `artifacts/` holds the run-owned product, architecture, UX, and
  backend-design artifacts
- `evidence/` holds the run-owned verification summaries
