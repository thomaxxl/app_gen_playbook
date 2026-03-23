# Change Packet Discipline

Change runs MUST stay delta-based.

The canonical change packet for the active change lives under:

- `runs/current/changes/<change_id>/`

At minimum, that packet SHOULD carry:

- `request.md`
- `classification.yaml`
- `impact-manifest.yaml`
- `affected-artifacts.md`
- `affected-candidate-artifacts.md`
- `affected-app-paths.md`
- `reopened-gates.md`
- `role-loads/*.yaml`
- `candidate/artifacts/**`
- `verification/**`
- `promotion.yaml`

Rules:

- change packets MUST make execution scope executable, not merely descriptive
- `classification.yaml` MUST record `scope_profile`, `active_roles`,
  `active_phases`, and the active policy slice
- change-run read sets MUST load the current change packet plus only the exact
  affected artifacts and app paths required by the current task
- `affected-candidate-artifacts.md` MUST name the candidate design deltas that
  implementation is expected to consume
- when a role-load manifest exists for the active role, it MUST become the
  default scope boundary for change reads and writes
- Architect MUST populate role-load manifests for every active role during
  Phase I3 for every non-hotfix change
- template-only role-load manifests do not justify broad fallback; until the
  manifest is populated, the resolver MUST narrow from `affected-artifacts.md`
  and `affected-app-paths.md`
- change-run task bundles MUST NOT justify reading whole artifact trees or
  whole `app/frontend/` or `app/backend/` subtrees by default
- if `request.md` is a review-style critique that lists concrete defects,
  weaknesses, or recommendations against the current accepted app, the packet
  MUST treat that as a baseline challenge rather than an automatic no-op
- review-style change packets MUST keep `affected-artifacts.md`,
  `affected-app-paths.md`, and `reopened-gates.md` explicit until the packet
  cites exact evidence that every raised finding is already resolved
- if a task needs more than the current change packet provides, the owning role
  MUST update the packet or issue a narrower handoff instead of falling back to
  a broad repo scan
- resumed and interrupted change runs MUST keep the packet current enough that
  a later role can understand the delta without scanning the whole baseline
- candidate design changes MUST go under
  `runs/current/changes/<change_id>/candidate/artifacts/**` until acceptance
