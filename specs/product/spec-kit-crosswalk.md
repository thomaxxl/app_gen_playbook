owner: product_manager
phase: phase-1-product-definition
status: reference
last_updated_by: playbook

# Spec-Kit Crosswalk

This note explains how the playbook's split Product package maps to a
future spec-kit style `spec.md`.

The playbook intentionally separates story scope, implementation mapping,
business rules, sample data, and acceptance evidence into distinct artifacts.
That separation should not be reversed. Use this crosswalk when translating
between the two models.

## Crosswalk

| Spec-kit area | Playbook artifact(s) | Notes |
| --- | --- | --- |
| Problem framing / summary | `brief.md`, `input-interpretation.md`, `research-notes.md` | Product framing and sparse-input decisions live here. |
| Conceptual domain model | `conceptual-domain-model.md`, `domain-glossary.md` | The business-facing concept, lifecycle, and event layer stays separate from app-resource or ORM design. |
| User Scenarios & Testing | `user-stories.md` | Story blocks are the spec-kit-core scenario records. |
| Requirements / scope commitments | `user-stories.md`, `traceability-matrix.md` | Story core stays in `user-stories.md`; implementation/review linkage stays in `traceability-matrix.md`. |
| Key Entities | `resource-inventory.md`, `resource-behavior-matrix.md`, `sample-data.md` | Entity definitions, CRUD behavior, and sample records are split on purpose. |
| Business rules | `business-rules.md` | The single authoritative human-readable rule catalog. |
| Workflows / process | `workflows.md` | Multi-step journeys and transitions. |
| UX / page intent | `custom-pages.md`, `ux/navigation.md`, `ux/landing-strategy.md`, `ux/screen-inventory.md` | Playbook separates product intent from UX execution. |
| Success criteria | `acceptance-criteria.md` | Delivery success and acceptance framing. |
| Assumptions / open questions | `assumptions-and-open-questions.md` | Explicit unresolved product decisions. |
| Review / traceability bridge | `traceability-matrix.md` | This is playbook-specific and has no direct spec-kit equivalent. |
| Story quality pass | `story-quality-checklist.md` | Also playbook-specific; used as a pre-handoff quality gate. |

## Integration rule

When translating from the playbook into a spec-kit document:

- keep user-facing scope and independent tests in the story blocks
- pull business concepts, state models, and events from
  `conceptual-domain-model.md`
- pull implementation linkage from `traceability-matrix.md`
- pull entity shape from `resource-inventory.md`
- pull success criteria from `acceptance-criteria.md`
- do not collapse rule mapping, permissions, page IDs, route IDs, or review
  evidence into the story core unless the target workflow explicitly requires
  it

When translating from spec-kit into the playbook:

- expand User Scenarios & Testing into `user-stories.md`
- expand conceptual entities, states, and business events into
  `conceptual-domain-model.md`
- expand requirements-to-implementation linkage into `traceability-matrix.md`
- expand entity references into `resource-inventory.md` and
  `resource-behavior-matrix.md`
- expand success criteria into `acceptance-criteria.md`
