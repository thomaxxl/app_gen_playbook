# Generated Northwind Admin

This frontend was generated from an `admin.yaml` file.

## Commands

```bash
npm install
npm run dev
```

Default runtime config:

- `VITE_ADMIN_YAML_URL=http://127.0.0.1:5656/ui/admin/admin.yaml`
- `VITE_API_ROOT=http://127.0.0.1:5656/api`

## Structure

- `src/generated/` is generated from `admin.yaml`
- `src/shared-runtime` points to the shared runtime used by generated apps

Change shared UI behavior in the shared runtime, not in the generated wrappers.
