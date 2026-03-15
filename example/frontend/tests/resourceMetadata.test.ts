import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";
import {
  buildResourceMeta,
  resolveSearchColumns,
} from "../src/shared-runtime/admin/resourceMetadata";

const rawYaml = {
  resources: {
    Service: {
      endpoint: "/api/services",
      label: "Services",
      user_key: "code",
      tab_groups: {
        related: {
          label: "Service Configuration Items",
          relationships: ["items"],
        },
      },
      attributes: {
        code: {
          label: "Service Code",
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
    ConfigurationItem: {
      endpoint: "/api/configuration_items",
      label: "Configuration Items",
      user_key: "hostname",
      tab_groups: {
        related: {
          label: "Related Records",
          relationships: ["service", "status"],
        },
      },
      attributes: {
        hostname: {
          label: "Hostname",
          required: true,
          search: true,
          type: "text",
        },
        service_id: {
          label: "Service",
          reference: "Service",
          required: true,
          type: "reference",
        },
        status_id: {
          label: "Operational Status",
          reference: "OperationalStatus",
          required: true,
          type: "reference",
        },
      },
    },
    OperationalStatus: {
      endpoint: "/api/operational_statuses",
      label: "Operational Statuses",
      user_key: "label",
      tab_groups: {
        related: {
          label: "Related Configuration Items",
          relationships: ["items"],
        },
      },
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

    const resourceMeta = buildResourceMeta(schema, rawYaml, "Service");

    expect(resourceMeta.name).toBe("Service");
    expect(resourceMeta.endpoint).toBe("/api/services");
    expect(resourceMeta.userKey).toBe("code");
    expect(resourceMeta.attributes.map((attribute) => attribute.name)).toEqual([
      "code",
      "name",
    ]);
  });

  it("resolves search columns by resource type", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    expect(resolveSearchColumns(schema, rawYaml, "Service")).toEqual([
      { name: "code" },
      { name: "name" },
    ]);
  });

  it("synthesizes toone relationships from foreign keys and tab groups", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    const itemMeta = buildResourceMeta(schema, rawYaml, "ConfigurationItem");

    expect(itemMeta.relationshipByName.service.targetResource).toBe("Service");
    expect(itemMeta.relationshipByName.service.direction).toBe("toone");
    expect(itemMeta.relationshipByName.service.fks).toEqual(["service_id"]);
    expect(itemMeta.relationshipByName.status.targetResource).toBe("OperationalStatus");
    expect(itemMeta.relationshipByName.status.direction).toBe("toone");
    expect(
      itemMeta.attributes.find((attribute) => attribute.name === "service_id")?.relationship?.name,
    ).toBe("service");
    expect(
      itemMeta.attributes.find((attribute) => attribute.name === "status_id")?.relationship?.name,
    ).toBe("status");
  });

  it("infers tomany relationships from tab groups and reverse foreign keys", () => {
    const schema = normalizeAdminYaml(adaptAdminYamlForClient(rawYaml));

    const serviceMeta = buildResourceMeta(schema, rawYaml, "Service");
    const statusMeta = buildResourceMeta(schema, rawYaml, "OperationalStatus");

    expect(serviceMeta.relationshipByName.items.direction).toBe("tomany");
    expect(serviceMeta.relationshipByName.items.targetResource).toBe("ConfigurationItem");
    expect(serviceMeta.relationshipByName.items.fks).toEqual(["service_id"]);
    expect(serviceMeta.relationships[0]?.label).toBe("Service Configuration Items");

    expect(statusMeta.relationshipByName.items.direction).toBe("tomany");
    expect(statusMeta.relationshipByName.items.targetResource).toBe("ConfigurationItem");
    expect(statusMeta.relationshipByName.items.fks).toEqual(["status_id"]);
    expect(statusMeta.relationships[0]?.label).toBe("Related Configuration Items");
  });
});
