import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";

describe("schemaContext admin.yaml adapter", () => {
  it("converts object-shaped resource attributes into the client schema format", () => {
    const adapted = adaptAdminYamlForClient({
      resources: {
        Tournament: {
          endpoint: "/api/tournaments",
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
        ).resources.tournaments.attributes,
      ),
    ).toBe(true);
    expect(schema.resourceByType.Tournament).toBe("tournaments");
    expect(
      schema.resources.tournaments.attributeConfigs.map((attribute) => attribute.name),
    ).toEqual(["code", "name"]);
    expect(schema.resources.tournaments.searchCols).toEqual([
      { name: "code" },
      { name: "name" },
    ]);
    expect(schema.resources.tournaments.userKey).toBe("code");
  });
});
