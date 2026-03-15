# `frontend/src/shared-runtime/admin/createSafrsJsonApiDataProvider.js`

See also:

- [../../../../../runs/current/artifacts/architecture/runtime-bom.md](../../../../../runs/current/artifacts/architecture/runtime-bom.md)
- [../../../../../specs/contracts/frontend/dependencies.md](../../../../../specs/contracts/frontend/dependencies.md)

```javascript
const JSON_API_CONTENT_TYPE = "application/vnd.api+json";

function trimTrailingSlashes(value) {
  return value.replace(/\/+$/, "");
}

function trimLeadingSlashes(value) {
  return value.replace(/^\/+/, "");
}

function isAbsoluteUrl(value) {
  return /^https?:\/\//i.test(value);
}

function clonePlainObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? { ...value } : {};
}

function normalizeSearchField(field) {
  if (typeof field === "string" && field.trim()) {
    return {
      name: field.trim(),
      op: "ilike",
      template: "%{q}%",
    };
  }

  if (!field || typeof field !== "object" || typeof field.name !== "string" || !field.name.trim()) {
    return null;
  }

  return {
    name: field.name.trim(),
    op: typeof field.op === "string" && field.op.trim() ? field.op.trim() : "ilike",
    template: typeof field.template === "string" && field.template ? field.template : "%{q}%",
  };
}

function applySearchTemplate(template, value) {
  if (!template) {
    return value;
  }

  if (template.includes("{q}")) {
    return template.split("{q}").join(value);
  }

  if (template.includes("{}")) {
    return template.split("{}").join(value);
  }

  if (template.includes("%s")) {
    return template.split("%s").join(value);
  }

  return template;
}

function buildSearchFilter(searchValue, searchFields) {
  const normalizedFields = searchFields.map(normalizeSearchField).filter(Boolean);
  if (!searchValue || normalizedFields.length === 0) {
    return null;
  }

  return {
    or: normalizedFields.map((field) => ({
      name: field.name,
      op: field.op,
      val: applySearchTemplate(field.template, searchValue),
    })),
  };
}

function buildScalarFilterClauses(filter) {
  const clauses = [];

  for (const [name, value] of Object.entries(filter)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }

    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      clauses.push({
        name,
        op: "eq",
        val: value,
      });
    }
  }

  return clauses;
}

function combineClauses(clauses) {
  if (clauses.length === 0) {
    return null;
  }

  if (clauses.length === 1) {
    return clauses[0];
  }

  return { and: clauses };
}

export function buildListQueryParams(params = {}, resourceConfig = {}) {
  const query = new URLSearchParams();
  const pagination = params.pagination ?? {};
  const sort = params.sort ?? {};
  const filter = clonePlainObject(params.filter);
  const rawJsonApiFilter = filter.__jsonapi;
  delete filter.__jsonapi;

  if (typeof pagination.page === "number") {
    query.set("page[number]", String(pagination.page));
  }

  if (typeof pagination.perPage === "number") {
    query.set("page[size]", String(pagination.perPage));
  }

  if (typeof sort.field === "string" && sort.field) {
    const prefix = String(sort.order).toUpperCase() === "DESC" ? "-" : "";
    query.set("sort", `${prefix}${sort.field}`);
  }

  const include = params.meta?.include ?? resourceConfig.include;
  if (Array.isArray(include) && include.length > 0) {
    query.set("include", include.join(","));
  } else if (typeof include === "string" && include.trim()) {
    query.set("include", include.trim());
  }

  const searchValue = typeof filter.q === "string" ? filter.q.trim() : "";
  delete filter.q;
  const scalarClauses = buildScalarFilterClauses(filter);
  const searchClause = buildSearchFilter(searchValue, resourceConfig.searchFields ?? []);
  const jsonFilter = combineClauses(
    [
      rawJsonApiFilter && typeof rawJsonApiFilter === "object" ? rawJsonApiFilter : null,
      ...scalarClauses,
      searchClause,
    ].filter(Boolean),
  );

  if (jsonFilter) {
    query.set("filter", JSON.stringify(jsonFilter));
    return query;
  }

  for (const clause of scalarClauses) {
    query.set(`filter[${clause.name}]`, String(clause.val));
  }

  return query;
}

function appendQuery(url, query) {
  const queryString = query.toString();
  return queryString ? `${url}?${queryString}` : url;
}

function resourceConfigFor(resource, resourceMap) {
  return resourceMap[resource] ?? {};
}

function resourceTypeFor(resource, resourceConfig) {
  return resourceConfig.type ?? resource;
}

function resourceUrlFor(resource, apiRoot, resourceMap) {
  const resourceConfig = resourceConfigFor(resource, resourceMap);
  const endpoint = resourceConfig.endpoint ?? resource;
  const normalizedApiRoot = trimTrailingSlashes(apiRoot);

  if (typeof endpoint !== "string" || !endpoint) {
    return normalizedApiRoot;
  }

  if (isAbsoluteUrl(endpoint)) {
    return endpoint;
  }

  if (endpoint.startsWith("/")) {
    return endpoint;
  }

  return `${normalizedApiRoot}/${trimLeadingSlashes(endpoint)}`;
}

function resourceItemUrlFor(resource, id, apiRoot, resourceMap) {
  return `${resourceUrlFor(resource, apiRoot, resourceMap)}/${encodeURIComponent(String(id))}`;
}

function includedIndexFor(document) {
  const index = new Map();

  for (const item of Array.isArray(document?.included) ? document.included : []) {
    if (!item || typeof item !== "object" || item.id === undefined || item.type === undefined) {
      continue;
    }
    index.set(`${item.type}:${item.id}`, item);
  }

  return index;
}

function normalizeRelationshipValue(value, index, visited) {
  if (!value) {
    return null;
  }

  if (Array.isArray(value)) {
    const ids = value.map((item) => item.id);
    const records = value
      .map((item) => normalizeIncludedRecord(item, index, visited))
      .filter(Boolean);

    return {
      ids,
      records,
    };
  }

  return {
    id: value.id ?? null,
    record: normalizeIncludedRecord(value, index, visited),
  };
}

function normalizeIncludedRecord(linkage, index, visited) {
  const key = linkage && linkage.type !== undefined && linkage.id !== undefined
    ? `${linkage.type}:${linkage.id}`
    : null;

  if (!key || visited.has(key)) {
    return null;
  }

  const included = index.get(key);
  if (!included) {
    return null;
  }

  return normalizeResourceObject(included, index, new Set([...visited, key]));
}

function normalizeResourceObject(resourceObject, index, visited = new Set()) {
  if (!resourceObject || typeof resourceObject !== "object") {
    return null;
  }

  const record = {
    id: resourceObject.id,
    ...(resourceObject.attributes ?? {}),
  };

  if (resourceObject.type !== undefined) {
    record.__type = resourceObject.type;
  }

  const relationships = resourceObject.relationships ?? {};
  if (Object.keys(relationships).length === 0) {
    return record;
  }

  record.__relationships = {};
  record.__included = {};

  for (const [name, descriptor] of Object.entries(relationships)) {
    const normalized = normalizeRelationshipValue(descriptor?.data, index, visited);
    if (!normalized) {
      record.__relationships[name] = null;
      continue;
    }

    if (Array.isArray(normalized.ids)) {
      record.__relationships[name] = normalized.ids;
      if (normalized.records.length > 0) {
        record.__included[name] = normalized.records;
      }
      continue;
    }

    record.__relationships[name] = normalized.id;
    if (normalized.record) {
      record.__included[name] = normalized.record;
    }
  }

  if (Object.keys(record.__included).length === 0) {
    delete record.__included;
  }

  return record;
}

export function normalizeJsonApiDocument(document) {
  const index = includedIndexFor(document);
  const primaryData = document?.data;

  if (Array.isArray(primaryData)) {
    return primaryData.map((item) => normalizeResourceObject(item, index)).filter(Boolean);
  }

  const record = normalizeResourceObject(primaryData, index);
  return record ? [record] : [];
}

function extractTotal(document, fallback) {
  const candidates = [
    document?.meta?.count,
    document?.meta?.total,
    document?.meta?.pagination?.total,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "number" && Number.isFinite(candidate)) {
      return candidate;
    }
  }

  return fallback;
}

function errorForResponse(response, payload) {
  const errors = Array.isArray(payload?.errors) ? payload.errors : [];
  const detail = errors.find((item) => typeof item?.detail === "string")?.detail;
  const title = errors.find((item) => typeof item?.title === "string")?.title;
  const message = detail || title || response.statusText || `Request failed with status ${response.status}`;
  const error = new Error(message);
  error.status = response.status;
  error.payload = payload;
  return error;
}

async function parseResponseBody(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }

  return JSON.parse(text);
}

async function requestJson(fetchImpl, url, init = {}) {
  const headers = new Headers(init.headers ?? {});
  headers.set("Accept", JSON_API_CONTENT_TYPE);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", JSON_API_CONTENT_TYPE);
  }

  const response = await fetchImpl(url, {
    ...init,
    headers,
  });
  const payload = await parseResponseBody(response);

  if (!response.ok) {
    throw errorForResponse(response, payload);
  }

  return payload;
}

function asRelationshipData(value, relationshipType, toMany) {
  if (value === null || value === undefined) {
    return toMany ? [] : null;
  }

  if (toMany) {
    if (!Array.isArray(value)) {
      return [];
    }

    return value
      .map((item) => {
        if (!item || item.id === undefined) {
          return null;
        }

        return {
          type: item.type ?? relationshipType,
          id: String(item.id),
        };
      })
      .filter(Boolean);
  }

  if (typeof value !== "object" || value.id === undefined) {
    return null;
  }

  return {
    type: value.type ?? relationshipType,
    id: String(value.id),
  };
}

function resourcePayloadFor(resource, data, resourceMap) {
  const resourceConfig = resourceConfigFor(resource, resourceMap);
  const type = resourceTypeFor(resource, resourceConfig);
  const attributes = {};
  const relationships = {};
  const relationshipFields = resourceConfig.relationshipFields ?? {};

  for (const [name, value] of Object.entries(data ?? {})) {
    if (name === "id" || name.startsWith("__")) {
      continue;
    }

    const relationshipField = relationshipFields[name];
    if (relationshipField) {
      relationships[name] = {
        data: asRelationshipData(value, relationshipField.type, Boolean(relationshipField.toMany)),
      };
      continue;
    }

    attributes[name] = value;
  }

  const payload = {
    data: {
      type,
    },
  };

  if (data?.id !== undefined && data?.id !== null) {
    payload.data.id = String(data.id);
  }

  if (Object.keys(attributes).length > 0) {
    payload.data.attributes = attributes;
  }

  if (Object.keys(relationships).length > 0) {
    payload.data.relationships = relationships;
  }

  return payload;
}

function normalizeSingleResult(document, fallback) {
  const records = normalizeJsonApiDocument(document);
  return records[0] ?? fallback;
}

export function createSafrsJsonApiDataProvider({
  apiRoot,
  fetch: fetchImpl = globalThis.fetch.bind(globalThis),
  resourceMap = {},
} = {}) {
  if (typeof apiRoot !== "string" || !apiRoot.trim()) {
    throw new Error("createSafrsJsonApiDataProvider requires a non-empty apiRoot");
  }

  if (typeof fetchImpl !== "function") {
    throw new Error("createSafrsJsonApiDataProvider requires a fetch implementation");
  }

  return {
    async getList(resource, params = {}) {
      const resourceConfig = resourceConfigFor(resource, resourceMap);
      const query = buildListQueryParams(params, resourceConfig);
      const url = appendQuery(resourceUrlFor(resource, apiRoot, resourceMap), query);
      const payload = await requestJson(fetchImpl, url);
      const data = normalizeJsonApiDocument(payload);

      return {
        data,
        total: extractTotal(payload, data.length),
      };
    },

    async getOne(resource, params) {
      const url = resourceItemUrlFor(resource, params.id, apiRoot, resourceMap);
      const payload = await requestJson(fetchImpl, url);

      return {
        data: normalizeSingleResult(payload, { id: params.id }),
      };
    },

    async getMany(resource, params) {
      const ids = Array.isArray(params?.ids) ? params.ids : [];
      const results = await Promise.all(ids.map((id) => this.getOne(resource, { id })));

      return {
        data: results.map((result) => result.data),
      };
    },

    async getManyReference(resource, params = {}) {
      const mergedFilter = {
        ...(clonePlainObject(params.filter)),
        [params.target]: params.id,
      };

      return this.getList(resource, {
        ...params,
        filter: mergedFilter,
      });
    },

    async create(resource, params = {}) {
      const url = resourceUrlFor(resource, apiRoot, resourceMap);
      const payload = await requestJson(fetchImpl, url, {
        method: "POST",
        body: JSON.stringify(resourcePayloadFor(resource, params.data, resourceMap)),
      });

      return {
        data: normalizeSingleResult(payload, params.data ?? {}),
      };
    },

    async update(resource, params = {}) {
      const url = resourceItemUrlFor(resource, params.id, apiRoot, resourceMap);
      const payload = await requestJson(fetchImpl, url, {
        method: "PATCH",
        body: JSON.stringify(resourcePayloadFor(resource, params.data, resourceMap)),
      });

      return {
        data: normalizeSingleResult(payload, params.data ?? { id: params.id }),
      };
    },

    async updateMany(resource, params = {}) {
      const ids = Array.isArray(params.ids) ? params.ids : [];
      await Promise.all(ids.map((id) => this.update(resource, {
        ...params,
        id,
        data: {
          ...(params.data ?? {}),
          id,
        },
      })));

      return {
        data: ids,
      };
    },

    async delete(resource, params = {}) {
      const url = resourceItemUrlFor(resource, params.id, apiRoot, resourceMap);
      const payload = await requestJson(fetchImpl, url, {
        method: "DELETE",
      });

      return {
        data: normalizeSingleResult(payload, params.previousData ?? { id: params.id }),
      };
    },

    async deleteMany(resource, params = {}) {
      const ids = Array.isArray(params.ids) ? params.ids : [];
      await Promise.all(ids.map((id) => this.delete(resource, {
        ...params,
        id,
      })));

      return {
        data: ids,
      };
    },
  };
}
```
