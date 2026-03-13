import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";

describe("schemaContext admin.yaml adapter", () => {
  it("converts object-shaped resource attributes into the client schema format", () => {
    const adapted = adaptAdminYamlForClient({
      resources: {
        Gate: {
          endpoint: "/api/gates",
          user_key: "code",
          attributes: {
            code: {
              required: true,
              search: true,
              type: "text",
            },
            terminal: {
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
        ).resources.gates.attributes,
      ),
    ).toBe(true);
    expect(schema.resourceByType.Gate).toBe("gates");
    expect(
      schema.resources.gates.attributeConfigs.map((attribute) => attribute.name),
    ).toEqual(["code", "terminal"]);
    expect(schema.resources.gates.searchCols).toEqual([
      { name: "code" },
      { name: "terminal" },
    ]);
    expect(schema.resources.gates.userKey).toBe("code");
  });
});
