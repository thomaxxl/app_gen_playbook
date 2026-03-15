import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";

describe("schemaContext admin.yaml adapter", () => {
  it("converts object-shaped resource attributes into the client schema format", () => {
    const adapted = adaptAdminYamlForClient({
      resources: {
        Service: {
          endpoint: "/api/services",
          user_key: "code",
          tab_groups: {
            related: {
              label: "Related Items",
              relationships: ["items"],
            },
          },
          attributes: {
            code: {
              required: true,
              search: true,
              type: "text",
            },
            name: {
              search: true,
              type: "text",
            },
          },
        },
      },
    });

    const schema = normalizeAdminYaml(adapted);

    expect(
      Array.isArray(
        (
          adapted as {
            resources: Record<string, { attributes: unknown[] }>;
          }
        ).resources.services.attributes,
      ),
    ).toBe(true);
    expect(schema.resourceByType.Service).toBe("services");
    expect(
      schema.resources.services.attributeConfigs.map((attribute) => attribute.name),
    ).toEqual(["code", "name"]);
    expect(schema.resources.services.searchCols).toEqual([
      { name: "code" },
      { name: "name" },
    ]);
    expect(schema.resources.services.userKey).toBe("code");
    expect(
      (
        adapted as {
          resources: Record<
            string,
            { tab_groups: Array<{ label?: string; name: string; relationships: string[] }> }
          >;
        }
      ).resources.services.tab_groups,
    ).toEqual([
      {
        name: "related",
        label: "Related Items",
        relationships: ["items"],
      },
    ]);
  });
});
