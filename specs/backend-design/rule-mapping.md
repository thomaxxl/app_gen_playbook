owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/business-rules.md
  - model-design.md
unresolved:
  - replace with run-specific rule mapping
last_updated_by: playbook

# Rule Mapping Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/rule-mapping.md`.

This artifact is implementation-oriented. It MUST NOT restate business meaning
that already belongs in `../../runs/current/artifacts/product/business-rules.md`.

## Required rule traceability table

The real artifact MUST include a table with this shape:

| Rule ID | Backend fields involved | Backend enforcement location | LogicBank pattern | API behavior | Backend tests | Frontend mirror mode | Frontend mirror location | Frontend tests | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BR-001` | `<fields>` | `<file/function>` | `<formula/sum/count/copy/constraint/custom>` | `<save rejected / derived update / none>` | `<test files>` | `<none/input/form/schema/async>` | `<file/function or none>` | `<test files or none>` | `<notes>` |

The Backend role MUST replace the placeholder row.

## Required notes

The real artifact MUST also define:

- which rule IDs are declarative LogicBank rules
- which rule IDs require custom Python behavior
- which fields are backend-managed because of those rules
- which rule IDs are explicitly deferred or out of scope
- when `copy` and `formula` both appear, which rule IDs are snapshot semantics
  versus live-propagation semantics

If the run needs LogicBank event handlers or signature-level API verification,
the Backend role MAY load
`../contracts/rules/logicbank-reference.md`.

That advanced reference MUST NOT become a default read for unrelated backend
tasks.
