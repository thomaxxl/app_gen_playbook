# `frontend/src/shared-runtime/admin/resourceMetadata.ts`

See also:

- [../../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../../specs/contracts/frontend/admin-yaml-contract.md)
- [../../../../../specs/contracts/frontend/record-shape.md](../../../../../specs/contracts/frontend/record-shape.md)
- [../../../../../specs/contracts/frontend/relationship-ui.md](../../../../../specs/contracts/frontend/relationship-ui.md)

```tsx
import { useMemo } from "react";

import type { Schema, SchemaAttribute, SearchCol } from "safrs-jsonapi-client";

import { useAdminSchema, useRawAdminYaml } from "./schemaContext";

type AttributeType = "boolean" | "date" | "file" | "image" | "number" | "reference" | "text";

type VisibilitySetting = boolean | string | undefined;

interface RawAttribute {
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
  purpose?: string;
  search?: boolean | string;
  show?: boolean;
  type?: string;
  upload_target?: string;
  widget?: string;
  help?: string;
}

interface RawTabGroup {
  label?: string;
  relationships?: string[];
}

interface RawResource {
  attributes?: Record<string, RawAttribute>;
  endpoint?: string;
  hidden?: VisibilitySetting;
  label?: string;
  menu_order?: number;
  tab_groups?: Record<string, RawTabGroup>;
  user_key?: string;
}

export interface RawAdminYaml {
  resources?: Record<string, RawResource>;
}

export interface ResourceAttributeMeta extends SchemaAttribute {
  accept?: string;
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
  purpose?: string;
  search?: boolean;
  show?: boolean;
  isPrimaryKey: boolean;
  uploadTarget?: string;
}

export interface ResourceMeta {
  attributes: ResourceAttributeMeta[];
  endpoint: string;
  hidden?: VisibilitySetting;
  label: string;
  menuOrder?: number;
  name: string;
  relationships: ResourceRelationshipMeta[];
  searchColumns: Array<SearchCol & { label: string }>;
  userKey?: string;
}

export interface ResourceRelationshipMeta {
  name: string;
  label: string;
  direction: "toone" | "tomany";
  targetResource: string;
  fks: string[];
  attributes: string[];
  compositeDelimiter?: string;
  hidden?: VisibilitySetting;
  hideList?: boolean;
  hideShow?: boolean;
  hideEdit?: boolean;
}

interface SchemaRelationshipInput {
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

  if (rawAttribute?.type === "image") {
    return "image";
  }

  if (rawAttribute?.type === "file") {
    return "file";
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

function normalizeLookupToken(value: string): string {
  return value.replace(/[_\-\s]+/g, "").toLowerCase();
}

function singularizeRelationshipName(value: string): string {
  return value.endsWith("ies")
    ? `${value.slice(0, -3)}y`
    : value.endsWith("s")
      ? value.slice(0, -1)
      : value;
}

function isLikelyPluralRelationship(value: string): boolean {
  const lowered = value.toLowerCase();
  return lowered.endsWith("ies") || lowered.endsWith("s");
}

function inferRelationshipDirection(name: string, explicitDirection: unknown): "toone" | "tomany" {
  if (explicitDirection === "toone" || explicitDirection === "tomany") {
    return explicitDirection;
  }

  return isLikelyPluralRelationship(name) ? "tomany" : "toone";
}

function findResourceNameByCandidate(
  rawYaml: RawAdminYaml,
  candidate: string | undefined,
): string | undefined {
  if (!candidate) {
    return undefined;
  }

  const normalizedCandidate = normalizeLookupToken(candidate);

  return Object.keys(rawYaml.resources ?? {}).find((resourceName) => {
    const resourceToken = normalizeLookupToken(resourceName);
    return resourceToken === normalizedCandidate;
  });
}

function inferTargetResource(
  rawYaml: RawAdminYaml,
  relationshipName: string,
  explicitTarget: string | undefined,
): string | undefined {
  const direct = findResourceNameByCandidate(rawYaml, explicitTarget);
  if (direct) {
    return direct;
  }

  const singular = singularizeRelationshipName(relationshipName);
  return (
    findResourceNameByCandidate(rawYaml, relationshipName)
    ?? findResourceNameByCandidate(rawYaml, singular)
  );
}

function getSchemaRelationshipInputs(
  schema: Schema,
  resource: string,
): SchemaRelationshipInput[] {
  const schemaResource = getSchemaResource(schema, resource) as
    | {
        relationshipConfigs?: unknown;
        relationships?: unknown;
      }
    | undefined;

  if (!schemaResource) {
    return [];
  }

  if (Array.isArray(schemaResource.relationshipConfigs)) {
    return schemaResource.relationshipConfigs as SchemaRelationshipInput[];
  }

  if (Array.isArray(schemaResource.relationships)) {
    return schemaResource.relationships as SchemaRelationshipInput[];
  }

  if (schemaResource.relationships && typeof schemaResource.relationships === "object") {
    return Object.entries(
      schemaResource.relationships as Record<string, SchemaRelationshipInput>,
    ).map(([name, config]) => ({
      ...config,
      name,
    }));
  }

  return [];
}

function getRelationshipNameFromFkMap(
  schema: Schema,
  resource: string,
  attributeName: string,
): string | undefined {
  const mapping = (schema as { fkToRelationship?: Record<string, unknown> }).fkToRelationship ?? {};
  const candidates = [
    `${resource}.${attributeName}`,
    `${resource}:${attributeName}`,
    `${resource}/${attributeName}`,
    attributeName,
  ];

  for (const key of candidates) {
    const resolved = mapping[key];
    if (typeof resolved === "string" && resolved) {
      return resolved;
    }

    if (
      resolved
      && typeof resolved === "object"
      && "name" in resolved
      && typeof resolved.name === "string"
      && resolved.name
    ) {
      return resolved.name;
    }
  }

  return undefined;
}

function inferTooneForeignKeys(
  rawAttributeMap: Map<string, RawAttribute>,
  relationshipName: string,
): string[] {
  const singular = singularizeRelationshipName(relationshipName);
  const fkName = `${singular}_id`;
  return rawAttributeMap.has(fkName) ? [fkName] : [];
}

function inferTomanyForeignKeys(
  rawYaml: RawAdminYaml,
  parentResource: string,
  targetResource: string,
): string[] {
  const targetAttributes = Object.entries(
    getRawResource(rawYaml, targetResource)?.attributes ?? {},
  );
  const parentToken = normalizeLookupToken(parentResource);
  const preferredFk = `${singularizeRelationshipName(parentResource)}_id`;

  const matches = targetAttributes
    .filter(([attributeName, attribute]) => {
      const referenceToken = normalizeLookupToken(attribute.reference ?? "");
      return (
        referenceToken === parentToken
        || normalizeLookupToken(attributeName) === normalizeLookupToken(preferredFk)
      );
    })
    .map(([attributeName]) => attributeName);

  return [...new Set(matches)];
}

function buildRelationshipMeta(
  schema: Schema,
  rawYaml: RawAdminYaml,
  resource: string,
): ResourceRelationshipMeta[] {
  const rawResource = getRawResource(rawYaml, resource);
  const rawAttributeMap = buildRawAttributeMap(rawResource);
  const relationshipsByName = new Map<string, ResourceRelationshipMeta>();

  for (const input of getSchemaRelationshipInputs(schema, resource)) {
    const name = input.name?.trim();
    if (!name) {
      continue;
    }

    const direction = inferRelationshipDirection(name, input.direction);
    const targetResource = inferTargetResource(rawYaml, name, input.targetResource);
    if (!targetResource) {
      throw new Error(`Unable to infer target resource for relationship '${name}' on '${resource}'.`);
    }

    const fallbackFks = direction === "toone"
      ? inferTooneForeignKeys(rawAttributeMap, name)
      : inferTomanyForeignKeys(rawYaml, resource, targetResource);
    const fks = [...new Set([...(input.fks ?? []), ...fallbackFks])];

    relationshipsByName.set(name, {
      name,
      label: normalizeLabel(input.label, name),
      direction,
      targetResource,
      fks,
      attributes: input.attributes ?? [],
      compositeDelimiter: input.compositeDelimiter,
      hidden: input.hidden,
      hideList: input.hideList,
      hideShow: input.hideShow,
      hideEdit: input.hideEdit,
    });
  }

  for (const [attributeName, rawAttribute] of rawAttributeMap.entries()) {
    const relationshipName = getRelationshipNameFromFkMap(schema, resource, attributeName)
      ?? (rawAttribute.reference ? singularizeRelationshipName(attributeName.replace(/_id$/, "")) : undefined);
    if (!relationshipName || relationshipsByName.has(relationshipName)) {
      continue;
    }

    const targetResource = inferTargetResource(rawYaml, relationshipName, rawAttribute.reference);
    if (!targetResource) {
      throw new Error(
        `Unable to infer target resource for foreign key '${attributeName}' on '${resource}'.`,
      );
    }

    relationshipsByName.set(relationshipName, {
      name: relationshipName,
      label: normalizeLabel(rawAttribute.label, relationshipName),
      direction: "toone",
      targetResource,
      fks: [attributeName],
      attributes: [attributeName],
    });
  }

  const orderedNames = Object.values(rawResource?.tab_groups ?? {}).flatMap(
    (group) => group.relationships ?? [],
  );

  for (const relationshipName of orderedNames) {
    if (relationshipsByName.has(relationshipName)) {
      continue;
    }

    const direction = inferRelationshipDirection(relationshipName, undefined);
    const targetResource = inferTargetResource(rawYaml, relationshipName, undefined);
    if (!targetResource) {
      throw new Error(
        `Unable to infer target resource for tab-group relationship '${relationshipName}' on '${resource}'.`,
      );
    }

    const fks = direction === "toone"
      ? inferTooneForeignKeys(rawAttributeMap, relationshipName)
      : inferTomanyForeignKeys(rawYaml, resource, targetResource);

    relationshipsByName.set(relationshipName, {
      name: relationshipName,
      label: normalizeLabel(undefined, relationshipName),
      direction,
      targetResource,
      fks,
      attributes: [],
    });
  }

  const orderedRelationships = orderedNames
    .map((name) => relationshipsByName.get(name))
    .filter((relationship): relationship is ResourceRelationshipMeta => Boolean(relationship));
  const unorderedRelationships = [...relationshipsByName.values()].filter(
    (relationship) => !orderedNames.includes(relationship.name),
  );

  return [...orderedRelationships, ...unorderedRelationships];
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
  const relationships = buildRelationshipMeta(schema, rawYaml, resource);

  return {
    attributes: schemaResource.attributeConfigs.map((attribute) => {
      const rawAttribute = rawAttributeMap.get(attribute.name);
      return {
        ...attribute,
        accept: rawAttribute?.accept,
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
        purpose: rawAttribute?.purpose,
        search: isSearchEnabled(rawAttribute?.search),
        show: rawAttribute?.show,
        isPrimaryKey: isPrimaryKeyName(resource, attribute.name),
        uploadTarget: rawAttribute?.upload_target,
      } satisfies ResourceAttributeMeta;
    }),
    endpoint: rawResource.endpoint,
    hidden: rawResource?.hidden,
    label: normalizeLabel(rawResource?.label, resource),
    menuOrder: rawResource?.menu_order,
    name: resource,
    relationships,
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

Required relationship extension:

- `buildResourceMeta(...)` MUST synthesize relationship metadata by combining:
  - normalized schema relationship metadata
  - `schema.fkToRelationship`
  - raw `admin.yaml tab_groups`
- `buildResourceMeta(...)` MUST attach a resolved `relationship` to a `toone`
  foreign-key attribute when `schema.fkToRelationship` identifies it
- raw `tab_groups` MUST be consumed here so the runtime can preserve
  author-defined relationship ordering and labels
- the runtime SHOULD maintain a relationship-by-name lookup here or in a
  closely related helper so list/show rendering can collapse duplicate
  foreign-key columns into one relationship display item
- fallback rules MUST include:
  - plural relationship name => default `tomany`
  - singular relationship name => default `toone`
  - infer target resource from resource-name matching when target metadata is
    absent
  - infer `toone` foreign-key attribute as `<singular_name>_id` when present
  - infer `tomany` reverse join by inspecting the target resource for a
    `toone` relationship or FK field back to the parent and using its
    foreign-key attributes
- if fallback inference cannot establish a safe relationship definition, the
  runtime MUST fail visibly instead of silently degrading to raw-id-only UI
