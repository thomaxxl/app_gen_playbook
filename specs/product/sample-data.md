owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - workflows.md
  - business-rules.md
unresolved:
  - replace with run-specific sample data
last_updated_by: playbook

# Sample Data Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/sample-data.md`.

The real artifact MUST define:

- reference records
- canonical happy-path scenarios
- boundary conditions
- invalid or negative scenarios
- workflow-specific records
- rule-specific records
- search or reporting test records
- delivery seed policy

The real artifact MUST include a machine-readable policy block like:

```yaml
delivery_seed_policy:
  mode: none | approved-demo | required-reference
  allowed_visible_resources:
    - ...
  forbidden_visible_markers:
    - mock
    - demo
    - sample
    - starter
  notes: ...
```

Interpretation:

- `none`: no seeded or demo data should remain visible in the delivered app
- `approved-demo`: approved demo data may remain visible, but it must be
  listed explicitly
- `required-reference`: reference data such as statuses or categories may
  remain, but transactional demo rows should not
