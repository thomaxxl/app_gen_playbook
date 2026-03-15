# D3 Custom Views Feature Templates

This directory is the feature-gated template entrypoint for D3-based custom
views.

It MUST be loaded only when:

- `runs/current/artifacts/architecture/capability-profile.md` enables
  `d3-custom-views`
- `runs/current/artifacts/architecture/load-plan.md` assigns the feature to
  the current role

If the capability is disabled or undecided, this directory MUST remain
unloaded.

This pack reuses the existing starter visualization snippet instead of adding
another parallel chart lane.

Expected implementation steps:

1. read `../../../specs/features/d3-custom-views/README.md`
2. read `../../../specs/features/d3-custom-views/frontend.md`
3. verify the target custom page is named in
   `runs/current/artifacts/ux/custom-view-specs.md`
4. install `d3@7.9.0`
5. copy `../../app/frontend/D3Visualization.tsx.md` or a run-specific variant
6. keep page-shell logic separate from the focused visualization component
