# `frontend/src/shared-runtime/admin/adminSchema.ts`

See also:

- [../../../../../runs/current/artifacts/architecture/runtime-bom.md](../../../../../runs/current/artifacts/architecture/runtime-bom.md)
- [../../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../../specs/contracts/frontend/admin-yaml-contract.md)

This file owns the playbook authoring types for `admin.yaml`.

The canonical normalized schema model and canonical base data provider come
from `safrs-jsonapi-client`. Do not rebuild those locally here.

```ts
import YAML from "yaml";

type VisibilitySetting = boolean | string | undefined;
type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export interface RawSearchCol {
  name: string;
  op?: string;
  template?: string;
  val?: string;
}

export interface RawAttribute {
  accept?: string;
  create?: boolean;
  edit?: boolean;
  hidden?: VisibilitySetting;
  label?: string;
  list?: boolean;
  order?: number;
  placeholder?: string;
  readonly?: boolean;
  reference?: string;
  required?: boolean;
  rows?: number;
  purpose?: string;
  search?: boolean | string;
  show?: boolean;
  type?: string;
  upload_target?: string;
  widget?: string;
  form_span?: number;
  full_width?: boolean;
  help?: string;
}

export interface RawTabGroup {
  label?: string;
  relationships?: string[];
}

export interface RawResource {
  attributes?: Record<string, RawAttribute>;
  endpoint?: string;
  hidden?: VisibilitySetting;
  label?: string;
  menu_order?: number;
  search_cols?: Array<string | RawSearchCol>;
  tab_groups?: Record<string, RawTabGroup>;
  user_key?: string;
}

export interface RawAdminYaml {
  resources?: Record<string, RawResource>;
}

function defaultFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  if (typeof globalThis.fetch !== "function") {
    throw new Error("A fetch implementation is required to load admin.yaml.");
  }

  return globalThis.fetch(input, init);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export async function loadPlaybookAdminYaml(
  adminYamlUrl: string,
  fetchImpl: FetchLike = defaultFetch,
): Promise<RawAdminYaml> {
  const response = await fetchImpl(adminYamlUrl, {
    headers: {
      Accept: "application/yaml, text/yaml, text/plain, */*",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Failed to load admin.yaml from '${adminYamlUrl}' (${response.status} ${response.statusText}).`,
    );
  }

  const source = await response.text();
  const parsed = YAML.parse(source);

  if (!isRecord(parsed)) {
    throw new Error("admin.yaml must parse to an object root.");
  }

  return parsed as RawAdminYaml;
}
```

Notes:

- This file defines the playbook authoring shape, not a second long-lived
  normalized schema system.
- `schemaContext.tsx` should adapt this authoring shape into the
  `safrs-jsonapi-client` input shape, then call the package normalizer.
- `tab_groups` is part of the executable authoring contract and must remain
  available through that adaptation path.
