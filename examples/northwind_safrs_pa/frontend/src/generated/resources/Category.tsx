import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const CategoryPages: ResourcePageSet = makeSchemaDrivenPages("Category");

export const CategoryList = CategoryPages.list;
export const CategoryShow = CategoryPages.show;
export const CategoryEdit = CategoryPages.edit;
export const CategoryCreate = CategoryPages.create;
