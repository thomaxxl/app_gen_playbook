# `frontend/src/shared-runtime/admin/schemaContext.tsx`

See also:

- [../../../../../specs/contracts/frontend/runtime-contract.md](../../../../../specs/contracts/frontend/runtime-contract.md)

```tsx
import { createContext, useContext } from "react";
import type { ReactNode } from "react";
import type { DataProvider } from "react-admin";

import {
  buildAdminResourceMap,
  loadAdminYamlFromUrl,
  normalizeAdminYaml,
} from "./adminSchema";
import type { RawAdminYaml, Schema } from "./adminSchema";

import { createSearchEnabledDataProvider } from "./createSearchEnabledDataProvider";
import { createSafrsJsonApiDataProvider } from "./createSafrsJsonApiDataProvider";
import {
  buildUploadFieldMap,
  createUploadAwareDataProvider,
} from "../files/uploadAwareDataProvider";

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

export async function loadAdminBootstrap(config: AdminAppConfig): Promise<{
  dataProvider: DataProvider;
  rawYaml: RawAdminYaml;
  schema: Schema;
}> {
  let rawYaml: RawAdminYaml | undefined;

  try {
    rawYaml = await loadAdminYamlFromUrl(
      config.adminYamlUrl,
      fetch,
    );
    const schema = normalizeAdminYaml(rawYaml) as Schema;
    const baseProvider = createSafrsJsonApiDataProvider({
      apiRoot: config.apiRoot,
      fetch,
      resourceMap: buildAdminResourceMap(schema, rawYaml),
    });
    const searchEnabledProvider = createSearchEnabledDataProvider({
      apiRoot: config.apiRoot,
      baseProvider,
      fetch,
      rawYaml,
      schema,
    }) as unknown as DataProvider;
    const uploadFieldMap = buildUploadFieldMap(rawYaml);
    const dataProvider = Object.keys(uploadFieldMap).length > 0
      ? createUploadAwareDataProvider(searchEnabledProvider, {
          apiRoot: config.apiRoot,
          uploadFieldMap,
        })
      : searchEnabledProvider;

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

- `normalizeAdminYaml(...)` is part of the required local shared-runtime
  contract. It converts playbook `admin.yaml` authoring input into the
  normalized resource/search metadata consumed by the runtime.
- The runtime MUST preserve raw `tab_groups` alongside the normalized schema
  because relationship-group ordering still comes from author-authored
  `admin.yaml`.
- The generated frontend test suite MUST include one direct integration test
  that calls `loadAdminBootstrap(...)`, then proves a representative scalar
  field survives through `dataProvider.getList(...)`.
- If the app supports upload-backed fields, wrap the returned provider with the
  `shared-runtime/files/uploadAwareDataProvider.ts` helper after the
  search-enabled provider is created.
- The shipped upload wrapper is expected to derive its mapping from raw
  `admin.yaml` upload field declarations; do not leave upload support as an
  undocumented manual integration step.
- Keep React-Admin's `DataProvider` as the only external runtime interface
  boundary. The schema loader, normalizer, and SAFRS JSON:API adapter stay
  local under `src/shared-runtime/admin/`.
