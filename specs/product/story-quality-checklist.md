owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - user-stories.md
  - traceability-matrix.md
unresolved:
  - replace with run-specific story quality assessment
last_updated_by: playbook

# Story Quality Checklist

Create the run-owned artifact at
`../../runs/current/artifacts/product/story-quality-checklist.md`.

This artifact is a human-readable quality pass over the story catalog. It does
not replace the compiler or traceability validator. It records whether the
current-release stories are concrete, independently testable, and free of
unresolved critical ambiguity.

This is not an optional afterthought. The run-owned checklist is a required
Phase 1 pre-handoff artifact and should be complete before Architecture starts
using the Product package as a stable contract.

Recommended checklist:

- no story text leaks implementation details that belong in traceability or
  technical artifacts
- every current-release story has `Why this priority`
- every current-release story has `Independent Test`
- every current-release story has at least one concrete `Given / When / Then`
  acceptance scenario
- edge cases are recorded where relevant
- permissions are explicit where relevant
- no backlog or later-release story is accidentally treated as current-release
  scope
- no critical story remains unresolved or hand-wavy
- normalized capability coverage is present and agrees with the coarse
  coverage matrix
- every current-release story has a spec-kit-core scenario block in
  `user-stories.md`
- every required higher-depth story includes the extended playbook fields

Suggested summary shape:

```md
# Story Quality Checklist

- status: reviewed
- current-release stories checked: US-001, US-004, US-010
- normalized capability coverage: aligned
- story-core completeness: pass
- critical issues: none
- review_summary: The story catalog is concrete, independently testable, and
  aligned with the traceability matrix for current-release scope.
```
