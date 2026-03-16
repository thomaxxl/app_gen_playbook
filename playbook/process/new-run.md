# New Run Procedure

Use this file to reset the mutable run state before starting a new app.

This procedure MUST be used only for a new full run.

It MUST NOT be used for an app-only maintenance pass that intentionally leaves
`../../runs/current/` unchanged.

Required steps:

1. archive any completed run-specific artifacts, evidence, or remarks that
   must remain available
2. ensure preserved examples live under `../../example/`
3. recreate local `../../runs/current/` from the tracked neutral starter under
   `../../runs/template/`
4. replace local `../../runs/current/input.md` with the new brief
5. reset local `../../runs/current/remarks.md` to a neutral placeholder
6. clear or recreate local:
   - `../../runs/current/artifacts/`
   - `../../runs/current/evidence/`
   - `../../runs/current/role-state/`
7. ensure the evidence lane is ready to record at least:
   - command logs
   - backend/frontend/e2e verification notes
   - `contract-samples.md` for the route-to-record trace
   - `frontend-usability.md` for the reviewed user-facing surfaces
   - `ui-previews/` for Playwright-captured UI screenshots when the run
     materially changes visible frontend behavior
8. seed `../../runs/current/role-state/product_manager/inbox/INPUT.md` from
   `../../runs/current/input.md`
9. seed `../../runs/current/artifacts/architecture/capability-profile.md`
   from `../../runs/template/artifacts/architecture/capability-profile.md`
10. seed `../../runs/current/artifacts/architecture/load-plan.md`
    from `../../runs/template/artifacts/architecture/load-plan.md`
11. if packaging or runtime normalization is expected for the run, recreate
   `../../runs/current/artifacts/devops/` from the starter stub set
12. if packaging or runtime normalization is expected for the run, ensure
    `../../runs/current/role-state/devops/` exists
13. ensure the dormant `../../runs/current/role-state/ceo/` lane exists for
    stalled-run intervention, but do not seed it with active work
14. leave `../../specs/contracts/`, `../../specs/features/`, and the generic
   template directories unchanged
15. create local gitignored `../../app/` and seed the role-owned subtree roots:
    - `../../app/frontend/`
    - `../../app/backend/`
    - `../../app/rules/`
    - `../../app/reference/`
16. seed local `../../app/` with the required generated-app root files from
    `../../templates/app/project/` and `../../templates/app/deployment/`,
    including at least:
    - `.gitignore`
    - `install.sh`
    - `run.sh`
    - `README.md`
    - `BUSINESS_RULES.md` when available
    - `Dockerfile`
    - `docker-compose.yml`
17. materialize app dependency manifests from the template sources plus the
    run-owned `runtime-bom.md` before any install step
18. treat local `../../app/` as implementation workspace, not as the
    canonical brief source
19. when the Product business-rules catalog becomes available, seed local
    `../../app/BUSINESS_RULES.md` from it and keep that copy synchronized

Rules:

- a new run MUST NOT begin from stale domain-filled files under
  local `../../runs/current/`
- the tracked `../../runs/template/` tree MUST remain neutral and reusable;
  it MUST NOT accumulate domain-specific run output
- the operator SHOULD preserve any historically useful run under
  `../../example/` or another archive before reset
- optional feature packs MUST remain disabled or undecided until the new
  capability profile explicitly enables them
- if `../../runs/current/input.md` and the Product Manager inbox `INPUT.md`
  ever diverge during setup, `../../runs/current/input.md` MUST win and the
  inbox copy MUST be refreshed before execution starts
- local `../../app/` MUST remain outside git and MUST be recreated locally for
  each new run as needed
