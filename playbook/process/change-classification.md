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
`app/docs/playbook-baseline/current/` before proceeding.

## Required output

The Product Manager MUST record:

- the chosen run mode
- the reason for that choice
- the affected product areas
- the likely affected architecture, UX, backend, and DevOps lanes
