# `frontend/src/shared-runtime/admin/adminSchema.ts`

See also:

- [../../../../../runs/current/artifacts/architecture/runtime-bom.md](../../../../../runs/current/artifacts/architecture/runtime-bom.md)
- [../../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../../specs/contracts/frontend/admin-yaml-contract.md)

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

export interface RawRelationship {
  attributes?: string[];
  compositeDelimiter?: string;
  direction?: "toone" | "tomany" | string;
  fks?: string[];
  hidden?: VisibilitySetting;
  hideEdit?: boolean;
  hideList?: boolean;
  hideShow?: boolean;
  label?: string;
  name?: string;
  targetResource?: string;
}

export interface RawResource {
  attributes?: Record<string, RawAttribute>;
  endpoint?: string;
  hidden?: VisibilitySetting;
  label?: string;
  menu_order?: number;
  relationships?: Record<string, RawRelationship> | RawRelationship[];
  search_cols?: Array<string | RawSearchCol>;
  tab_groups?: Record<string, RawTabGroup>;
  user_key?: string;
}

export interface RawAdminYaml {
  resources?: Record<string, RawResource>;
}

export interface SearchCol {
  name: string;
  op?: string;
  val?: string;
}

export interface SchemaAttribute {
  hideEdit?: boolean;
  name: string;
  reference?: string;
  required?: boolean;
  search?: boolean;
  type?: string;
}

export interface SchemaRelationshipConfig {
  attributes?: string[];
  compositeDelimiter?: string;
  direction?: "toone" | "tomany" | string;
  fks?: string[];
  hidden?: VisibilitySetting;
  hideEdit?: boolean;
  hideList?: boolean;
  hideShow?: boolean;
  label?: string;
  name: string;
  targetResource?: string;
}

export interface SchemaResource {
  attributeConfigs: SchemaAttribute[];
  endpoint: string;
  relationshipConfigs: SchemaRelationshipConfig[];
  relationships: Record<string, SchemaRelationshipConfig>;
  searchCols: SearchCol[];
  type: string;
  userKey?: string;
}

export interface Schema {
  fkToRelationship: Record<string, string>;
  resourceByType: Record<string, string>;
  resources: Record<string, SchemaResource>;
}

export interface ResourceMapSearchField {
  name: string;
  op?: string;
  template?: string;
}

export interface ResourceMapRelationshipField {
  toMany?: boolean;
  type: string;
}

export interface ResourceMapEntry {
  endpoint: string;
  relationshipFields: Record<string, ResourceMapRelationshipField>;
  searchFields: ResourceMapSearchField[];
  type: string;
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

  return normalized || String(endpoint ?? "").trim();
}

function singularizeRelationshipName(value: string): string {
  return value.endsWith("ies")
    ? `${value.slice(0, -3)}y`
    : value.endsWith("s")
      ? value.slice(0, -1)
      : value;
}

function normalizeSearchColumn(input: string | RawSearchCol): ResourceMapSearchField | null {
  if (typeof input === "string" && input.trim()) {
    return {
      name: input.trim(),
      op: "ilike",
      template: "%{q}%",
    };
  }

  if (!input || typeof input.name !== "string" || !input.name.trim()) {
    return null;
  }

  return {
    name: input.name.trim(),
    op: typeof input.op === "string" && input.op.trim() ? input.op.trim() : "ilike",
    template: typeof input.template === "string" && input.template
      ? input.template
      : typeof input.val === "string" && input.val
        ? input.val
        : "%{q}%",
  };
}

function normalizeRelationshipConfig(
  name: string,
  relationship: RawRelationship,
): SchemaRelationshipConfig {
  return {
    attributes: Array.isArray(relationship.attributes) ? [...relationship.attributes] : [],
    compositeDelimiter: relationship.compositeDelimiter,
    direction: relationship.direction,
    fks: Array.isArray(relationship.fks) ? [...relationship.fks] : [],
    hidden: relationship.hidden,
    hideEdit: relationship.hideEdit,
    hideList: relationship.hideList,
    hideShow: relationship.hideShow,
    label: relationship.label,
    name,
    targetResource: relationship.targetResource,
  };
}

function getExplicitRelationshipEntries(resource: RawResource): Array<[string, RawRelationship]> {
  if (Array.isArray(resource.relationships)) {
    return resource.relationships.flatMap((relationship) => {
      const name = relationship?.name?.trim();
      return name ? [[name, relationship]] : [];
    });
  }

  if (isRecord(resource.relationships)) {
    return Object.entries(resource.relationships).flatMap(([name, relationship]) => {
      return isRecord(relationship)
        ? [[name, relationship as RawRelationship]]
        : [];
    });
  }

  return [];
}

