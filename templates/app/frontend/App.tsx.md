import { CustomRoutes, Resource } from "react-admin";
import { Navigate, Route } from "react-router-dom";

import AppIcon from "./AppIcon";
import Home from "./Home";
import {
  ArtifactsPage,
  BlockersPage,
  ChangesPage,
  EvidencePage,
  FilesPage,
  MessagesPage,
  ObserverLayout,
  PhasesPage,
  TimelinePage,
  WorkersPage,
} from "./ObserverPages";
import { appConfig } from "./config";
import { resourcePages } from "./resourcePages";
import { SchemaDrivenAdminApp } from "./SchemaDrivenAdminApp";

export default function App() {
  return (
    <SchemaDrivenAdminApp
      appConfig={appConfig}
      layout={ObserverLayout}
      resourcePages={resourcePages}
    >
      <>
        <Resource
          icon={(props) => <AppIcon name="home" {...props} />}
          list={Home}
          name="Home"
          options={{ label: "Run Overview" }}
        />
        <CustomRoutes noLayout>
          <Route element={<Navigate replace to="/Home" />} path="/" />
        </CustomRoutes>
        <CustomRoutes>
          <Route element={<PhasesPage />} path="/phases" />
          <Route element={<ArtifactsPage />} path="/artifacts" />
          <Route element={<MessagesPage />} path="/messages" />
          <Route element={<BlockersPage />} path="/blockers" />
          <Route element={<EvidencePage />} path="/evidence" />
          <Route element={<WorkersPage />} path="/workers" />
          <Route element={<TimelinePage />} path="/timeline" />
          <Route element={<FilesPage />} path="/files" />
          <Route element={<ChangesPage />} path="/changes" />
          <Route element={<Navigate replace to="/phases" />} path="/Collection" />
          <Route element={<Navigate replace to="/messages" />} path="/Item" />
          <Route element={<Navigate replace to="/files" />} path="/Status" />
        </CustomRoutes>
      </>
    </SchemaDrivenAdminApp>
  );
}
