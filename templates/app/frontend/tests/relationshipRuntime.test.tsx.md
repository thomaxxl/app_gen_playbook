# `frontend/tests/relationshipRuntime.test.tsx`

See also:

- [../../../../specs/contracts/frontend/relationship-ui.md](../../../../specs/contracts/frontend/relationship-ui.md)
- [../../../../specs/contracts/frontend/validation.md](../../../../specs/contracts/frontend/validation.md)
- [../shared-runtime/relationshipUi.tsx.md](../shared-runtime/relationshipUi.tsx.md)
- [../shared-runtime/resourceRegistry.tsx.md](../shared-runtime/resourceRegistry.tsx.md)

Use a deterministic runtime test for the relationship lanes that a generic
live-app Playwright smoke cannot guarantee:

- unresolved relationship metadata must render a visible configuration error
- sparse `tab_groups` fallback must still synthesize a usable `tomany`
  relationship route and row-action surface

```tsx
import type { ReactNode } from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import type { Schema } from "safrs-jsonapi-client";
import { normalizeAdminYaml } from "safrs-jsonapi-client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mockState = vi.hoisted(() => ({
  dataProvider: {
    execute: vi.fn(),
    getOne: vi.fn(),
  },
  rawYaml: null as Record<string, unknown> | null,
  record: null as Record<string, unknown> | null,
  redirect: vi.fn(),
  schema: null as Record<string, unknown> | null,
}));

vi.mock("react-admin", async () => {
  const React = await import("react");
  const ListContext = React.createContext<{ data?: Record<string, unknown>[] } | null>(null);
  const RowRecordContext = React.createContext<Record<string, unknown> | null>(null);

  const useRecordContext = () => React.useContext(RowRecordContext) ?? mockState.record;

  const passthrough = ({ children }: { children?: ReactNode }) => <>{children}</>;

  const FunctionField = ({
    render,
  }: {
    render: (record: Record<string, unknown>) => ReactNode;
  }) => <>{render((useRecordContext() ?? {}) as Record<string, unknown>)}</>;

  const TextField = ({ source }: { source: string }) => {
    const record = useRecordContext() ?? {};
    return <span data-testid={`text-field:${source}`}>{String(record[source] ?? "")}</span>;
  };

  const Datagrid = ({
    children,
    rowClick,
  }: {
    children?: ReactNode;
    rowClick?: string;
  }) => {
    const list = React.useContext(ListContext) ?? { data: [] };
    return (
      <div data-row-click={rowClick} role="grid">
        {(list.data ?? []).map((record) => (
          <RowRecordContext.Provider key={String(record.id)} value={record}>
            <div data-testid={`grid-row:${String(record.id)}`}>
              {React.Children.map(children, (child) =>
                React.isValidElement(child)
                  ? React.cloneElement(child as React.ReactElement)
                  : child,
              )}
            </div>
          </RowRecordContext.Provider>
        ))}
      </div>
    );
  };

  const ActionButton = ({
    children,
    label,
    ...props
  }: {
    children?: ReactNode;
    label?: string;
    [key: string]: any;
  }) => (
    <button type="button" {...props}>
      {label ?? children}
    </button>
  );

  return {
    AutocompleteInput: passthrough,
    BooleanField: TextField,
    BooleanInput: passthrough,
    Create: passthrough,
    Datagrid,
    DateField: TextField,
    DateInput: passthrough,
    DeleteWithConfirmButton: ActionButton,
    Edit: passthrough,
    EditButton: ActionButton,
    FunctionField,
    List: passthrough,
    ListContextProvider: ({
      children,
      value,
    }: {
      children?: ReactNode;
      value: { data?: Record<string, unknown>[] };
    }) => <ListContext.Provider value={value}>{children}</ListContext.Provider>,
    Loading: () => <div>Loading...</div>,
    NumberField: TextField,
    NumberInput: passthrough,
    ReferenceInput: passthrough,
    Resource: passthrough,
    SearchInput: passthrough,
    Show: passthrough,
    SimpleForm: passthrough,
    TextField,
    TextInput: passthrough,
    useDataProvider: () => mockState.dataProvider,
    useList: (value: Record<string, unknown>) => value,
    useRecordContext,
    useRedirect: () => mockState.redirect,
  };
});

vi.mock("../src/shared-runtime/admin/schemaContext", async () => {
  const actual = await vi.importActual<
    typeof import("../src/shared-runtime/admin/schemaContext")
  >("../src/shared-runtime/admin/schemaContext");

  return {
    ...actual,
    useAdminSchema: () => mockState.schema,
    useRawAdminYaml: () => mockState.rawYaml,
  };
});

import { adaptAdminYamlForClient } from "../src/shared-runtime/admin/schemaContext";
import { buildResourceMeta, type ResourceRelationshipMeta } from "../src/shared-runtime/admin/resourceMetadata";
import { ManyRelationshipTab } from "../src/shared-runtime/resourceRegistry";
import { SingleRelationshipTab } from "../src/shared-runtime/relationshipUi";

const sparseYaml = {
  resources: {
    Device: {
      endpoint: "/api/devices",
      label: "Devices",
      user_key: "name",
      tab_groups: {
        related: {
          label: "Related",
          relationships: ["session_events", "alerts"],
        },
      },
      attributes: {
        name: { type: "text" },
      },
    },
    SessionEvent: {
      endpoint: "/api/session_events",
      label: "Session Events",
      user_key: "name",
      attributes: {
        name: { type: "text" },
        device_id: {
          type: "reference",
          reference: "Device",
        },
      },
    },
    Alert: {
      endpoint: "/api/alerts",
      label: "Alerts",
      user_key: "message",
      attributes: {
        device_id: {
          type: "reference",
          reference: "Device",
        },
        message: { type: "text" },
      },
    },
  },
};

describe("relationship runtime", () => {
  beforeEach(() => {
    mockState.dataProvider.execute.mockReset();
    mockState.dataProvider.getOne.mockReset();
    mockState.redirect.mockReset();
    mockState.rawYaml = sparseYaml;
    mockState.schema = normalizeAdminYaml(adaptAdminYamlForClient(sparseYaml));
    mockState.record = null;
  });

  afterEach(() => {
    cleanup();
  });

  it("shows a visible unresolved relationship error instead of a quiet empty state", async () => {
    mockState.record = { id: "device-1", name: "Router" };

    const unresolvedRelationship: ResourceRelationshipMeta = {
      attributes: ["ghost_id"],
      direction: "toone",
      fks: ["ghost_id"],
      includePath: "ghost",
      label: "Ghost",
      name: "ghost",
      parentEndpoint: "/api/devices",
      parentResource: "Device",
      relationshipRouteTemplate: "/api/devices/{id}/ghost",
      resolutionReason: "missing-target-resource",
      resolutionStatus: "unresolved",
      targetResource: "Ghost",
    };

    render(<SingleRelationshipTab relationship={unresolvedRelationship} />);

    const alert = await screen.findByTestId("relationship-resolution-error:toone:ghost");
    expect(screen.getByText("Relationship metadata incomplete")).toBeTruthy();
    expect(alert).toHaveAttribute("data-relationship-fetch-source", "unresolved");
    expect(screen.queryByText(/No related record/i)).toBeNull();
    expect(mockState.dataProvider.execute).not.toHaveBeenCalled();
    expect(mockState.dataProvider.getOne).not.toHaveBeenCalled();
  });

  it("loads sparse tab_groups tomany relationships through the canonical parent route and keeps row actions", async () => {
    const deviceMeta = buildResourceMeta(mockState.schema as unknown as Schema, sparseYaml, "Device");
    const relationship = deviceMeta.relationshipByName.session_events;
    mockState.record = { id: "device-1", name: "Router" };
    mockState.dataProvider.execute.mockResolvedValue({
      data: [
        {
          device_id: "device-1",
          id: "session-1",
          name: "Morning Sync",
        },
      ],
    });

    render(<ManyRelationshipTab parentResource="Device" relationship={relationship} />);

    await waitFor(() => {
      expect(mockState.dataProvider.execute).toHaveBeenCalledWith(
        "devices",
        expect.objectContaining({
          action: "session_events",
          id: "device-1",
          method: "GET",
        }),
      );
    });

    const panel = await screen.findByTestId("relationship-tab-panel:tomany:session_events");
    expect(panel).toHaveAttribute("data-relationship-fetch-source", "relationship-route");
    expect(panel).toHaveAttribute("data-relationship-route-path", "devices/device-1/session_events");
    expect(screen.getByTestId("relationship-row-actions:session_events:session-1")).toBeTruthy();
    expect(screen.getByTestId("relationship-row-action:edit:session_events:session-1")).toBeTruthy();
    expect(screen.getByTestId("relationship-row-action:delete:session_events:session-1")).toBeTruthy();
  });
});
```

Notes:

- Keep this deterministic. It exists specifically to prove sparse fallback and
  unresolved-relationship behavior without depending on a live generated app to
  contain a conveniently broken or sparse case.
