owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - workflows.md
unresolved:
  - replace with run-specific business rules
last_updated_by: playbook

# Business Rules Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/business-rules.md`.

Each rule entry MUST include:

- rule ID
- plain-language rule
- rule class
- triggering action
- preconditions
- valid outcome
- invalid outcome
- user-visible consequence
- affected resources and fields
