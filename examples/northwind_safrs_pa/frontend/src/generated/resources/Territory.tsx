import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const TerritoryPages: ResourcePageSet = makeSchemaDrivenPages("Territory");

export const TerritoryList = TerritoryPages.list;
export const TerritoryShow = TerritoryPages.show;
export const TerritoryEdit = TerritoryPages.edit;
export const TerritoryCreate = TerritoryPages.create;
