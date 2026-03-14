# Run Artifacts

This directory is for run-owned artifacts for the current app definition.

Use it for:

- current run product artifacts
- current run architecture artifacts
- current run UX artifacts
- current run backend-design artifacts
- current run DevOps artifacts when packaging is in scope
- current run capability-gating artifacts

Generic template sources live in:

- `../../../specs/product/`
- `../../../specs/architecture/`
- `../../../specs/ux/`
- `../../../specs/backend-design/`

Accepted copies MAY later be promoted into:

- local `../../../app/docs/`

The generated app MUST also include:

- local `../../../app/BUSINESS_RULES.md`

That file is the app-local copy of the approved
`product/business-rules.md` artifact for the run snapshot.

Architecture artifacts MUST also include:

- `architecture/capability-profile.md`
- `architecture/load-plan.md`

These files control which optional feature packs may be loaded for the run.

If the optional DevOps role is active, this directory MUST also include:

- `devops/package-policy.md`
- `devops/packaging-plan.md`
- `devops/build-matrix.md`
- `devops/verification.md`
