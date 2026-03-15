---
owner: role_name
phase: phase-name
status: stub
depends_on:
  - runs/current/input.md
unresolved:
  - replace with run-specific decision
last_updated_by: role_name
---

# Artifact Frontmatter Template

Use this block at the top of run-owned artifact files under:

- `runs/current/artifacts/product/`
- `runs/current/artifacts/architecture/`
- `runs/current/artifacts/ux/`
- `runs/current/artifacts/backend-design/`
- `runs/current/artifacts/devops/`

Rules:

- keep the metadata small and machine-readable
- update `status`, `unresolved`, and `last_updated_by` as the artifact evolves
- do not replace artifact body content with inbox-only state
