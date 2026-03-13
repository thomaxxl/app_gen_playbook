# `frontend/tests/resourceMetadata.test.ts`

See also:

- [../../../../specs/contracts/frontend/runtime-contract.md](../../../../specs/contracts/frontend/runtime-contract.md)
- [../shared-runtime/admin/resourceMetadata.ts.md](../shared-runtime/admin/resourceMetadata.ts.md)

This test proves that the runtime resolves metadata by React-Admin resource
name even when the normalized schema is keyed by collection-path names such as
`flight_statuses`.

```ts
import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";
import {
  buildResourceMeta,
  resolveSearchColumns,
} from "../src/shared-runtime/admin/resourceMetadata";

const rawYaml = {
  resources: {
    FlightStatus: {
      endpoint: "/api/flight_statuses",
      label: "Flight Statuses",
      user_key: "label",
      attributes: {
        code: {
          label: "Code",
          required: true,
          search: true,
          type: "text",
        },
        label: {
          label: "Label",
          required: true,
          search: true,
          type: "text",
        },
      },
    },
  },
};

describe("resourceMetadata", () => {
  it("resolves metadata by resource type when the schema is keyed by collection path", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    const resourceMeta = buildResourceMeta(schema, rawYaml, "FlightStatus");

    expect(resourceMeta.name).toBe("FlightStatus");
    expect(resourceMeta.endpoint).toBe("/api/flight_statuses");
    expect(resourceMeta.userKey).toBe("label");
    expect(resourceMeta.attributes.map((attribute) => attribute.name)).toEqual([
      "code",
      "label",
    ]);
  });

  it("resolves search columns by React-Admin resource name", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    expect(resolveSearchColumns(schema, rawYaml, "FlightStatus")).toEqual([
      { name: "code" },
      { name: "label" },
    ]);
  });
});
```
