import { startTransition, useEffect, useState } from "react";
import type { ReactNode } from "react";
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
        <p>
          Schema URL: <code>{appConfig.adminYamlUrl}</code>
        </p>
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

  let renderedResources: ReactNode;
  try {
    renderedResources = buildResources(
      resourcePages,
      bootstrap.schema,
      bootstrap.rawYaml,
    );
  } catch (error) {
    return (
      <main style={{ fontFamily: "sans-serif", minHeight: "100vh", padding: 24 }}>
        <h1>{appConfig.title}</h1>
        <p>Failed to render resource metadata.</p>
        <p>
          Schema URL: <code>{appConfig.adminYamlUrl}</code>
        </p>
        <pre>{error instanceof Error ? error.message : String(error)}</pre>
      </main>
    );
  }

  return (
    <AdminSchemaProvider rawYaml={bootstrap.rawYaml} schema={bootstrap.schema}>
      <Admin dataProvider={bootstrap.dataProvider} disableTelemetry title={appConfig.title}>
        {children}
        {renderedResources}
      </Admin>
    </AdminSchemaProvider>
  );
}
