import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const RegionPages: ResourcePageSet = makeSchemaDrivenPages("Region");

export const RegionList = RegionPages.list;
export const RegionShow = RegionPages.show;
export const RegionEdit = RegionPages.edit;
export const RegionCreate = RegionPages.create;
