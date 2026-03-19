import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const ProductPages: ResourcePageSet = makeSchemaDrivenPages("Product");

export const ProductList = ProductPages.list;
export const ProductShow = ProductPages.show;
export const ProductEdit = ProductPages.edit;
export const ProductCreate = ProductPages.create;
