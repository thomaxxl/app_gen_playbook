import { CustomRoutes } from "react-admin";
import { Navigate, Route } from "react-router-dom";

import Landing from "./Landing";
import { appConfig } from "./config";
import { resourcePages } from "./generated/resourcePages";
import { SchemaDrivenAdminApp } from "./shared-runtime/SchemaDrivenAdminApp";

export default function App() {
  return (
    <SchemaDrivenAdminApp appConfig={appConfig} resourcePages={resourcePages}>
      <CustomRoutes noLayout>
        <Route element={<Navigate replace to="/Landing" />} path="/" />
        <Route element={<Landing />} path="/Landing" />
      </CustomRoutes>
    </SchemaDrivenAdminApp>
  );
}
