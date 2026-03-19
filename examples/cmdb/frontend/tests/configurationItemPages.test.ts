import { describe, expect, it } from "vitest";

import { ConfigurationItemPages } from "../src/generated/resources/ConfigurationItem";
import { OperationalStatusPages } from "../src/generated/resources/OperationalStatus";
import { ServicePages } from "../src/generated/resources/Service";

describe("generated CMDB resource pages", () => {
  it("exports the expected resource names", () => {
    expect(ServicePages.name).toBe("Service");
    expect(ConfigurationItemPages.name).toBe("ConfigurationItem");
    expect(OperationalStatusPages.name).toBe("OperationalStatus");
  });
});
