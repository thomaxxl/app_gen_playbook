import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import { CustomRoutes, Resource } from "react-admin";
import { Navigate, Route } from "react-router-dom";

import Home from "./Home";
import Landing from "./Landing";
import { appConfig } from "./config";
import { resourcePages } from "./generated/resourcePages";
import { SchemaDrivenAdminApp } from "./shared-runtime/SchemaDrivenAdminApp";

export default function App() {
  return (
    <SchemaDrivenAdminApp appConfig={appConfig} resourcePages={resourcePages}>
      <Resource
        icon={HomeRoundedIcon}
        list={Home}
        name="Home"
        options={{ label: "Home" }}
      />
      <CustomRoutes noLayout>
        <Route element={<Navigate replace to="/Home" />} path="/" />
        <Route element={<Landing />} path="/Landing" />
      </CustomRoutes>
    </SchemaDrivenAdminApp>
  );
}
