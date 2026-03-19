import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const SupplierPages: ResourcePageSet = makeSchemaDrivenPages("Supplier");

export const SupplierList = SupplierPages.list;
export const SupplierShow = SupplierPages.show;
export const SupplierEdit = SupplierPages.edit;
export const SupplierCreate = SupplierPages.create;
