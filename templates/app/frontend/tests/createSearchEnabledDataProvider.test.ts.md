# `frontend/tests/createSearchEnabledDataProvider.test.ts`

See also:

- [../../../../specs/contracts/frontend/validation.md](../../../../specs/contracts/frontend/validation.md)
- [../shared-runtime/admin/createSearchEnabledDataProvider.ts.md](../shared-runtime/admin/createSearchEnabledDataProvider.ts.md)

Use a direct unit test for the grouped search-filter merge behavior.

```ts
import { describe, expect, it } from "vitest";

import {
  buildJsonApiSearchFilter,
  mergeSearchWithExistingFilters,
} from "../src/shared-runtime/admin/createSearchEnabledDataProvider";

describe("createSearchEnabledDataProvider helpers", () => {
  it("keeps existing scalar filters when q is added", () => {
    const query: Record<string, string | number | boolean> = {
      "filter[status_id]": 2,
    };

    const merged = mergeSearchWithExistingFilters(
      query,
      buildJsonApiSearchFilter("board", [
        { name: "title" },
        { name: "status_code", op: "eq", val: "{q}" },
      ]),
    );

    expect(JSON.parse(merged)).toEqual({
      and: [
        { name: "status_id", op: "eq", val: 2 },
        {
          or: [
            { name: "title", op: "ilike", val: "%board%" },
            { name: "status_code", op: "eq", val: "board" },
          ],
        },
      ],
    });
    expect(query).not.toHaveProperty("filter[status_id]");
  });

  it("keeps existing JSON filters and combines them with search", () => {
    const query: Record<string, string | number | boolean> = {
      filter: JSON.stringify({ name: "collection_id", op: "eq", val: 7 }),
    };

    const merged = mergeSearchWithExistingFilters(
      query,
      buildJsonApiSearchFilter("done", [{ name: "title" }]),
    );

    expect(JSON.parse(merged)).toEqual({
      and: [
        { name: "collection_id", op: "eq", val: 7 },
        {
          or: [{ name: "title", op: "ilike", val: "%done%" }],
        },
      ],
    });
  });
});
```
