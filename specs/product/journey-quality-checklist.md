owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - user-journeys.md
  - user-stories.md
  - workflows.md
  - traceability-matrix.md
unresolved:
  - replace with run-specific journey-quality review
last_updated_by: playbook

# Journey Quality Checklist

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/journey-quality-checklist.md`.

This artifact is the journey equivalent of `story-quality-checklist.md`.

It exists to confirm that current-release journeys are:

- real
- concrete
- readable
- end-to-end
- not just UI choreography
- not missing alternate or recovery paths
- aligned with the current-release story and workflow set

Suggested summary shape:

- status: reviewed
- current-release journeys checked: J-001, J-002, J-005
- end-to-end completeness: pass
- actor coverage: pass
- recovery-path coverage: partial
- critical issues: none
- review_summary: The current-release journeys are concrete, user-centered,
  and aligned with the workflow and story catalog.
