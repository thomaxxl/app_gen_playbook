import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";
import {
  buildResourceMeta,
  resolveSearchColumns,
} from "../src/shared-runtime/admin/resourceMetadata";

const rawYaml = {
  resources: {
    Gate: {
      endpoint: "/api/gates",
      label: "Gates",
      user_key: "code",
      attributes: {
        code: {
          label: "Gate Code",
          required: true,
          search: true,
          type: "text",
        },
        terminal: {
          label: "Terminal",
          search: true,
          type: "text",
        },
      },
    },
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

    const resourceMeta = buildResourceMeta(schema, rawYaml, "Gate");

    expect(resourceMeta.name).toBe("Gate");
    expect(resourceMeta.endpoint).toBe("/api/gates");
    expect(resourceMeta.userKey).toBe("code");
    expect(resourceMeta.attributes.map((attribute) => attribute.name)).toEqual([
      "code",
      "terminal",
    ]);
  });

  it("resolves search columns by resource type", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    expect(resolveSearchColumns(schema, rawYaml, "Gate")).toEqual([
      { name: "code" },
      { name: "terminal" },
    ]);
  });

  it("resolves multi-word resources through resourceByType", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    const resourceMeta = buildResourceMeta(schema, rawYaml, "FlightStatus");

    expect(resourceMeta.name).toBe("FlightStatus");
    expect(resourceMeta.endpoint).toBe("/api/flight_statuses");
    expect(resolveSearchColumns(schema, rawYaml, "FlightStatus")).toEqual([
      { name: "code" },
      { name: "label" },
    ]);
  });
});
