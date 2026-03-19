# `frontend/src/config.ts`

See also:

- [../../../specs/contracts/frontend/routing-and-paths.md](../../../specs/contracts/frontend/routing-and-paths.md)
- [../reference/admin.yaml.md](../reference/admin.yaml.md)

Default to same-origin paths so the built app works on public URLs.

```ts
export const appConfig = {
  adminYamlUrl: import.meta.env.VITE_ADMIN_YAML_URL ?? "/ui/admin/admin.yaml",
  apiRoot: import.meta.env.VITE_API_ROOT ?? "/api",
  title: "My App Admin",
} as const;
```

Notes:

- Avoid hardcoding `127.0.0.1` into built bundles.
- Let Vite env vars override same-origin defaults during local development.
- The public SPA path is `/app/`, but the config values above stay
  same-origin API/admin paths.
