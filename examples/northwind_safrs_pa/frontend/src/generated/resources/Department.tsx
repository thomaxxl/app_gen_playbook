import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const DepartmentPages: ResourcePageSet = makeSchemaDrivenPages("Department");

export const DepartmentList = DepartmentPages.list;
export const DepartmentShow = DepartmentPages.show;
export const DepartmentEdit = DepartmentPages.edit;
export const DepartmentCreate = DepartmentPages.create;
