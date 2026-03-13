owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - model-design.md
unresolved:
  - replace with run-specific relationship map
last_updated_by: playbook

# Relationship Map Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/relationship-map.md`.

The real artifact MUST define:

- relationship directions
- exact relationship names
- delete behavior
- nullability and foreign-key rules
