import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const UnionPages: ResourcePageSet = makeSchemaDrivenPages("Union");

export const UnionList = UnionPages.list;
export const UnionShow = UnionPages.show;
export const UnionEdit = UnionPages.edit;
export const UnionCreate = UnionPages.create;
