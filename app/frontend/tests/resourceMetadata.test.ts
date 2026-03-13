import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";
import {
  buildResourceMeta,
  resolveSearchColumns,
} from "../src/shared-runtime/admin/resourceMetadata";

const rawYaml = {
  resources: {
    Tournament: {
      endpoint: "/api/tournaments",
      label: "Tournaments",
      user_key: "code",
      attributes: {
        code: {
          label: "Tournament Code",
          required: true,
          search: true,
          type: "text",
        },
        name: {
          label: "Tournament Name",
          search: true,
          type: "text",
        },
      },
    },
    PairingStatus: {
      endpoint: "/api/pairing_statuses",
      label: "Pairing Statuses",
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

    const resourceMeta = buildResourceMeta(schema, rawYaml, "Tournament");

    expect(resourceMeta.name).toBe("Tournament");
    expect(resourceMeta.endpoint).toBe("/api/tournaments");
    expect(resourceMeta.userKey).toBe("code");
    expect(resourceMeta.attributes.map((attribute) => attribute.name)).toEqual([
      "code",
      "name",
    ]);
  });

  it("resolves search columns by resource type", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    expect(resolveSearchColumns(schema, rawYaml, "Tournament")).toEqual([
      { name: "code" },
      { name: "name" },
    ]);
  });

  it("resolves multi-word resources through resourceByType", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    const resourceMeta = buildResourceMeta(schema, rawYaml, "PairingStatus");

    expect(resourceMeta.name).toBe("PairingStatus");
    expect(resourceMeta.endpoint).toBe("/api/pairing_statuses");
    expect(resolveSearchColumns(schema, rawYaml, "PairingStatus")).toEqual([
      { name: "code" },
      { name: "label" },
    ]);
  });
});
