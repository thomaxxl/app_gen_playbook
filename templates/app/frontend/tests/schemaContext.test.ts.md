# `frontend/tests/schemaContext.test.ts`

See also:

- [../../../../specs/contracts/frontend/runtime-contract.md](../../../../specs/contracts/frontend/runtime-contract.md)
- [../shared-runtime/admin/schemaContext.tsx.md](../shared-runtime/admin/schemaContext.tsx.md)

Use this test to keep the raw-`admin.yaml` adapter contract executable.

```tsx
import { describe, expect, it } from "vitest";
import { normalizeAdminYaml } from "safrs-jsonapi-client";

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";

describe("schemaContext admin.yaml adapter", () => {
  it("converts object-shaped resource attributes into the client schema format", () => {
    const adapted = adaptAdminYamlForClient({
      resources: {
        Collection: {
          endpoint: "/api/collections",
          user_key: "name",
          tab_groups: {
            related: {
              label: "Related",
              relationships: ["items"],
            },
          },
          attributes: {
            name: {
              required: true,
              search: true,
              type: "text",
            },
            status_id: {
              edit: false,
              type: "reference",
            },
          },
        },
      },
    });

    const schema = normalizeAdminYaml(adapted);

    expect(
      Array.isArray(
        (adapted as { resources: Record<string, { attributes: unknown[] }> }).resources.collections.attributes,
      ),
    ).toBe(true);
    expect(schema.resourceByType.Collection).toBe("collections");
    expect(schema.resources.collections.attributeConfigs.map((attribute) => attribute.name)).toEqual([
      "name",
      "status_id",
    ]);
    expect(schema.resources.collections.searchCols).toEqual([{ name: "name" }]);
    expect(schema.resources.collections.userKey).toBe("name");
    expect(
      (adapted as {
        resources: Record<string, { tab_groups: Array<{ relationships: string[] }> }>;
      }).resources.collections.tab_groups,
    ).toEqual([
      {
        relationships: ["items"],
        label: "Related",
        name: "related",
      },
    ]);
  });
});
```
