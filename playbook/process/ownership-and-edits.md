# Ownership And Edits

This file defines which role owns which artifact area and how cross-role
changes are requested.

Ownership map:

- `runs/current/artifacts/product/` -> Product Manager
- `runs/current/artifacts/architecture/` -> Architect
- `runs/current/artifacts/ux/` -> UX/UI + Frontend
- `runs/current/artifacts/backend-design/` -> Backend
- `runs/current/artifacts/devops/` -> DevOps
- `specs/contracts/frontend/` -> UX/UI + Frontend technical contracts
- `specs/contracts/backend/` -> Backend technical contracts
- `specs/contracts/rules/` -> Backend technical contracts
- `specs/contracts/deployment/` -> optional DevOps role when packaging is in scope
- `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` -> generic playbook template source, only editable
  when explicitly updating the playbook itself

Rules:

- only the owning role may directly edit files in its artifact area
- non-owning roles must request changes through inbox handoff unless
  ownership is explicitly delegated
- exception: a receiving or gate-owning review role MAY perform a metadata-only
  edit in another role's artifact file when setting review state such as
  `approved`, `blocked`, `superseded`, `unresolved`, or `last_updated_by`
- a metadata-only approval edit MUST NOT change the artifact body content
- implementation work for a generated app MUST stay inside local gitignored
  `app/`
- `app/` subtree ownership is explicit:
  - `app/BUSINESS_RULES.md` -> Product Manager
  - `app/README.md` -> Architect
  - `app/frontend/**` -> Frontend
  - `app/backend/**`, `app/rules/**`, `app/reference/admin.yaml` -> Backend
  - `app/.gitignore`, `app/Dockerfile`, `app/docker-compose.yml`,
    `app/nginx.conf`, `app/entrypoint.sh`, `app/install.sh`, `app/run.sh` ->
    DevOps
- during parallel frontend/backend implementation, no role MAY treat a shared
  `app/` file as implicitly co-owned; ownership MUST remain single-role or be
  handed back to Architect for mediation
- `app/BUSINESS_RULES.md` is a generated-app snapshot of the run-owned
  Product artifact, not a second source of truth
- implementation work MUST NOT patch the playbook contract files while
  creating the app unless the user explicitly requests a playbook update
- when the task updates the playbook itself, those playbook changes MUST be
  committed in the playbook git repository before the task is treated as
  complete, unless the user explicitly asks to keep them uncommitted
- playbook maintenance MUST preserve segmentation intended to reduce context
  overload; do not merge optional capability packs into core contracts, widen
  role reading lists unnecessarily, or blur the boundary between playbook
  source, templates, run state, and generated app output without an explicit
  documented reason
- phase artifacts and inbox traces outside `app/` are expected output of a
  real playbook run; see `playbook-execution-outputs.md`
- required decisions must live in owned artifacts, not only in inbox messages
  or agent `context.md`
- if a role finds a contract problem in another role's area, it must send a
  change request to the owning role instead of silently patching around it
