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

Replace this stub with the run-specific rule mapping.

This artifact is implementation-oriented. It MUST NOT replace the
human-readable business-rules catalog.

## Required rule traceability table

| Rule ID | Backend fields involved | Backend enforcement location | LogicBank pattern | API behavior | Backend tests | Frontend mirror mode | Frontend mirror location | Frontend tests | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BR-001` | `<fields>` | `<file/function>` | `<formula/sum/count/copy/constraint/custom>` | `<save rejected / derived update / none>` | `<test files>` | `<none/input/form/schema/async>` | `<file/function or none>` | `<test files or none>` | `<notes>` |

## Required notes

- which rule IDs are declarative LogicBank rules
- which rule IDs require custom Python behavior
- which rule IDs are deferred or out of scope
