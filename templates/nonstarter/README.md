# Non-Starter Templates

This directory contains generic templates for apps that do not stay on the
starter trio.

Use this lane when the app requires custom resource names, custom landing-page
content, or fully rewritten bootstrap/rule content.

Available templates:

- `backend/models.py.md`
- `backend/bootstrap.py.md`
- `rules/rules.py.md`
- `frontend/CustomDashboard.tsx.md`
- `reference/admin.yaml.md`

These templates are generic placeholders. They SHOULD be combined with the
run-owned artifacts under `../../runs/current/artifacts/`.

For a concrete four-resource non-starter example with multiple references to
the same target resource and a custom dashboard join, see:

- `../../specs/architecture/nonstarter-worked-example.md`
