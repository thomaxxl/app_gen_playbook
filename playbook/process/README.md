# Process

This directory contains the static phased workflow for the playbook.

Generated application output belongs under:

- local gitignored `../../app/`

Interpretation rule:

- references to `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` refer to generic template sources unless a file
  explicitly says otherwise
- the run-owned copies of those artifacts MUST live under
  `../../runs/current/artifacts/`
- optional feature-pack contracts live under `../../specs/features/`
- optional feature-pack templates live under `../../templates/features/`
- disabled or undecided feature packs MUST NOT be loaded or copied

Mutable run state belongs under:

- tracked `../../runs/template/`
- local `../../runs/current/`

An explicit app-only maintenance pass MAY update local `../../app/` without
rewriting `../../runs/current/`; see
`playbook-execution-outputs.md` and `single-operator-mode.md`.

Recommended reading order:

1. [input-policy.md](input-policy.md)
2. [inbox-protocol.md](inbox-protocol.md)
3. [capability-loading.md](capability-loading.md)
4. [playbook-execution-outputs.md](playbook-execution-outputs.md)
5. [artifact-metadata.md](artifact-metadata.md)
6. [run-lifecycle.md](run-lifecycle.md)
7. [compatibility.md](compatibility.md)
8. [runtime-baseline.md](runtime-baseline.md)
9. [dependency-materialization.md](dependency-materialization.md)
10. [segmentation-model.md](segmentation-model.md)
11. [packaging-lanes.md](packaging-lanes.md)
12. [single-operator-mode.md](single-operator-mode.md)
13. [ownership-and-edits.md](ownership-and-edits.md)
14. [phases/phase-0-intake-and-framing.md](phases/phase-0-intake-and-framing.md)
15. [phases/phase-1-product-definition.md](phases/phase-1-product-definition.md)
16. [phases/phase-2-architecture-contract.md](phases/phase-2-architecture-contract.md)
17. [architect-decision-procedure.md](architect-decision-procedure.md)
18. [phases/phase-3-ux-and-interaction-design.md](phases/phase-3-ux-and-interaction-design.md)
19. [phases/phase-4-backend-design-and-rules-mapping.md](phases/phase-4-backend-design-and-rules-mapping.md)
20. [phases/phase-5-parallel-implementation.md](phases/phase-5-parallel-implementation.md)
21. [phases/phase-6-integration-review.md](phases/phase-6-integration-review.md)
22. [new-run.md](new-run.md)
23. [rename-starter-trio-checklist.md](rename-starter-trio-checklist.md)
24. [frontend-nonstarter-checklist.md](frontend-nonstarter-checklist.md)
25. [phases/phase-7-product-acceptance.md](phases/phase-7-product-acceptance.md)
26. [handoffs.md](handoffs.md)
27. [escalation.md](escalation.md)
28. [done.md](done.md)
29. [cadence.md](cadence.md)
30. [release-checklist.md](release-checklist.md)

Maintainer-only reference:

- [ui-system-change-policy.md](ui-system-change-policy.md)
- [read-sets/frontend-core.md](read-sets/frontend-core.md)
- [read-sets/backend-core.md](read-sets/backend-core.md)
- [read-sets/devops-core.md](read-sets/devops-core.md)

Optional late-stage packaging role:

- `../roles/devops.md`
