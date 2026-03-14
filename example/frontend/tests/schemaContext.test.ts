import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";

describe("schemaContext admin.yaml adapter", () => {
  it("converts object-shaped resource attributes into the client schema format", () => {
    const adapted = adaptAdminYamlForClient({
      resources: {
        Gallery: {
          endpoint: "/api/galleries",
          user_key: "code",
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
        ).resources.galleries.attributes,
      ),
    ).toBe(true);
    expect(schema.resourceByType.Gallery).toBe("galleries");
    expect(
      schema.resources.galleries.attributeConfigs.map((attribute) => attribute.name),
    ).toEqual(["code", "name"]);
    expect(schema.resources.galleries.searchCols).toEqual([
      { name: "code" },
      { name: "name" },
    ]);
    expect(schema.resources.galleries.userKey).toBe("code");
  });
});
