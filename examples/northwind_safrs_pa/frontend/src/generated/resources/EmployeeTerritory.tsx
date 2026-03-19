import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const EmployeeTerritoryPages: ResourcePageSet = makeSchemaDrivenPages("EmployeeTerritory");

export const EmployeeTerritoryList = EmployeeTerritoryPages.list;
export const EmployeeTerritoryShow = EmployeeTerritoryPages.show;
export const EmployeeTerritoryEdit = EmployeeTerritoryPages.edit;
export const EmployeeTerritoryCreate = EmployeeTerritoryPages.create;
