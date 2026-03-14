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
      buildJsonApiSearchFilter("seattle", [
        { name: "title" },
        { name: "filename", op: "eq", val: "{q}" },
      ]),
    );

    expect(JSON.parse(merged)).toEqual({
      and: [
        { name: "status_id", op: "eq", val: 2 },
        {
          or: [
            { name: "title", op: "ilike", val: "%seattle%" },
            { name: "filename", op: "eq", val: "seattle" },
          ],
        },
      ],
    });
    expect(query).not.toHaveProperty("filter[status_id]");
  });

  it("keeps existing JSON filters and combines them with search", () => {
    const query: Record<string, string | number | boolean> = {
      filter: JSON.stringify({ name: "gallery_id", op: "eq", val: 7 }),
    };

    const merged = mergeSearchWithExistingFilters(
      query,
      buildJsonApiSearchFilter("poster", [{ name: "title" }]),
    );

    expect(JSON.parse(merged)).toEqual({
      and: [
        { name: "gallery_id", op: "eq", val: 7 },
        {
          or: [{ name: "title", op: "ilike", val: "%poster%" }],
        },
      ],
    });
  });
});
