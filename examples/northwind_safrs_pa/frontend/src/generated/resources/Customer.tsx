import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const CustomerPages: ResourcePageSet = makeSchemaDrivenPages("Customer");

export const CustomerList = CustomerPages.list;
export const CustomerShow = CustomerPages.show;
export const CustomerEdit = CustomerPages.edit;
export const CustomerCreate = CustomerPages.create;
