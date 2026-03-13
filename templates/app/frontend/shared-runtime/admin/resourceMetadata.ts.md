# `frontend/src/shared-runtime/admin/resourceMetadata.ts`

See also:

- [../../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../../specs/contracts/frontend/admin-yaml-contract.md)
- [../../../../../specs/contracts/frontend/record-shape.md](../../../../../specs/contracts/frontend/record-shape.md)

```tsx
import { useMemo } from "react";

import type { Schema, SchemaAttribute, SearchCol } from "safrs-jsonapi-client";

import { useAdminSchema, useRawAdminYaml } from "./schemaContext";

type AttributeType = "boolean" | "date" | "number" | "reference" | "text";

type VisibilitySetting = boolean | string | undefined;

interface RawAttribute {
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
  search?: boolean | string;
  show?: boolean;
  type?: string;
  widget?: string;
  help?: string;
}

interface RawResource {
  attributes?: Record<string, RawAttribute>;
  endpoint?: string;
  hidden?: VisibilitySetting;
  label?: string;
  menu_order?: number;
  tab_groups?: Record<string, { label?: string; relationships?: string[] }>;
  user_key?: string;
}

export interface RawAdminYaml {
  resources?: Record<string, RawResource>;
}

export interface ResourceAttributeMeta extends SchemaAttribute {
  create?: boolean;
  edit?: boolean;
  hidden?: VisibilitySetting;
  kind: AttributeType;
  label: string;
  list?: boolean;
  order?: number;
  readonly?: boolean;
  reference?: string;
  required?: boolean;
  search?: boolean;
  show?: boolean;
  isPrimaryKey: boolean;
}

export interface ResourceMeta {
  attributes: ResourceAttributeMeta[];
  endpoint: string;
  hidden?: VisibilitySetting;
  label: string;
  menuOrder?: number;
  name: string;
  searchColumns: Array<SearchCol & { label: string }>;
  userKey?: string;
}

function getRawResource(rawYaml: RawAdminYaml, resource: string): RawResource | undefined {
  return rawYaml.resources?.[resource];
}

function getSchemaResource(schema: Schema, resource: string) {
  const schemaResourceKey = schema.resources[resource]
    ? resource
    : schema.resourceByType[resource];
  return schemaResourceKey ? schema.resources[schemaResourceKey] : undefined;
}

function normalizeLabel(label: string | undefined, fallbackName: string): string {
  const cleaned = label?.trim().replace(/\*+$/, "").trim();
  if (cleaned) {
    return cleaned;
  }

  return fallbackName
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function inferFieldKind(attribute: SchemaAttribute, rawAttribute: RawAttribute | undefined): AttributeType {
  if (rawAttribute?.type === "reference" || rawAttribute?.reference) {
    return "reference";
  }

  const rawType = String(attribute.type ?? rawAttribute?.type ?? "").toLowerCase();

  if (rawType.includes("bool")) {
    return "boolean";
  }

  if (rawType.includes("date") || rawType.includes("time")) {
    return "date";
  }

  if (
    rawType.includes("int")
    || rawType.includes("float")
    || rawType.includes("double")
    || rawType.includes("numeric")
    || rawType.includes("decimal")
    || rawAttribute?.type === "number"
  ) {
    return "number";
  }

  return "text";
}

function isPrimaryKeyName(resource: string, attributeName: string): boolean {
  const lowered = attributeName.toLowerCase();
  return lowered === "id" || lowered === `${resource.toLowerCase()}id`;
}

function buildRawAttributeMap(rawResource: RawResource | undefined): Map<string, RawAttribute> {
  return new Map(Object.entries(rawResource?.attributes ?? {}));
}

function isSearchEnabled(value: boolean | string | undefined): boolean {
  return value === true || value === "true";
}

export function resolveSearchColumns(
  schema: Schema,
  rawYaml: RawAdminYaml,
  resource: string,
): SearchCol[] {
  const schemaResource = getSchemaResource(schema, resource);
  if (!schemaResource) {
    return [];
  }

  if (schemaResource.searchCols.length > 0) {
    return schemaResource.searchCols;
  }

  const rawAttributeMap = buildRawAttributeMap(getRawResource(rawYaml, resource));
  return schemaResource.attributeConfigs
    .filter((attribute) => isSearchEnabled(rawAttributeMap.get(attribute.name)?.search))
    .map((attribute) => ({ name: attribute.name }));
}

export function buildResourceMeta(
  schema: Schema,
  rawYaml: RawAdminYaml,
  resource: string,
): ResourceMeta {
  const schemaResource = getSchemaResource(schema, resource);
  if (!schemaResource) {
    throw new Error(`Unknown resource '${resource}'.`);
  }

  const rawResource = getRawResource(rawYaml, resource);
  if (!rawResource?.endpoint) {
    throw new Error(`Resource '${resource}' is missing admin.yaml endpoint.`);
  }
  const rawAttributeMap = buildRawAttributeMap(rawResource);

  return {
    attributes: schemaResource.attributeConfigs.map((attribute) => {
      const rawAttribute = rawAttributeMap.get(attribute.name);
      return {
        ...attribute,
        create: rawAttribute?.create,
        edit: rawAttribute?.edit,
        hidden: rawAttribute?.hidden,
        kind: inferFieldKind(attribute, rawAttribute),
        label: normalizeLabel(rawAttribute?.label, attribute.name),
        list: rawAttribute?.list,
        order: rawAttribute?.order,
        readonly: rawAttribute?.readonly,
        reference: rawAttribute?.reference,
        required: rawAttribute?.required,
        search: isSearchEnabled(rawAttribute?.search),
        show: rawAttribute?.show,
        isPrimaryKey: isPrimaryKeyName(resource, attribute.name),
      } satisfies ResourceAttributeMeta;
    }),
    endpoint: rawResource.endpoint,
    hidden: rawResource?.hidden,
    label: normalizeLabel(rawResource?.label, resource),
    menuOrder: rawResource?.menu_order,
    name: resource,
    searchColumns: resolveSearchColumns(schema, rawYaml, resource).map((column) => ({
      ...column,
      label: normalizeLabel(rawAttributeMap.get(column.name)?.label, column.name),
    })),
    userKey: schemaResource.userKey ?? rawResource?.user_key,
  };
}

export function resolveResourceEndpoint(
  schema: Schema,
  rawYaml: RawAdminYaml,
  resource: string,
): string {
  return buildResourceMeta(schema, rawYaml, resource).endpoint;
}

export function useResourceMeta(resource: string): ResourceMeta {
  const schema = useAdminSchema();
  const rawYaml = useRawAdminYaml();

  return useMemo(() => buildResourceMeta(schema, rawYaml, resource), [rawYaml, resource, schema]);
}
```