function buildRelationshipConfigs(
  resourceName: string,
  resource: RawResource,
): SchemaRelationshipConfig[] {
  const explicitRelationships = getExplicitRelationshipEntries(resource).map(
    ([name, relationship]) => normalizeRelationshipConfig(name, relationship),
  );
  const byName = new Map(
    explicitRelationships.map((relationship) => [relationship.name, relationship]),
  );

  for (const [attributeName, attribute] of Object.entries(resource.attributes ?? {})) {
    if (!attribute.reference) {
      continue;
    }

    const relationshipName = singularizeRelationshipName(attributeName.replace(/_id$/, ""));
    if (byName.has(relationshipName)) {
      continue;
    }

    byName.set(relationshipName, {
      attributes: [attributeName],
      direction: "toone",
      fks: [attributeName],
      label: attribute.label,
      name: relationshipName,
      targetResource: attribute.reference,
    });
  }

  return [...byName.values()];
}

function buildFkToRelationship(
  resourceName: string,
  schemaKey: string,
  resource: RawResource,
  relationships: SchemaRelationshipConfig[],
): Record<string, string> {
  const mapping: Record<string, string> = {};

  for (const relationship of relationships) {
    for (const fk of relationship.fks ?? []) {
      mapping[`${resourceName}.${fk}`] = relationship.name;
      mapping[`${schemaKey}.${fk}`] = relationship.name;
    }
  }

  for (const [attributeName, attribute] of Object.entries(resource.attributes ?? {})) {
    if (!attribute.reference) {
      continue;
    }

    const relationshipName = singularizeRelationshipName(attributeName.replace(/_id$/, ""));
    mapping[`${resourceName}.${attributeName}`] = relationshipName;
    mapping[`${schemaKey}.${attributeName}`] = relationshipName;
  }

  return mapping;
}

export function normalizeAdminYaml(rawYaml: RawAdminYaml): Schema {
  const resources: Record<string, SchemaResource> = {};
  const resourceByType: Record<string, string> = {};
  const fkToRelationship: Record<string, string> = {};

  for (const [resourceName, resource] of Object.entries(rawYaml.resources ?? {})) {
    const schemaKey = toSchemaResourceKey(resource.endpoint) || resourceName;
    const attributeConfigs = Object.entries(resource.attributes ?? {}).map(
      ([name, attribute]): SchemaAttribute => ({
        hideEdit: attribute.readonly === true || attribute.edit === false,
        name,
        reference: attribute.reference,
        required: attribute.required,
        search: isSearchEnabled(attribute.search),
        type: attribute.type,
      }),
    );
    const searchCols = (
      Array.isArray(resource.search_cols)
        ? resource.search_cols.map(normalizeSearchColumn).filter(Boolean)
        : []
    ) as ResourceMapSearchField[];
    const relationshipConfigs = buildRelationshipConfigs(resourceName, resource);

    resources[schemaKey] = {
      attributeConfigs,
      endpoint: resource.endpoint ?? schemaKey,
      relationshipConfigs,
      relationships: Object.fromEntries(
        relationshipConfigs.map((relationship) => [relationship.name, relationship]),
      ),
      searchCols: searchCols.length > 0
        ? searchCols.map(({ name, op, template }) => ({
            name,
            op,
            val: template,
          }))
        : attributeConfigs
            .filter((attribute) => attribute.search)
            .map((attribute) => ({ name: attribute.name })),
      type: resourceName,
      userKey: resource.user_key,
    };
    resourceByType[resourceName] = schemaKey;
    resourceByType[schemaKey] = schemaKey;
    Object.assign(
      fkToRelationship,
      buildFkToRelationship(resourceName, schemaKey, resource, relationshipConfigs),
    );
  }

  return {
    fkToRelationship,
    resourceByType,
    resources,
  };
}

export async function loadAdminYamlFromUrl(
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

export function buildAdminResourceMap(
  schema: Schema,
  rawYaml: RawAdminYaml,
): Record<string, ResourceMapEntry> {
  const resourceMap: Record<string, ResourceMapEntry> = {};

  for (const [resourceName, resource] of Object.entries(rawYaml.resources ?? {})) {
    const schemaKey = schema.resourceByType[resourceName]
      ?? toSchemaResourceKey(resource.endpoint)
      ?? resourceName;
    const schemaResource = schema.resources[schemaKey];

    if (!schemaResource) {
      continue;
    }

    const searchFields = (
      Array.isArray(resource.search_cols)
        ? resource.search_cols.map(normalizeSearchColumn).filter(Boolean)
        : []
    ) as ResourceMapSearchField[];
    const relationshipFields = Object.fromEntries(
      schemaResource.relationshipConfigs.flatMap((relationship) => {
        if (!relationship.name || !relationship.targetResource) {
          return [];
        }

        return [[
          relationship.name,
          {
            toMany: String(relationship.direction).toLowerCase() === "tomany",
            type: relationship.targetResource,
          },
        ]];
      }),
    );
    const entry: ResourceMapEntry = {
      endpoint: schemaResource.endpoint,
      relationshipFields,
      searchFields: searchFields.length > 0
        ? searchFields
        : schemaResource.searchCols.map((column) => ({
            name: column.name,
            op: column.op,
            template: column.val ?? "%{q}%",
          })),
      type: schemaResource.type,
    };

    resourceMap[schemaKey] = entry;
    resourceMap[resourceName] = entry;
  }

  return resourceMap;
}
```
