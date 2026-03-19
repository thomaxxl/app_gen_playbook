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
  rows?: number;
  search?: boolean | string;
  show?: boolean;
  type?: string;
  widget?: string;
  form_span?: number;
  full_width?: boolean;
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
  max_list_columns?: number | string;
  maxListColumns?: number | string;
  menu_order?: number;
  tab_groups?: Record<string, RawTabGroup>;
  user_key?: string;
}

export interface RawAdminYaml {
  resources?: Record<string, RawResource>;
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

export interface ResourceAttributeMeta extends SchemaAttribute {
  create?: boolean;
  edit?: boolean;
  hidden?: VisibilitySetting;
  isPrimaryKey: boolean;
  kind: AttributeType;
  label: string;
  list?: boolean;
  order?: number;
  readonly?: boolean;
  reference?: string;
  relationship?: ResourceRelationshipMeta;
  required?: boolean;
  rows?: number;
  search?: boolean;
  show?: boolean;
  widget?: string;
  formSpan?: number;
  fullWidth?: boolean;
}

export interface ResourceMeta {
  attributes: ResourceAttributeMeta[];
  endpoint: string;
  hidden?: VisibilitySetting;
  label: string;
  maxListColumns: number;
  menuOrder?: number;
  name: string;
  relationshipByName: Record<string, ResourceRelationshipMeta>;
  relationships: ResourceRelationshipMeta[];
  searchColumns: Array<SearchCol & { label: string }>;
  userKey?: string;
}

function getRawResource(
  rawYaml: RawAdminYaml,
  resource: string,
): RawResource | undefined {
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

function inferFieldKind(
  attribute: SchemaAttribute,
  rawAttribute: RawAttribute | undefined,
): AttributeType {
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

function buildRawAttributeMap(
  rawResource: RawResource | undefined,
): Map<string, RawAttribute> {
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

function inferRelationshipDirection(
  name: string,
  explicitDirection: unknown,
): "toone" | "tomany" {
  const normalized = String(explicitDirection ?? "").toLowerCase();

  if (normalized === "tomany" || normalized === "many" || normalized === "to-many") {
    return "tomany";
  }

  if (normalized === "toone" || normalized === "one" || normalized === "to-one") {
    return "toone";
  }

  if (name.toLowerCase().endsWith("_records")) {
    return "tomany";
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
  parentResource: string,
  relationshipName: string,
  explicitTarget: string | undefined,
  direction: "toone" | "tomany",
): string | undefined {
  const direct = findResourceNameByCandidate(rawYaml, explicitTarget);
  if (direct) {
    return direct;
  }

  const singularRelationship = singularizeRelationshipName(relationshipName);
  const fromName = findResourceNameByCandidate(rawYaml, relationshipName)
    ?? findResourceNameByCandidate(rawYaml, singularRelationship);
  if (fromName) {
    return fromName;
  }

  const parentToken = normalizeLookupToken(parentResource);
  const preferredFk = `${singularizeRelationshipName(parentResource)}_id`;
  const candidates = Object.keys(rawYaml.resources ?? {}).filter((resourceName) => {
    if (resourceName === parentResource) {
      return false;
    }

    const rawResource = getRawResource(rawYaml, resourceName);
    return Object.entries(rawResource?.attributes ?? {}).some(([attributeName, attribute]) => {
      const referenceToken = normalizeLookupToken(attribute.reference ?? "");
      return (
        referenceToken === parentToken
        || normalizeLookupToken(attributeName) === normalizeLookupToken(preferredFk)
      );
    });
  });

  if (candidates.length === 1) {
    return candidates[0];
  }

  if (direction === "tomany") {
    const relationshipToken = normalizeLookupToken(singularRelationship);
    const tokenMatch = candidates.find((resourceName) =>
      normalizeLookupToken(resourceName).includes(relationshipToken),
    );
    if (tokenMatch) {
      return tokenMatch;
    }
  }

  return undefined;
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

function getTabGroupRelationshipNameForFk(
  rawResource: RawResource | undefined,
  rawAttributeMap: Map<string, RawAttribute>,
  attributeName: string,
): string | undefined {
  const relationshipNames = Object.values(rawResource?.tab_groups ?? {}).flatMap(
    (group) => group.relationships ?? [],
  );

  const matches = relationshipNames.filter((relationshipName) =>
    inferTooneForeignKeys(rawAttributeMap, relationshipName).includes(attributeName),
  );

  return matches.length === 1 ? matches[0] : undefined;
}

function getRelationshipNameFromFkMap(
  schema: Schema,
  resource: string,
  attributeName: string,
): string | undefined {
  const mapping = (schema as { fkToRelationship?: Record<string, unknown> }).fkToRelationship ?? {};
  const resourceMapping = mapping[resource];

  if (
    resourceMapping
    && typeof resourceMapping === "object"
    && attributeName in (resourceMapping as Record<string, unknown>)
  ) {
    const resolved = (resourceMapping as Record<string, unknown>)[attributeName];
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
  const candidates = [
    `${relationshipName}_id`,
    `${singularizeRelationshipName(relationshipName)}_id`,
  ];

  return [...new Set(candidates)].filter((fkName) => rawAttributeMap.has(fkName));
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

function getTabGroupLabel(
  rawResource: RawResource | undefined,
  relationshipName: string,
): string | undefined {
  for (const group of Object.values(rawResource?.tab_groups ?? {})) {
    const relationships = group.relationships ?? [];
    if (relationships.length === 1 && relationships[0] === relationshipName && group.label) {
      return group.label;
    }
  }

  return undefined;
}

function normalizeNumber(value: number | string | undefined, fallback: number): number {
  if (value === undefined) {
    return fallback;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
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
    const targetResource = inferTargetResource(
      rawYaml,
      resource,
      name,
      input.targetResource,
      direction,
    );
    if (!targetResource) {
      continue;
    }

    const fallbackFks = direction === "toone"
      ? inferTooneForeignKeys(rawAttributeMap, name)
      : inferTomanyForeignKeys(rawYaml, resource, targetResource);
    const fks = [...new Set([...(input.fks ?? []), ...fallbackFks])];

    relationshipsByName.set(name, {
      name,
      label: normalizeLabel(getTabGroupLabel(rawResource, name) ?? input.label, name),
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
    const relationshipName = getTabGroupRelationshipNameForFk(
      rawResource,
      rawAttributeMap,
      attributeName,
    )
      ?? getRelationshipNameFromFkMap(schema, resource, attributeName)
      ?? (rawAttribute.reference
        ? singularizeRelationshipName(attributeName.replace(/_id$/, ""))
        : undefined);
    if (!relationshipName || relationshipsByName.has(relationshipName)) {
      continue;
    }

    const targetResource = inferTargetResource(
      rawYaml,
      resource,
      relationshipName,
      rawAttribute.reference,
      "toone",
    );
    if (!targetResource) {
      continue;
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
  const schemaRelationshipNames = getSchemaRelationshipInputs(schema, resource)
    .map((relationship) => relationship.name?.trim())
    .filter((name): name is string => Boolean(name));
  const orderedRelationshipNames = [
    ...orderedNames,
    ...schemaRelationshipNames.filter((name) => !orderedNames.includes(name)),
  ];

  for (const relationshipName of orderedRelationshipNames) {
    if (relationshipsByName.has(relationshipName)) {
      continue;
    }

    const direction = inferRelationshipDirection(relationshipName, undefined);
    const targetResource = inferTargetResource(
      rawYaml,
      resource,
      relationshipName,
      undefined,
      direction,
    );
    if (!targetResource) {
      continue;
    }

    const fks = direction === "toone"
      ? inferTooneForeignKeys(rawAttributeMap, relationshipName)
      : inferTomanyForeignKeys(rawYaml, resource, targetResource);

    relationshipsByName.set(relationshipName, {
      name: relationshipName,
      label: normalizeLabel(getTabGroupLabel(rawResource, relationshipName), relationshipName),
      direction,
      targetResource,
      fks,
      attributes: [],
    });
  }

  const orderedRelationships = orderedRelationshipNames
    .map((name) => relationshipsByName.get(name))
    .filter((relationship): relationship is ResourceRelationshipMeta => Boolean(relationship));
  const unorderedRelationships = [...relationshipsByName.values()].filter(
    (relationship) => !orderedRelationshipNames.includes(relationship.name),
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
  const relationshipByName = Object.fromEntries(
    relationships.map((relationship) => [relationship.name, relationship]),
  ) as Record<string, ResourceRelationshipMeta>;
  const relationshipByFk = new Map<string, ResourceRelationshipMeta>();

  for (const relationship of relationships) {
    if (relationship.direction !== "toone") {
      continue;
    }

    for (const fk of relationship.fks) {
      relationshipByFk.set(fk, relationship);
    }
  }

  return {
    attributes: schemaResource.attributeConfigs.map((attribute) => {
      const rawAttribute = rawAttributeMap.get(attribute.name);
      return {
        ...attribute,
        create: rawAttribute?.create,
        edit: rawAttribute?.edit,
        hidden: rawAttribute?.hidden,
        isPrimaryKey: isPrimaryKeyName(resource, attribute.name),
        kind: inferFieldKind(attribute, rawAttribute),
        label: normalizeLabel(rawAttribute?.label, attribute.name),
        list: rawAttribute?.list,
        order: rawAttribute?.order,
        readonly: rawAttribute?.readonly,
        reference: rawAttribute?.reference,
        relationship: relationshipByFk.get(attribute.name),
        required: rawAttribute?.required,
        rows: rawAttribute?.rows,
        search: isSearchEnabled(rawAttribute?.search),
        show: rawAttribute?.show,
        widget: rawAttribute?.widget,
        formSpan: rawAttribute?.form_span,
        fullWidth: rawAttribute?.full_width,
      } satisfies ResourceAttributeMeta;
    }),
    endpoint: rawResource.endpoint,
    hidden: rawResource.hidden,
    label: normalizeLabel(rawResource.label, resource),
    maxListColumns: normalizeNumber(
      rawResource.max_list_columns ?? rawResource.maxListColumns,
      8,
    ),
    menuOrder: rawResource.menu_order,
    name: resource,
    relationshipByName,
    relationships,
    searchColumns: resolveSearchColumns(schema, rawYaml, resource).map((column) => ({
      ...column,
      label: normalizeLabel(rawAttributeMap.get(column.name)?.label, column.name),
    })),
    userKey: schemaResource.userKey ?? rawResource.user_key,
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

  return useMemo(() => buildResourceMeta(schema, rawYaml, resource), [
    rawYaml,
    resource,
    schema,
  ]);
}
