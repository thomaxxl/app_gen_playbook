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

  it("documents the sparse-relationship fallback expectation", () => {
    const sparseYaml = {
      resources: {
        Device: {
          endpoint: "/api/devices",
          label: "Devices",
          user_key: "name",
          tab_groups: {
            related: {
              label: "Related",
              relationships: ["sessions"],
            },
          },
          attributes: {
            name: { type: "text" },
          },
        },
        Session: {
          endpoint: "/api/sessions",
          label: "Sessions",
          user_key: "name",
          attributes: {
            name: { type: "text" },
            device_id: {
              type: "reference",
              reference: "Device",
            },
          },
        },
      },
    };

    const sparseSchema = normalizeAdminYaml(adaptAdminYamlForClient(sparseYaml));
    const deviceMeta = buildResourceMeta(sparseSchema, sparseYaml, "Device");

    expect(deviceMeta.name).toBe("Device");
    expect(deviceMeta.endpoint).toBe("/api/devices");
    // Replace this placeholder with concrete relationship assertions in the
    // generated app. The runtime contract requires relationship synthesis
    // from raw tab_groups plus reference/fallback metadata when the
    // normalized relationship graph is incomplete.
    expect(deviceMeta.relationships).toBeDefined();
  });
});
```

Notes:

- Generated apps SHOULD replace the sparse fallback placeholder assertion above
  with concrete relationship expectations for the actual domain.
- At minimum, the generated runtime MUST prove one sparse relationship example
  where `tab_groups` plus fallback inference still produce a usable
  relationship metadata entry.
