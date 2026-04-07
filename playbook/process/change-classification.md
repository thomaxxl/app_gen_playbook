# Change Classification

Use this file to classify a post-launch request before work starts.

## Classification rule

If a request changes product intent, UX behavior, business rules, API shape,
data shape, enabled capabilities, or acceptance criteria, it MUST use
`iterative-change-run`.

If a request is only a narrow implementation repair with no design-state
change, it MAY use `app-only-hotfix`.

If the current app no longer matches the requested framing well enough to
evolve safely, the Product Manager and Architect SHOULD escalate to
`new-full-run`.

If the current accepted baseline cannot be proven from `runs/current/artifacts/`
alone, the change lane SHOULD restore or verify it from
`runs/current/exports/playbook-baseline/current/` before proceeding.
Legacy generated-app exports MAY be imported as compatibility input when that
repository-local export is missing.

## Required output

The Product Manager MUST record:

- the chosen run mode
- the chosen `scope_profile`
- the reason for that choice
- the affected product areas
- the exact active roles and phases
- the likely affected architecture, UX, backend, rules, and DevOps lanes
- the exact affected app paths, candidate artifacts, and reopened gates
