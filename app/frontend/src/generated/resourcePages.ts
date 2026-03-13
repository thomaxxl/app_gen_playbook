import type { ResourcePages } from "../shared-runtime/resourceRegistry";
import { PairingPages } from "./resources/Pairing";
import { PairingStatusPages } from "./resources/PairingStatus";
import { PlayerPages } from "./resources/Player";
import { TournamentPages } from "./resources/Tournament";

export const resourcePages: ResourcePages[] = [
  TournamentPages,
  PlayerPages,
  PairingPages,
  PairingStatusPages,
];
