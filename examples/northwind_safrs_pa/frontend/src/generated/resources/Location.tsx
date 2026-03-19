import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const LocationPages: ResourcePageSet = makeSchemaDrivenPages("Location");

export const LocationList = LocationPages.list;
export const LocationShow = LocationPages.show;
export const LocationEdit = LocationPages.edit;
export const LocationCreate = LocationPages.create;
