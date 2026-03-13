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
      buildJsonApiSearchFilter("round 1", [
        { name: "pairing_code" },
        { name: "result_summary", op: "eq", val: "{q}" },
      ]),
    );

    expect(JSON.parse(merged)).toEqual({
      and: [
        { name: "status_id", op: "eq", val: 2 },
        {
          or: [
            { name: "pairing_code", op: "ilike", val: "%round 1%" },
            { name: "result_summary", op: "eq", val: "round 1" },
          ],
        },
      ],
    });
    expect(query).not.toHaveProperty("filter[status_id]");
  });

  it("keeps existing JSON filters and combines them with search", () => {
    const query: Record<string, string | number | boolean> = {
      filter: JSON.stringify({ name: "tournament_id", op: "eq", val: 7 }),
    };

    const merged = mergeSearchWithExistingFilters(
      query,
      buildJsonApiSearchFilter("sofia", [{ name: "full_name" }]),
    );

    expect(JSON.parse(merged)).toEqual({
      and: [
        { name: "tournament_id", op: "eq", val: 7 },
        {
          or: [{ name: "full_name", op: "ilike", val: "%sofia%" }],
        },
      ],
    });
  });
});
