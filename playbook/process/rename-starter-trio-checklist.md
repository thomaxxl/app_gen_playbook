# Rename Starter Trio Checklist

Use this file when adapting the starter trio to a non-starter domain.

The operator MUST review and update these areas together:

- `runs/current/artifacts/product/domain-glossary.md`
- `runs/current/artifacts/product/business-rules.md`
- `runs/current/artifacts/product/sample-data.md`
- `runs/current/artifacts/architecture/resource-naming.md`
- `runs/current/artifacts/architecture/generated-vs-custom.md`
- `runs/current/artifacts/backend-design/model-design.md`
- `runs/current/artifacts/backend-design/relationship-map.md`
- `runs/current/artifacts/backend-design/rule-mapping.md`
- `templates/app/reference/admin.yaml.md`
- `templates/app/backend/models.py.md`
- `templates/app/backend/bootstrap.py.md`
- `templates/app/rules/rules.py.md`
- `templates/app/frontend/resourcePages.ts.md`
- `templates/app/frontend/generated/resources/*.tsx.md`
- `templates/app/frontend/Landing.tsx.md` or
  `templates/app/frontend/CustomDashboard.tsx.md`
- generated app tests and Playwright smoke expectations

The operator MUST NOT update only one naming layer and assume the others will
infer the change.
