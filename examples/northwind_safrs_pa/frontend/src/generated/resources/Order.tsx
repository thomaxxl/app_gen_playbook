import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const OrderPages: ResourcePageSet = makeSchemaDrivenPages("Order");

export const OrderList = OrderPages.list;
export const OrderShow = OrderPages.show;
export const OrderEdit = OrderPages.edit;
export const OrderCreate = OrderPages.create;
