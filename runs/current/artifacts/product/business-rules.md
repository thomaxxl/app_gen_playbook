owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - workflows.md
  - domain-glossary.md
unresolved:
  - replace with run-specific business rules
last_updated_by: playbook

# Business Rules Catalog Template

Replace this stub with the run-specific business-rules catalog.

## Required top-level sections

1. `Purpose`
2. `Domain Vocabulary Used In Rules`
3. `Defaults Not Listed Individually`
4. `Rule Index`

## Required rule index

| Rule ID | Title | Class | Frontend Mirror | Status |
| --- | --- | --- | --- | --- |
| `BR-001` | `<title>` | `<class>` | `<mirror mode>` | `<status>` |

## Required rule entry schema

Each rule entry MUST include:

- `Rule ID`
- `Title`
- `Status`
- `Rule Class`
- `Plain-Language Rule`
- `Rationale`
- `Source`
- `Trigger`
- `Preconditions`
- `Applies To`
- `Valid Outcome`
- `Invalid Outcome`
- `User-Visible Consequence`
- `Backend Enforcement`
- `Frontend Mirror`
- `Frontend Mirror Reason`
- `Authoritative Error Message`
- `Examples`
- `Backend Test Required`
- `Frontend Test Required`

Optional but recommended:

- `Decision Table Ref`
- `Implementation Notes`
- `Traceability`
