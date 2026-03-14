import { describe, expect, it, vi } from "vitest";

import {
  extractRawFile,
  prepareImageAssetPayload,
} from "../src/generated/resources/ImageAsset";

describe("ImageAsset upload helpers", () => {
  it("extracts a raw file from the react-admin upload field shape", () => {
    const file = new File(["abc"], "cover.png", { type: "image/png" });

    expect(
      extractRawFile([{ rawFile: file, src: "blob:preview", title: "cover.png" }]),
    ).toBe(file);
  });

  it("uploads the selected file and injects derived asset fields", async () => {
    const file = new File(["image-body"], "launch.png", { type: "image/png" });
    const fetchImpl = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          file_size_mb: 0.002,
          filename: "launch-abc123.png",
          preview_url: "/media/uploads/launch-abc123.png",
        }),
        {
          headers: { "Content-Type": "application/json" },
          status: 201,
        },
      ),
    );

    const result = await prepareImageAssetPayload(
      {
        gallery_id: "1",
        published_at: "",
        status_id: "3",
        title: "Launch",
        upload_file: [{ rawFile: file, src: "blob:preview", title: "launch.png" }],
      },
      { fetchImpl },
    );

    expect(fetchImpl).toHaveBeenCalledOnce();
    expect(result).toMatchObject({
      file_size_mb: 0.002,
      filename: "launch-abc123.png",
      gallery_id: 1,
      preview_url: "/media/uploads/launch-abc123.png",
      published_at: null,
      status_id: 3,
      title: "Launch",
    });
    expect(typeof result.uploaded_at).toBe("string");
  });

  it("keeps existing values when no new file is selected", async () => {
    const result = await prepareImageAssetPayload({
      gallery_id: 2,
      preview_url: "/media/uploads/existing.png",
      published_at: "2026-03-14T09:30",
      status_id: 1,
      title: "Existing",
    });

    expect(result).toMatchObject({
      gallery_id: 2,
      preview_url: "/media/uploads/existing.png",
      published_at: "2026-03-14T09:30:00.000Z",
      status_id: 1,
      title: "Existing",
    });
  });
});
