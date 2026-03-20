# `frontend/src/SchemaDrivenAdminApp.tsx`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)

This template makes the custom-route extension point explicit and includes the
required bootstrap/error behavior.

```tsx
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Component, startTransition, useEffect, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Admin } from "react-admin";
import type { DataProvider, LayoutProps } from "react-admin";
import type { ComponentType } from "react";
import type { Schema } from "./shared-runtime/admin/adminSchema";

import ErrorState from "./ErrorState";
import type { RawAdminYaml } from "./shared-runtime/admin/resourceMetadata";

import {
  AdminSchemaProvider,
  type AdminAppConfig,
  loadAdminBootstrap,
} from "./shared-runtime/admin/schemaContext";
import { buildResources } from "./shared-runtime/resourceRegistry";
import type { ResourcePages } from "./shared-runtime/resourceRegistry";

interface BootstrapState {
  dataProvider: DataProvider;
  rawYaml: RawAdminYaml;
  schema: Schema;
}

class ResourceRenderBoundary extends Component<
  { adminYamlUrl: string; title: string; children: ReactNode },
  { error: string | null }
> {
  state = { error: null };

  static getDerivedStateFromError(error: unknown) {
    return {
      error: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(_error: unknown, _info: ErrorInfo) {}

  render() {
    if (this.state.error) {
      return (
        <Box sx={{ maxWidth: 880, mx: "auto", p: 3 }}>
          <ErrorState
            details={`Schema URL: ${this.props.adminYamlUrl}\n\n${this.state.error}`}
            message="Failed to render resource metadata."
            title={this.props.title}
          />
        </Box>
      );
    }

    return this.props.children;
  }
}

function RenderedResourceElements({
  rawYaml,
  resourcePages,
  schema,
}: {
  rawYaml: RawAdminYaml;
  resourcePages: ResourcePages[];
  schema: Schema;
}) {
  return buildResources(resourcePages, schema, rawYaml);
}

export function SchemaDrivenAdminApp({
  appConfig,
  layout,
  resourcePages,
  children,
}: {
  appConfig: AdminAppConfig;
  layout?: ComponentType<LayoutProps>;
  resourcePages: ResourcePages[];
  children?: ReactNode;
}) {
  const [bootstrap, setBootstrap] = useState<BootstrapState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    startTransition(() => {
      loadAdminBootstrap(appConfig)
        .then((next) => {
          if (mounted) {
            setBootstrap(next);
          }
        })
        .catch((err: unknown) => {
          if (mounted) {
            setError(err instanceof Error ? err.message : String(err));
          }
        });
    });

    return () => {
      mounted = false;
    };
  }, [appConfig]);

  if (error) {
    return (
      <Box sx={{ maxWidth: 880, mx: "auto", p: 3 }}>
        <ErrorState
          details={`Schema URL: ${appConfig.adminYamlUrl}\n\n${error}`}
          message="Failed to initialize the schema or data provider."
          title={appConfig.title}
        />
      </Box>
    );
  }

  if (!bootstrap) {
    return (
      <Stack alignItems="center" justifyContent="center" minHeight="100vh" spacing={2}>
        <CircularProgress />
        <Typography component="h1" variant="h5">
          {appConfig.title}
        </Typography>
        <Typography color="text.secondary">
          Loading `admin.yaml` and wiring `safrs-jsonapi-client`...
        </Typography>
      </Stack>
    );
  }

  return (
    <AdminSchemaProvider rawYaml={bootstrap.rawYaml} schema={bootstrap.schema}>
      <ResourceRenderBoundary adminYamlUrl={appConfig.adminYamlUrl} title={appConfig.title}>
        <Admin
          dataProvider={bootstrap.dataProvider}
          disableTelemetry
          layout={layout}
          title={appConfig.title}
        >
          {children}
          <RenderedResourceElements
            rawYaml={bootstrap.rawYaml}
            resourcePages={resourcePages}
            schema={bootstrap.schema}
          />
        </Admin>
      </ResourceRenderBoundary>
    </AdminSchemaProvider>
  );
}
```

Notes:

- `Component` must be imported as a runtime value, not type-only.
- Resource registration must happen inside a child rendered under the boundary,
  so metadata failures thrown by `buildResources(...)` are actually caught by
  the visible error screen.
- Bootstrap and render-time failures SHOULD use the shared page-level error
  pattern so the app shell stays visually consistent.
