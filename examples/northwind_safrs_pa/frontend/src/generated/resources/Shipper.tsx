import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const ShipperPages: ResourcePageSet = makeSchemaDrivenPages("Shipper");

export const ShipperList = ShipperPages.list;
export const ShipperShow = ShipperPages.show;
export const ShipperEdit = ShipperPages.edit;
export const ShipperCreate = ShipperPages.create;
