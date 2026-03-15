# `frontend/src/shared-runtime/admin/createSearchEnabledDataProvider.ts`

See also:

- [../../../../../specs/contracts/backend/query-contract.md](../../../../../specs/contracts/backend/query-contract.md)
- [../../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../../specs/contracts/frontend/admin-yaml-contract.md)

```tsx
import type { DataProvider } from "react-admin";

import type { RawAdminYaml } from "./resourceMetadata";
import { resolveResourceEndpoint, resolveSearchColumns } from "./resourceMetadata";

type Schema = Parameters<typeof resolveSearchColumns>[0];
type SearchCol = ReturnType<typeof resolveSearchColumns>[number];
type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
type LoggerLike = Pick<Console, "error" | "warn">;

interface JsonApiResourceObject {
  id?: string | number;
  attributes?: Record<string, unknown>;
}

interface JsonApiDocument {
  data?: JsonApiResourceObject | JsonApiResourceObject[] | null;
  meta?: Record<string, unknown> & {
    pagination?: Record<string, unknown>;
  };
}

interface ListParams {
  filter?: Record<string, unknown>;
  meta?: {
    include?: string | string[];
  };
  pagination?: {
    page?: number;
    perPage?: number;
  };
  sort?: {
    field?: string;
    order?: string;
  };
}

function queryToSearchParams(query: Record<string, string | number | boolean>): URLSearchParams {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(query)) {
    params.set(key, String(value));
  }

  return params;
}

function appendQuery(url: string, query: Record<string, string | number | boolean>): string {
  const queryString = queryToSearchParams(query).toString();
  return queryString ? `${url}?${queryString}` : url;
}

function trimTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, "");
}

function isAbsoluteUrl(value: string): boolean {
  return /^https?:\/\//i.test(value);
}

function resolveEndpointUrl(apiRoot: string, endpoint: string): string {
  const trimmedApiRoot = trimTrailingSlashes(apiRoot);

  if (isAbsoluteUrl(endpoint)) {
    return endpoint;
  }

  if (endpoint.startsWith("/")) {
    if (isAbsoluteUrl(trimmedApiRoot)) {
      const apiUrl = new URL(trimmedApiRoot);
      if (endpoint === apiUrl.pathname || endpoint.startsWith(`${apiUrl.pathname}/`)) {
        return `${apiUrl.origin}${endpoint}`;
      }
    }
    return endpoint;
  }

  return `${trimmedApiRoot}/${endpoint.replace(/^\/+/, "")}`;
}

function resolveSchemaResourceKey(schema: Schema, resource: string): string {
  return schema.resources[resource] ? resource : (schema.resourceByType[resource] ?? resource);
}

function buildListQuery(
  _resource: string,
  params: ListParams = {},
): Record<string, string | number | boolean> {
  const query: Record<string, string | number | boolean> = {};
  const pagination = params.pagination ?? {};
  const sort = params.sort ?? {};
  const filter = { ...(params.filter ?? {}) };
  const rawJsonApiFilter = filter.__jsonapi;

  delete filter.__jsonapi;

  if (typeof pagination.page === "number") {
    query["page[number]"] = pagination.page;
  }

  if (typeof pagination.perPage === "number") {
    query["page[size]"] = pagination.perPage;
  }

  if (typeof sort.field === "string" && sort.field.trim()) {
    const prefix = String(sort.order).toUpperCase() === "DESC" ? "-" : "";
    query.sort = `${prefix}${sort.field.trim()}`;
  }

  const include = params.meta?.include;
  if (Array.isArray(include) && include.length > 0) {
    query.include = include.join(",");
  } else if (typeof include === "string" && include.trim()) {
    query.include = include.trim();
  }

  if (rawJsonApiFilter && typeof rawJsonApiFilter === "object") {
    query.filter = JSON.stringify(rawJsonApiFilter);
  }

  for (const [name, value] of Object.entries(filter)) {
    if (name === "q" || value === undefined || value === null || value === "") {
      continue;
    }

    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      query[`filter[${name}]`] = value;
    }
  }

  return query;
}

function applySearchTemplate(template: string | undefined, search: string): string {
  if (!template) {
    return `%${search}%`;
  }

  if (template.includes("{q}")) {
    return template.split("{q}").join(search);
  }

  if (template.includes("{}")) {
    return template.split("{}").join(search);
  }

  if (template.includes("%s")) {
    return template.split("%s").join(search);
  }

  return template;
}

export function buildJsonApiSearchFilter(
  search: string,
  searchCols: SearchCol[],
): { or: Array<{ name: string; op: string; val: string }> } {
  return {
    or: searchCols.map((column) => ({
      name: column.name,
      op: column.op ?? "ilike",
      val: applySearchTemplate(column.val, search),
    })),
  };
}

function parseExistingJsonFilter(
  value: string | undefined,
): Record<string, unknown> | undefined {
  if (!value) {
    return undefined;
  }

  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" ? parsed as Record<string, unknown> : undefined;
  } catch {
    return undefined;
  }
}

function consumeScalarFilterClauses(
  query: Record<string, string | number | boolean>,
): Array<{ name: string; op: string; val: string | number | boolean }> {
  const clauses: Array<{ name: string; op: string; val: string | number | boolean }> = [];

  for (const key of Object.keys(query)) {
    const match = key.match(/^filter\[(.+)\]$/);
    if (!match) {
      continue;
    }

    clauses.push({
      name: match[1],
      op: "eq",
      val: query[key],
    });
    delete query[key];
  }

  return clauses;
}

export function mergeSearchWithExistingFilters(
  query: Record<string, string | number | boolean>,
  searchFilter: Record<string, unknown>,
): string {
  const conditions: Record<string, unknown>[] = [];
  const existingJsonFilter = typeof query.filter === "string"
    ? parseExistingJsonFilter(query.filter)
    : undefined;

  if (existingJsonFilter) {
    conditions.push(existingJsonFilter);
  }

  const scalarClauses = consumeScalarFilterClauses(query);
  if (scalarClauses.length === 1) {
    conditions.push(scalarClauses[0]);
  } else if (scalarClauses.length > 1) {
    conditions.push({ and: scalarClauses });
  }

  conditions.push(searchFilter);
  delete query.filter;

  if (conditions.length === 1) {
    return JSON.stringify(conditions[0]);
  }

  return JSON.stringify({ and: conditions });
}

function omitSearchFilter(filter: Record<string, unknown> | undefined): Record<string, unknown> | undefined {
  if (!filter || !("q" in filter)) {
    return filter;
  }

  const { q: _q, ...rest } = filter;
  return Object.keys(rest).length > 0 ? rest : undefined;
}

function normalizeResourceObject(resourceObject: JsonApiResourceObject | null | undefined): Record<string, unknown> | null {
  if (!resourceObject || resourceObject.id === undefined || resourceObject.id === null) {
    return null;
  }

  return {
    id: resourceObject.id,
    ...(resourceObject.attributes ?? {}),
  };
}

function normalizeDocument(document: JsonApiDocument): { records: Array<Record<string, unknown>> } {
  const primaryData = Array.isArray(document.data)
    ? document.data
    : document.data
      ? [document.data]
      : [];

  return {
    records: primaryData
      .map((item) => normalizeResourceObject(item))
      .filter((item): item is Record<string, unknown> => Boolean(item)),
  };
}

function synthesizeCompositeKeys(record: Record<string, unknown>): Record<string, unknown> {
  return record;
}

function getTotal(document: JsonApiDocument, fallback: number): number {
  const candidates = [
    document.meta?.count,
    document.meta?.total,
    document.meta?.pagination?.total,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "number" && Number.isFinite(candidate)) {
      return candidate;
    }
  }

  return fallback;
}

function errorForResponse(response: Response, payload: unknown): Error & {
  payload?: unknown;
  status?: number;
} {
  const error = new Error(response.statusText || `Request failed with status ${response.status}`);
  error.status = response.status;
  error.payload = payload;
  return error;
}

async function parseResponseBody(response: Response): Promise<JsonApiDocument> {
  const text = await response.text();
  return text ? JSON.parse(text) as JsonApiDocument : { data: [] };
}

async function requestJson(
  fetchImpl: FetchLike,
  url: string,
  logger: LoggerLike,
): Promise<{ json: JsonApiDocument }> {
  const response = await fetchImpl(url, {
    headers: {
      Accept: "application/vnd.api+json",
    },
  });
  const json = await parseResponseBody(response);

  if (!response.ok) {
    logger.error?.("Search-enabled JSON:API request failed", {
      status: response.status,
      url,
    });
    throw errorForResponse(response, json);
  }

  return { json };
}

export function createSearchEnabledDataProvider({
  apiRoot,
  baseProvider,
  fetch: fetchImpl,
  logger = console,
  rawYaml,
  schema,
}: {
  apiRoot: string;
  baseProvider: DataProvider;
  fetch?: FetchLike;
  logger?: LoggerLike;
  rawYaml: RawAdminYaml;
  schema: Schema;
}): DataProvider {
  const resolvedFetch = fetchImpl
    ? (input: RequestInfo | URL, init?: RequestInit) => fetchImpl(input, init)
    : globalThis.fetch.bind(globalThis);
  const normalizedApiRoot = `${trimTrailingSlashes(apiRoot)}/`;

  return {
    ...baseProvider,

    async getList(resource, params: ListParams = {}) {
      const schemaResourceKey = resolveSchemaResourceKey(schema, resource);
      const searchValue = params.filter?.q;
      if (typeof searchValue !== "string" || !searchValue.trim()) {
        return baseProvider.getList(schemaResourceKey, omitSearchFilter(params.filter) === params.filter
          ? params
          : {
              ...params,
              filter: omitSearchFilter(params.filter),
            });
      }

      const searchCols = resolveSearchColumns(schema, rawYaml, resource);
      if (searchCols.length === 0) {
        return baseProvider.getList(schemaResourceKey, {
          ...params,
          filter: omitSearchFilter(params.filter),
        });
      }

      const query = buildListQuery(
        schemaResourceKey,
        {
          ...params,
          filter: omitSearchFilter(params.filter),
        },
      );

      query.filter = mergeSearchWithExistingFilters(
        query,
        buildJsonApiSearchFilter(searchValue.trim(), searchCols),
      );

      const resourceEndpoint = resolveResourceEndpoint(schema, rawYaml, resource);
      const url = appendQuery(resolveEndpointUrl(normalizedApiRoot, resourceEndpoint), query);
      const { json } = await requestJson(resolvedFetch, url, logger);

      const normalized = normalizeDocument(json);

      return {
        data: normalized.records.map((record) => synthesizeCompositeKeys(record)),
        total: getTotal(json, normalized.records.length),
      };
    },

    async getOne(resource, params) {
      return baseProvider.getOne(resolveSchemaResourceKey(schema, resource), params);
    },

    async getMany(resource, params) {
      return baseProvider.getMany(resolveSchemaResourceKey(schema, resource), params);
    },

    async getManyReference(resource, params) {
      return baseProvider.getManyReference(
        resolveSchemaResourceKey(schema, resource),
        params,
      );
    },

    async create(resource, params) {
      return baseProvider.create(resolveSchemaResourceKey(schema, resource), params);
    },

    async update(resource, params) {
      return baseProvider.update(resolveSchemaResourceKey(schema, resource), params);
    },

    async updateMany(resource, params) {
      return baseProvider.updateMany(
        resolveSchemaResourceKey(schema, resource),
        params,
      );
    },

    async delete(resource, params) {
      return baseProvider.delete(resolveSchemaResourceKey(schema, resource), params);
    },

    async deleteMany(resource, params) {
      return baseProvider.deleteMany(
        resolveSchemaResourceKey(schema, resource),
        params,
      );
    },
  };
}
```

Notes:

- `buildJsonApiSearchFilter` and `mergeSearchWithExistingFilters` are exported
  so the starter frontend can keep the search/filter composition contract under
  unit test.
- Resource-type names such as `Collection` must be translated to schema
  resource keys such as `collections` before calling the base provider or the
  low-level normalizer.
- This template intentionally avoids `safrs-jsonapi-client`; keep SAFRS
  JSON:API search helpers in run-owned frontend code on the baseline
  React-Admin stack recorded in `runtime-bom.md`.
- If the primary SAFRS adapter already owns search/filter merging for the run,
  fold this wrapper into that local adapter instead of reintroducing an
  external package dependency.
