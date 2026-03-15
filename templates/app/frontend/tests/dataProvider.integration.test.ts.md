# `frontend/tests/dataProvider.integration.test.ts`

See also:

- [../../../../specs/contracts/frontend/validation.md](../../../../specs/contracts/frontend/validation.md)
- [../shared-runtime/admin/schemaContext.tsx.md](../shared-runtime/admin/schemaContext.tsx.md)

Use this test to keep the real bootstrap path executable:

- load raw `admin.yaml`
- normalize it through `adaptAdminYamlForClient(...)`
- build the real data provider
- fetch one representative list payload
- prove that representative scalar fields survive into row records

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { loadAdminBootstrap } from "../src/shared-runtime/admin/schemaContext";

const rawAdminYaml = `
resources:
  Collection:
    endpoint: /api/collections
    label: Collection
    user_key: name
    attributes:
      name:
        type: text
        search: true
        required: true
`;

function responseFor(input: unknown): Response {
  return new Response(JSON.stringify(input), {
    status: 200,
    headers: {
      "Content-Type": "application/vnd.api+json",
    },
  });
}

function requestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.toString();
  }
  return input.url;
}

describe("loadAdminBootstrap data-provider integration", () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = requestUrl(input);

    if (url === "/ui/admin/admin.yaml") {
      return new Response(rawAdminYaml, {
        status: 200,
        headers: {
          "Content-Type": "text/yaml",
        },
      });
    }

    if (url.includes("/api/collections")) {
      return responseFor({
        data: [
          {
            id: "1",
            type: "Collection",
            attributes: {
              name: "Spring Planning",
            },
            relationships: {},
          },
        ],
        meta: {
          count: 1,
        },
      });
    }

    throw new Error(`Unexpected fetch: ${url}`);
  });

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("preserves scalar fields through the admin.yaml to data-provider row path", async () => {
    const { dataProvider, schema } = await loadAdminBootstrap({
      adminYamlUrl: "/ui/admin/admin.yaml",
      apiRoot: "/api",
      title: "Starter App",
    });

    expect(schema.resourceByType.Collection).toBe("collections");

    const result = await dataProvider.getList("Collection", {
      pagination: { page: 1, perPage: 10 },
      sort: { field: "id", order: "ASC" },
      filter: {},
    });

    expect(result.data).toHaveLength(1);
    expect(result.data[0]).toMatchObject({
      id: "1",
      name: "Spring Planning",
    });
  });
});
```

Notes:

- For a non-starter run, replace the starter resource name and representative
  scalar field with the values declared in:
  - `../../../../runs/current/artifacts/architecture/resource-naming.md`
  - `../../../../runs/current/artifacts/product/sample-data.md`
- This test is intentionally narrower than a browser smoke suite. Its purpose
  is to prove that the schema/data-provider path preserves row data before the
  UI layer renders it.
