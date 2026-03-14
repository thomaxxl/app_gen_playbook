export const appConfig = {
  adminYamlUrl: import.meta.env.VITE_ADMIN_YAML_URL ?? "/ui/admin/admin.yaml",
  apiRoot: import.meta.env.VITE_API_ROOT ?? "/api",
  title: "Cimage Sharing and Management",
} as const;
