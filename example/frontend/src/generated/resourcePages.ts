import type { ResourcePages } from "../shared-runtime/resourceRegistry";
import { GalleryPages } from "./resources/Gallery";
import { ImageAssetPages } from "./resources/ImageAsset";
import { ShareStatusPages } from "./resources/ShareStatus";

export const resourcePages: ResourcePages[] = [
  GalleryPages,
  ImageAssetPages,
  ShareStatusPages,
];
