import {
  makeSchemaDrivenPages,
  type ResourcePageSet,
} from "../../shared-runtime/resourceRegistry";

export const SampleDBVersionPages: ResourcePageSet = makeSchemaDrivenPages("SampleDBVersion");

export const SampleDBVersionList = SampleDBVersionPages.list;
export const SampleDBVersionShow = SampleDBVersionPages.show;
export const SampleDBVersionEdit = SampleDBVersionPages.edit;
export const SampleDBVersionCreate = SampleDBVersionPages.create;
