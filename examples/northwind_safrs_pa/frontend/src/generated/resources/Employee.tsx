import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const EmployeePages: ResourcePageSet = makeSchemaDrivenPages("Employee");

export const EmployeeList = EmployeePages.list;
export const EmployeeShow = EmployeePages.show;
export const EmployeeEdit = EmployeePages.edit;
export const EmployeeCreate = EmployeePages.create;
