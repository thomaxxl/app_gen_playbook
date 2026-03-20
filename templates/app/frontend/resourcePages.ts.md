import {
  makeSchemaDrivenPages,
  type ResourcePages,
} from "./shared-runtime/resourceRegistry";
import { OBSERVER_RESOURCE_PAGES } from "./observerRouteContracts";

export const resourcePages: ResourcePages[] = OBSERVER_RESOURCE_PAGES.map((resourceName) =>
  makeSchemaDrivenPages(resourceName),
);
