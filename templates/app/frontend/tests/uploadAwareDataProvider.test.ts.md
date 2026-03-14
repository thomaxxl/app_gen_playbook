# `frontend/tests/uploadAwareDataProvider.test.ts`

See also:

- [../../../../specs/contracts/files/uploads-and-frontend-integration.md](../../../../specs/contracts/files/uploads-and-frontend-integration.md)
- [../shared-runtime/files/uploadAwareDataProvider.ts.md](../shared-runtime/files/uploadAwareDataProvider.ts.md)

Use this file when the app supports uploaded files.

```ts
import { describe, expect, it, vi } from "vitest";

import {
  buildUploadFieldMap,
  createUploadAwareDataProvider,
} from "../src/shared-runtime/files/uploadAwareDataProvider";

describe("buildUploadFieldMap", () => {
  it("builds per-resource mappings from file/image admin.yaml fields", () => {
    const map = buildUploadFieldMap({
      resources: {
        Gallery: {
          attributes: {
            cover_image: {
              type: "image",
              upload_target: "cover_image_file_id",
              purpose: "gallery-cover",
            },
          },
        },
        ImageAsset: {
          attributes: {
            upload: {
              type: "file",
              upload_target: "stored_file_id",
            },
          },
        },
      },
    });

    expect(map).toEqual({
      Gallery: {
        cover_image: {
          purpose: "gallery-cover",
          targetField: "cover_image_file_id",
        },
      },
      ImageAsset: {
        upload: {
          purpose: undefined,
          targetField: "stored_file_id",
        },
      },
    });
  });
});

describe("createUploadAwareDataProvider", () => {
  it("uploads a new file and replaces the synthetic field with the target field", async () => {
    const baseProvider = {
      create: vi.fn(async (_resource, params) => ({
        data: { id: "10", ...params.data },
      })),
      update: vi.fn(),
    } as const;

    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ data: { id: "f_123" } }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 200 }));

    const provider = createUploadAwareDataProvider(baseProvider as never, {
      apiRoot: "/api",
      uploadFieldMap: {
        Gallery: {
          cover_image: {
            targetField: "cover_image_file_id",
            purpose: "gallery-cover",
          },
        },
      },
    });

    const file = new File(["png"], "cover.png", { type: "image/png" });

    await provider.create("Gallery", {
      data: {
        cover_image: {
          rawFile: file,
          src: "blob:http://localhost/mock",
          title: "cover.png",
        },
        title: "Summer",
      },
    } as never);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(baseProvider.create).toHaveBeenCalledWith(
      "Gallery",
      expect.objectContaining({
        data: {
          cover_image_file_id: "f_123",
          title: "Summer",
        },
      }),
    );

    fetchMock.mockRestore();
  });
});
```
