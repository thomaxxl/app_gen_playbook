import type { ResourcePages } from "../shared-runtime/resourceRegistry";
import { FlightPages } from "./resources/Flight";
import { FlightStatusPages } from "./resources/FlightStatus";
import { GatePages } from "./resources/Gate";

export const resourcePages: ResourcePages[] = [
  GatePages,
  FlightPages,
  FlightStatusPages,
];
