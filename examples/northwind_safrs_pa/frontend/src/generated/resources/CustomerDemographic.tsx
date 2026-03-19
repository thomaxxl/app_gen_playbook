import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const CustomerDemographicPages: ResourcePageSet = makeSchemaDrivenPages("CustomerDemographic");

export const CustomerDemographicList = CustomerDemographicPages.list;
export const CustomerDemographicShow = CustomerDemographicPages.show;
export const CustomerDemographicEdit = CustomerDemographicPages.edit;
export const CustomerDemographicCreate = CustomerDemographicPages.create;
