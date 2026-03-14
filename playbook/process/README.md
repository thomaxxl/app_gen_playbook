# Process

This directory contains the static phased workflow for the playbook.

Generated application output belongs under:

- `../../app/`

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

- `../../runs/current/`

An explicit app-only maintenance pass MAY update `../../app/` without
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
8. [single-operator-mode.md](single-operator-mode.md)
9. [ownership-and-edits.md](ownership-and-edits.md)
10. [phases/phase-0-intake-and-framing.md](phases/phase-0-intake-and-framing.md)
11. [phases/phase-1-product-definition.md](phases/phase-1-product-definition.md)
12. [phases/phase-2-architecture-contract.md](phases/phase-2-architecture-contract.md)
13. [phases/phase-3-ux-and-interaction-design.md](phases/phase-3-ux-and-interaction-design.md)
14. [phases/phase-4-backend-design-and-rules-mapping.md](phases/phase-4-backend-design-and-rules-mapping.md)
15. [phases/phase-5-parallel-implementation.md](phases/phase-5-parallel-implementation.md)
16. [phases/phase-6-integration-review.md](phases/phase-6-integration-review.md)
17. [new-run.md](new-run.md)
18. [rename-starter-trio-checklist.md](rename-starter-trio-checklist.md)
19. [phases/phase-7-product-acceptance.md](phases/phase-7-product-acceptance.md)
20. [handoffs.md](handoffs.md)
21. [escalation.md](escalation.md)
22. [done.md](done.md)
23. [cadence.md](cadence.md)
