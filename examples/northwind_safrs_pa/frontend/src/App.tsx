import { SchemaDrivenAdminApp } from "./shared-runtime/SchemaDrivenAdminApp";

import { appConfig } from "./config";
import { generatedResourcePages } from "./generated/resourcePages";

export default function App() {
  return (
    <SchemaDrivenAdminApp
      appConfig={appConfig}
      resourcePages={generatedResourcePages}
    />
  );
}
