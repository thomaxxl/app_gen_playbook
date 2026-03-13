# `frontend/src/shared-runtime/admin/createSearchEnabledDataProvider.ts`

See also:

- [../../../../../specs/contracts/backend/query-contract.md](../../../../../specs/contracts/backend/query-contract.md)
- [../../../../../specs/contracts/frontend/admin-yaml-contract.md](../../../../../specs/contracts/frontend/admin-yaml-contract.md)

```tsx
import {
  buildListQuery,
  createHttpClient,
  getTotal,
  normalizeDocument,
  queryToSearchParams,
  synthesizeCompositeKeys,
} from "safrs-jsonapi-client";
import type {
  CreateHttpClientOptions,
  DataProvider,
  JsonApiDocument,
  LoggerLike,
  Schema,
  SearchCol,
} from "safrs-jsonapi-client";

import type { RawAdminYaml } from "./resourceMetadata";
import { resolveResourceEndpoint, resolveSearchColumns } from "./resourceMetadata";

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
  fetch?: CreateHttpClientOptions["fetch"];
  logger?: LoggerLike;
  rawYaml: RawAdminYaml;
  schema: Schema;
}): DataProvider {
  const resolvedFetch = fetchImpl
    ? (input: RequestInfo | URL, init?: RequestInit) => fetchImpl(input, init)
    : globalThis.fetch.bind(globalThis);
  const http = createHttpClient({
    fetch: resolvedFetch,
    logger,
  });
  const normalizedApiRoot = `${trimTrailingSlashes(apiRoot)}/`;

  return {
    ...baseProvider,

    async getList(resource, params = {}) {
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
        schema,
        {
          defaultPerPage: params.pagination?.perPage,
          delimiter: schema.delimiter,
          logger,
        },
      );

      query.filter = mergeSearchWithExistingFilters(
        query,
        buildJsonApiSearchFilter(searchValue.trim(), searchCols),
      );

      const resourceEndpoint = resolveResourceEndpoint(schema, rawYaml, resource);
      const url = appendQuery(resolveEndpointUrl(normalizedApiRoot, resourceEndpoint), query);
      const { json } = await http.requestJson<JsonApiDocument>(url);

      const normalized = normalizeDocument(json, {
        delimiter: schema.delimiter,
        includeTomany: false,
        logger,
        resourceEndpoint: schemaResourceKey,
        schema,
      });

      return {
        data: normalized.records.map((record) =>
          synthesizeCompositeKeys(record, schemaResourceKey, schema, schema.delimiter),
        ),
        total: getTotal(json, { keys: ["count", "total"] }),
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
