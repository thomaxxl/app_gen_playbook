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
    expect(resourceMeta.relationshipByName).toEqual({});
  });

  it("resolves search columns by React-Admin resource name", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    expect(resolveSearchColumns(schema, rawYaml, "FlightStatus")).toEqual([
      { name: "code" },
      { name: "label" },
    ]);
  });

  it("resolves sparse tab_groups relationships into canonical parent-route metadata", () => {
    const sparseYaml = {
      resources: {
        Device: {
          endpoint: "/api/devices",
          label: "Devices",
          user_key: "name",
          tab_groups: {
            related: {
              label: "Related",
              relationships: ["session_events", "alerts"],
            },
          },
          attributes: {
            name: { type: "text" },
          },
        },
        SessionEvent: {
          endpoint: "/api/session_events",
          label: "Session Events",
          user_key: "name",
          attributes: {
            name: { type: "text" },
            device_id: {
              type: "reference",
              reference: "Device",
            },
          },
        },
        Alert: {
          endpoint: "/api/alerts",
          label: "Alerts",
          user_key: "message",
          attributes: {
            message: { type: "text" },
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
    const sessionEventMeta = buildResourceMeta(sparseSchema, sparseYaml, "SessionEvent");

    expect(deviceMeta.name).toBe("Device");
    expect(deviceMeta.endpoint).toBe("/api/devices");
    expect(deviceMeta.relationships.map((relationship) => relationship.name).slice(0, 2)).toEqual([
      "session_events",
      "alerts",
    ]);
    expect(deviceMeta.relationshipByName.session_events.direction).toBe("tomany");
    expect(deviceMeta.relationshipByName.session_events.targetResource).toBe("SessionEvent");
    expect(deviceMeta.relationshipByName.session_events.fks).toContain("device_id");
    expect(deviceMeta.relationshipByName.session_events.includePath).toBe("session_events");
    expect(deviceMeta.relationshipByName.session_events.relationshipRouteTemplate).toBe(
      "/api/devices/{id}/session_events",
    );
    expect(deviceMeta.relationshipByName.session_events.resolutionStatus).toBe("resolved");
    expect(deviceMeta.relationshipByName.alerts.targetResource).toBe("Alert");
    expect(sessionEventMeta.relationshipByName.device.direction).toBe("toone");
    expect(sessionEventMeta.attributes.find((attribute) => attribute.name === "device_id")?.relationship?.name).toBe(
      "device",
    );
  });
});
```

Notes:

- At minimum, the generated runtime MUST prove one sparse relationship example
  where `tab_groups` plus fallback inference still produce a usable
  relationship metadata entry with stable `includePath`,
  `relationshipRouteTemplate`, and ordered `tab_groups` relationships.
