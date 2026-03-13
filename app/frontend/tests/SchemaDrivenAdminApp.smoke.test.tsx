import type { ReactNode } from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import type { DataProvider } from "react-admin";
import type { Schema } from "safrs-jsonapi-client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SchemaDrivenAdminApp } from "../src/shared-runtime/SchemaDrivenAdminApp";

const { buildResources, loadAdminBootstrap } = vi.hoisted(() => ({
  buildResources: vi.fn(() => "resources-ready"),
  loadAdminBootstrap: vi.fn(),
}));

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
  title: "Chess Tournament Management Admin",
};

const bootstrapPayload = {
  dataProvider: {
    getList: vi.fn(),
  } as unknown as DataProvider,
  rawYaml: { resources: {} },
  schema: { resources: {}, delimiter: ":" } as Schema,
};

beforeEach(() => {
  buildResources.mockReset();
  buildResources.mockImplementation(() => "resources-ready");
  loadAdminBootstrap.mockReset();
});

afterEach(() => {
  cleanup();
});

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
              name: "Tournament",
              list: () => <div />,
              create: () => <div />,
              edit: () => <div />,
            show: () => <div />,
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
    buildResources.mockImplementation(() => {
      throw new Error("Unknown resource 'Ghost'.");
    });

    render(
      <SchemaDrivenAdminApp
        appConfig={appConfig}
        resourcePages={[
          {
            name: "Ghost",
            list: () => <div />,
            create: () => <div />,
            edit: () => <div />,
            show: () => <div />,
          },
        ]}
      />,
    );

    await screen.findByText(/failed to render resource metadata/i);
    expect(screen.getByText(/unknown resource 'ghost'/i)).toBeTruthy();
  });
});
