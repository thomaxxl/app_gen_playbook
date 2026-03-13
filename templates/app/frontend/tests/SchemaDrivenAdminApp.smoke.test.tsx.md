# `frontend/tests/SchemaDrivenAdminApp.smoke.test.tsx`

See also:

- [../../../../specs/contracts/frontend/validation.md](../../../../specs/contracts/frontend/validation.md)
- [../SchemaDrivenAdminApp.tsx.md](../SchemaDrivenAdminApp.tsx.md)

Use a lightweight smoke test to prove bootstrap success, bootstrap failure,
and render-time resource-metadata failure all produce visible UI states.

```tsx
import type { ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import type { DataProvider } from "react-admin";
import type { Schema } from "safrs-jsonapi-client";
import { describe, expect, it, vi } from "vitest";

import { SchemaDrivenAdminApp } from "../src/shared-runtime/SchemaDrivenAdminApp";

const loadAdminBootstrap = vi.fn();
const buildResources = vi.fn(() => <div>resources-ready</div>);

vi.mock("react-admin", () => ({
  Admin: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("../src/shared-runtime/resourceRegistry", () => ({
  buildResources,
}));

vi.mock("../src/shared-runtime/admin/schemaContext", async () => {
  const actual = await vi.importActual<
    typeof import("../src/shared-runtime/admin/schemaContext")
  >("../src/shared-runtime/admin/schemaContext");

  return {
    ...actual,
    loadAdminBootstrap,
  };
});

const appConfig = {
  adminYamlUrl: "/ui/admin/admin.yaml",
  apiRoot: "/api",
  title: "Starter App",
};

const bootstrapPayload = {
  dataProvider: {
    getList: vi.fn(),
  } as unknown as DataProvider,
  rawYaml: { resources: {} },
  schema: { resources: {}, delimiter: ":" } as Schema,
};

describe("SchemaDrivenAdminApp", () => {
  it("shows the bootstrap error screen on admin.yaml/provider failure", async () => {
    loadAdminBootstrap.mockRejectedValueOnce(new Error("boom"));

    render(<SchemaDrivenAdminApp appConfig={appConfig} resourcePages={[]} />);

    expect(screen.getByText(/loading `admin\.yaml`/i)).toBeTruthy();
    await screen.findByText(/failed to initialize the schema or data provider/i);
    expect(screen.getByText("/ui/admin/admin.yaml")).toBeTruthy();
  });

  it("renders admin resources after bootstrap succeeds", async () => {
    loadAdminBootstrap.mockResolvedValueOnce(bootstrapPayload);

    render(
      <SchemaDrivenAdminApp
        appConfig={appConfig}
        resourcePages={[
          {
            name: "Collection",
            list: () => null,
            create: () => null,
            edit: () => null,
            show: () => null,
          },
        ]}
      />,
    );

    await waitFor(() => {
      expect(buildResources).toHaveBeenCalled();
      expect(screen.getByText("resources-ready")).toBeTruthy();
    });
  });

  it("shows the render boundary screen when resource registration throws", async () => {
    loadAdminBootstrap.mockResolvedValueOnce(bootstrapPayload);
    buildResources.mockImplementationOnce(() => {
      throw new Error("Unknown resource 'Ghost'.");
    });

    render(
      <SchemaDrivenAdminApp
        appConfig={appConfig}
        resourcePages={[
          {
            name: "Ghost",
            list: () => null,
            create: () => null,
            edit: () => null,
            show: () => null,
          },
        ]}
      />,
    );

    await screen.findByText(/failed to render resource metadata/i);
    expect(screen.getByText(/unknown resource 'ghost'/i)).toBeTruthy();
  });
});
```

Notes:

- Keep this test focused on the starter bootstrap contract.
- Do not turn it into an end-to-end CRUD test. Browser-level flows belong in a
  different validation layer.
