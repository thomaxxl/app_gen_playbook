import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";
import {
  buildResourceMeta,
  resolveSearchColumns,
} from "../src/shared-runtime/admin/resourceMetadata";

const rawYaml = {
  resources: {
    Gallery: {
      endpoint: "/api/galleries",
      label: "Galleries",
      user_key: "code",
      attributes: {
        code: {
          label: "Gallery Code",
          required: true,
          search: true,
          type: "text",
        },
        name: {
          label: "Name",
          search: true,
          type: "text",
        },
      },
    },
    ShareStatus: {
      endpoint: "/api/share_statuses",
      label: "Share Statuses",
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

    const resourceMeta = buildResourceMeta(schema, rawYaml, "Gallery");

    expect(resourceMeta.name).toBe("Gallery");
    expect(resourceMeta.endpoint).toBe("/api/galleries");
    expect(resourceMeta.userKey).toBe("code");
    expect(resourceMeta.attributes.map((attribute) => attribute.name)).toEqual([
      "code",
      "name",
    ]);
  });

  it("resolves search columns by resource type", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    expect(resolveSearchColumns(schema, rawYaml, "Gallery")).toEqual([
      { name: "code" },
      { name: "name" },
    ]);
  });

  it("resolves multi-word resources through resourceByType", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    const resourceMeta = buildResourceMeta(schema, rawYaml, "ShareStatus");

    expect(resourceMeta.name).toBe("ShareStatus");
    expect(resourceMeta.endpoint).toBe("/api/share_statuses");
    expect(resolveSearchColumns(schema, rawYaml, "ShareStatus")).toEqual([
      { name: "code" },
      { name: "label" },
    ]);
  });
});
