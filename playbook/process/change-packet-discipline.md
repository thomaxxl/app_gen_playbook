# Change Packet Discipline

Change runs MUST stay delta-based.

The canonical change packet for the active change lives under:

- `runs/current/artifacts/product/changes/<change_id>/`

At minimum, that packet SHOULD carry:

- `request.md`
- `affected-artifacts.md`
- `affected-app-paths.md`
- `reopened-gates.md`

Rules:

- change-run read sets MUST load the current change packet plus only the exact
  affected artifacts and app paths required by the current task
- change-run task bundles MUST NOT justify reading whole artifact trees or
  whole `app/frontend/` or `app/backend/` subtrees by default
- if a task needs more than the current change packet provides, the owning role
  MUST update the packet or issue a narrower handoff instead of falling back to
  a broad repo scan
- resumed and interrupted change runs MUST keep the packet current enough that
  a later role can understand the delta without scanning the whole baseline
