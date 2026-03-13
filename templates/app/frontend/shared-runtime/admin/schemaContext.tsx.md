# `frontend/src/shared-runtime/admin/schemaContext.tsx`

See also:

- [../../../../../specs/contracts/frontend/runtime-contract.md](../../../../../specs/contracts/frontend/runtime-contract.md)

```tsx
import { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { DataProvider } from "react-admin";

import {
  createDataProviderSync,
  loadAdminYamlFromUrl,
  normalizeAdminYaml,
} from "safrs-jsonapi-client";
import type {
  DataProvider as SafrsDataProvider,
  Schema,
} from "safrs-jsonapi-client";

import { createSearchEnabledDataProvider } from "./createSearchEnabledDataProvider";
import type { RawAdminYaml } from "./resourceMetadata";

interface AdminSchemaContextValue {
  rawYaml: RawAdminYaml;
  schema: Schema;
}

const AdminSchemaContext = createContext<AdminSchemaContextValue | null>(null);

export interface AdminAppConfig {
  adminYamlUrl: string;
  apiRoot: string;
  title: string;
}

export function AdminSchemaProvider({
  children,
  rawYaml,
  schema,
}: {
  children: ReactNode;
  rawYaml: RawAdminYaml;
  schema: Schema;
}) {
  return (
    <AdminSchemaContext.Provider value={{ rawYaml, schema }}>
      {children}
    </AdminSchemaContext.Provider>
  );
}

export function useAdminSchema(): Schema {
  const context = useContext(AdminSchemaContext);
  if (!context) {
    throw new Error("Admin schema is not available.");
  }
  return context.schema;
}

export function useRawAdminYaml(): RawAdminYaml {
  const context = useContext(AdminSchemaContext);
  if (!context) {
    throw new Error("Raw admin.yaml is not available.");
  }
  return context.rawYaml;
}

function isSearchEnabled(value: unknown): boolean {
  return value === true || value === "true";
}

function toSchemaResourceKey(endpoint: string | undefined): string {
  const normalized = String(endpoint ?? "")
    .trim()
    .replace(/^https?:\/\/[^/]+/i, "")
    .replace(/^\/+/, "");

  if (normalized.startsWith("api/")) {
    return normalized.slice(4);
  }

  return normalized;
}

export function adaptAdminYamlForClient(
  rawYaml: RawAdminYaml,
): Record<string, unknown> {
  const resources = Object.fromEntries(
    Object.entries(rawYaml.resources ?? {}).map(([resourceName, resource]) => [
      toSchemaResourceKey(resource.endpoint),
      {
        endpoint: toSchemaResourceKey(resource.endpoint),
        type: resourceName,
        user_key: resource.user_key,
        search_cols: Object.entries(resource.attributes ?? {})
          .filter(([, attribute]) => isSearchEnabled(attribute.search))
          .map(([name]) => ({ name })),
        attributes: Object.entries(resource.attributes ?? {}).map(
          ([name, attribute]) => ({
            name,
            type: attribute.type,
            search: isSearchEnabled(attribute.search),
            required: attribute.required,
            hide_edit: attribute.readonly === true || attribute.edit === false,
          }),
        ),
        tab_groups: [],
      },
    ]),
  );

  return {
    ...rawYaml,
    resources,
  };
}

export async function loadAdminBootstrap(config: AdminAppConfig): Promise<{
  dataProvider: DataProvider;
  rawYaml: RawAdminYaml;
  schema: Schema;
}> {
  let rawYaml: RawAdminYaml | undefined;

  try {
    rawYaml = (await loadAdminYamlFromUrl(
      config.adminYamlUrl,
      fetch,
    )) as RawAdminYaml;
    const clientYaml = adaptAdminYamlForClient(rawYaml);
    const schema = normalizeAdminYaml(clientYaml) as Schema;
    const baseProvider = createDataProviderSync({
      apiRoot: config.apiRoot,
      schema,
    }) as unknown as SafrsDataProvider;
    const dataProvider = createSearchEnabledDataProvider({
      apiRoot: config.apiRoot,
      baseProvider,
      fetch,
      rawYaml,
      schema,
    }) as unknown as DataProvider;

    return {
      dataProvider,
      rawYaml,
      schema,
    };
  } catch (error) {
    console.error("Failed to load admin bootstrap", {
      adminYamlUrl: config.adminYamlUrl,
      error,
      resourceNames: Object.keys(rawYaml?.resources ?? {}),
    });
    throw error;
  }
}
```

Notes:

- The playbook `admin.yaml` authoring shape and the current
  `safrs-jsonapi-client` normalizer input shape are not identical.
- `adaptAdminYamlForClient(...)` is therefore part of the required runtime
  contract, not a project-specific optional workaround.
