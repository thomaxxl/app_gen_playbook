# New Run Procedure

Use this file to reset the mutable run state before starting a new app.

This procedure MUST be used only for a new full run.

It MUST NOT be used for an app-only maintenance pass that intentionally leaves
`../../runs/current/` unchanged.

Required steps:

1. archive any completed run-specific artifacts, evidence, or remarks that
   must remain available
2. ensure preserved examples live under `../../example/`
3. replace `../../runs/current/input.md` with the new brief
4. reset `../../runs/current/remarks.md` to a neutral placeholder
5. clear or recreate:
   - `../../runs/current/artifacts/`
   - `../../runs/current/evidence/`
   - `../../runs/current/role-state/`
6. seed `../../runs/current/role-state/product_manager/inbox/INPUT.md` from
   `../../runs/current/input.md`
7. recreate `../../runs/current/artifacts/architecture/capability-profile.md`
   from the starter template shape
8. recreate `../../runs/current/artifacts/architecture/load-plan.md`
   from the starter template shape
9. leave `../../specs/contracts/`, `../../specs/features/`, and the generic
   template directories unchanged

Rules:

- a new run MUST NOT begin from stale domain-filled files under
  `../../runs/current/`
- the operator SHOULD preserve any historically useful run under
  `../../example/` or another archive before reset
- optional feature packs MUST remain disabled or undecided until the new
  capability profile explicitly enables them
- if `../../runs/current/input.md` and the Product Manager inbox `INPUT.md`
  ever diverge during setup, `../../runs/current/input.md` MUST win and the
  inbox copy MUST be refreshed before execution starts
