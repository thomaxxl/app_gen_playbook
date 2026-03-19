import type { ResourcePages } from "../shared-runtime/resourceRegistry";
import { ConfigurationItemPages } from "./resources/ConfigurationItem";
import { OperationalStatusPages } from "./resources/OperationalStatus";
import { ServicePages } from "./resources/Service";

export const resourcePages: ResourcePages[] = [
  ServicePages,
  ConfigurationItemPages,
  OperationalStatusPages,
];
