import type { ResourcePageRegistry } from "../shared-runtime/resourceRegistry";
import { CategoryPages } from "./resources/Category";
import { CustomerPages } from "./resources/Customer";
import { CustomerDemographicPages } from "./resources/CustomerDemographic";
import { DepartmentPages } from "./resources/Department";
import { EmployeePages } from "./resources/Employee";
import { EmployeeAuditPages } from "./resources/EmployeeAudit";
import { EmployeeTerritoryPages } from "./resources/EmployeeTerritory";
import { LocationPages } from "./resources/Location";
import { OrderPages } from "./resources/Order";
import { OrderDetailPages } from "./resources/OrderDetail";
import { ProductPages } from "./resources/Product";
import { RegionPages } from "./resources/Region";
import { SampleDBVersionPages } from "./resources/SampleDBVersion";
import { ShipperPages } from "./resources/Shipper";
import { SupplierPages } from "./resources/Supplier";
import { TerritoryPages } from "./resources/Territory";
import { UnionPages } from "./resources/Union";

export const generatedResourcePages: ResourcePageRegistry = {
  "Category": CategoryPages,
  "Customer": CustomerPages,
  "CustomerDemographic": CustomerDemographicPages,
  "Department": DepartmentPages,
  "Employee": EmployeePages,
  "EmployeeAudit": EmployeeAuditPages,
  "EmployeeTerritory": EmployeeTerritoryPages,
  "Location": LocationPages,
  "Order": OrderPages,
  "OrderDetail": OrderDetailPages,
  "Product": ProductPages,
  "Region": RegionPages,
  "SampleDBVersion": SampleDBVersionPages,
  "Shipper": ShipperPages,
  "Supplier": SupplierPages,
  "Territory": TerritoryPages,
  "Union": UnionPages,
};
