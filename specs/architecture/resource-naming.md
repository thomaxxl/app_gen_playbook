owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - ../product/domain-glossary.md
unresolved:
  - replace with run-specific resource naming table
last_updated_by: playbook

# Resource Naming Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/resource-naming.md`.

The real artifact MUST define, per resource:

- Python model class
- SQL table
- admin.yaml key
- SAFRS wire type
- collection path
- relationship names

If the domain contains multiple references to the same target resource, the
artifact MUST define each reference relationship explicitly instead of
describing them only by target type. For a worked example, see
`nonstarter-worked-example.md`.
