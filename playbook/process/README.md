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

Mutable run state belongs under:

- `../../runs/current/`

An explicit app-only maintenance pass MAY update `../../app/` without
rewriting `../../runs/current/`; see
`playbook-execution-outputs.md` and `single-operator-mode.md`.

Recommended reading order:

1. [input-policy.md](input-policy.md)
2. [inbox-protocol.md](inbox-protocol.md)
3. [playbook-execution-outputs.md](playbook-execution-outputs.md)
4. [artifact-metadata.md](artifact-metadata.md)
5. [run-lifecycle.md](run-lifecycle.md)
6. [compatibility.md](compatibility.md)
7. [single-operator-mode.md](single-operator-mode.md)
8. [ownership-and-edits.md](ownership-and-edits.md)
9. [phases/phase-0-intake-and-framing.md](phases/phase-0-intake-and-framing.md)
10. [phases/phase-1-product-definition.md](phases/phase-1-product-definition.md)
11. [phases/phase-2-architecture-contract.md](phases/phase-2-architecture-contract.md)
12. [phases/phase-3-ux-and-interaction-design.md](phases/phase-3-ux-and-interaction-design.md)
13. [phases/phase-4-backend-design-and-rules-mapping.md](phases/phase-4-backend-design-and-rules-mapping.md)
14. [phases/phase-5-parallel-implementation.md](phases/phase-5-parallel-implementation.md)
15. [phases/phase-6-integration-review.md](phases/phase-6-integration-review.md)
16. [new-run.md](new-run.md)
17. [rename-starter-trio-checklist.md](rename-starter-trio-checklist.md)
16. [phases/phase-7-product-acceptance.md](phases/phase-7-product-acceptance.md)
17. [handoffs.md](handoffs.md)
18. [escalation.md](escalation.md)
19. [done.md](done.md)
20. [cadence.md](cadence.md)
