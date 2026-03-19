import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const OrderDetailPages: ResourcePageSet = makeSchemaDrivenPages("OrderDetail");

export const OrderDetailList = OrderDetailPages.list;
export const OrderDetailShow = OrderDetailPages.show;
export const OrderDetailEdit = OrderDetailPages.edit;
export const OrderDetailCreate = OrderDetailPages.create;
