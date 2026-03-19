import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const EmployeeAuditPages: ResourcePageSet = makeSchemaDrivenPages("EmployeeAudit");

export const EmployeeAuditList = EmployeeAuditPages.list;
export const EmployeeAuditShow = EmployeeAuditPages.show;
export const EmployeeAuditEdit = EmployeeAuditPages.edit;
export const EmployeeAuditCreate = EmployeeAuditPages.create;
