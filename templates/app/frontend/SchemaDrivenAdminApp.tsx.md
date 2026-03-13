# `frontend/src/shared-runtime/SchemaDrivenAdminApp.tsx`

See also:

- [../../../specs/contracts/frontend/runtime-contract.md](../../../specs/contracts/frontend/runtime-contract.md)

This template makes the custom-route extension point explicit and includes the
required bootstrap/error behavior.

```tsx
import { Component, startTransition, useEffect, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { Admin } from "react-admin";
import type { DataProvider } from "react-admin";
import type { Schema } from "safrs-jsonapi-client";

import type { RawAdminYaml } from "./admin/resourceMetadata";

import {
  AdminSchemaProvider,
  type AdminAppConfig,
  loadAdminBootstrap,
} from "./admin/schemaContext";
import { buildResources } from "./resourceRegistry";
import type { ResourcePages } from "./resourceRegistry";

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
        <main style={{ fontFamily: "sans-serif", minHeight: "100vh", padding: 24 }}>
          <h1>{this.props.title}</h1>
          <p>Failed to render resource metadata.</p>
          <p>Schema URL: <code>{this.props.adminYamlUrl}</code></p>
          <pre>{this.state.error}</pre>
        </main>
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
  resourcePages,
  children,
}: {
  appConfig: AdminAppConfig;
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
      <main style={{ fontFamily: "sans-serif", minHeight: "100vh", padding: 24 }}>
        <h1>{appConfig.title}</h1>
        <p>Failed to initialize the schema or data provider.</p>
        <p>Schema URL: <code>{appConfig.adminYamlUrl}</code></p>
        <pre>{error}</pre>
      </main>
    );
  }

  if (!bootstrap) {
    return (
      <main style={{ fontFamily: "sans-serif", minHeight: "100vh", padding: 24 }}>
        <h1>{appConfig.title}</h1>
        <p>Loading `admin.yaml` and wiring `safrs-jsonapi-client`...</p>
      </main>
    );
  }

  return (
    <AdminSchemaProvider rawYaml={bootstrap.rawYaml} schema={bootstrap.schema}>
      <ResourceRenderBoundary adminYamlUrl={appConfig.adminYamlUrl} title={appConfig.title}>
        <Admin
          dataProvider={bootstrap.dataProvider}
          disableTelemetry
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
