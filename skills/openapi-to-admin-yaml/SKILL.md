---
name: openapi-to-admin-yaml
description: Use when a user wants to generate a playbook-style `admin.yaml` from a SAFRS FastAPI `jsonapi.json` or OpenAPI schema, especially when reusing the `openapi_to_admin_yaml.py` generator in other projects.
---

# OpenAPI To Admin YAML

Use this skill when the task is: take a SAFRS FastAPI OpenAPI schema and generate an `admin.yaml` file for the admin frontend.

The bundled generator lives at `scripts/openapi_to_admin_yaml.py`.

## Workflow

1. Confirm the input is a SAFRS FastAPI OpenAPI document.
   It should expose collection routes under `/api/...` and JSON:API collection responses that reference `*DocumentCollection` schemas.
2. Run the generator.
   Default usage:

```bash
python skills/openapi-to-admin-yaml/scripts/openapi_to_admin_yaml.py path/to/jsonapi.json -o path/to/admin.yaml
```

3. If the project already has an `admin.yaml` with static top-level settings, reuse it as a template:

```bash
python skills/openapi-to-admin-yaml/scripts/openapi_to_admin_yaml.py path/to/jsonapi.json --template-admin path/to/admin.yaml -o path/to/admin.yaml
```

4. Validate the generated file.
   Check that:
   - resources were discovered
   - `user_key` values look sensible
   - relationship `tab_groups` match the API model
   - required attributes only appear when the OpenAPI schema marks them as required

## Behavior

- Resource discovery comes from JSON:API document refs, not raw path names.
- Non-resource `/api/...` routes are skipped.
- Empty attribute schemas do not crash the generator; the resource is emitted without `user_key`.
- Invalid or missing input files return a clean CLI error.

## When To Edit The Generator

Open `scripts/openapi_to_admin_yaml.py` only if the target project uses a different SAFRS OpenAPI contract or the generated `admin.yaml` shape needs to change.
The script is designed for the raw playbook-style `admin.yaml` used in this repo.
