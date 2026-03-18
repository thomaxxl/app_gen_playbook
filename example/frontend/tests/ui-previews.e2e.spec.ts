import { existsSync } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";

import { expect, test } from "@playwright/test";

type PreviewCapture = {
  file: string;
  route: string;
  surface: string;
};

function resolvePreviewOutputDir(): string {
  if (process.env.UI_PREVIEW_OUTPUT_DIR) {
    return path.resolve(process.cwd(), process.env.UI_PREVIEW_OUTPUT_DIR);
  }

  const playbookEvidenceDir = path.resolve(
    process.cwd(),
    "..",
    "..",
    "runs",
    "current",
    "evidence",
    "ui-previews",
  );
  if (existsSync(playbookEvidenceDir)) {
    return playbookEvidenceDir;
  }

  return path.resolve(process.cwd(), "..", "evidence", "ui-previews");
}

async function writeManifest(outputDir: string, captures: PreviewCapture[]): Promise<void> {
  const lines = [
    "# UI Preview Manifest",
    "",
    "capture_status: captured",
    "- command: `npm run capture:ui-previews`",
    "- reviewed_surfaces:",
    ...captures.map((capture) =>
      `  - \`${capture.surface}\` at \`${capture.route}\` -> \`${capture.file}\``,
    ),
    "",
    "These screenshots are intended for product-facing review.",
    "",
  ];
  await fs.writeFile(path.join(outputDir, "manifest.md"), lines.join("\n"), "utf-8");
}

test("capture reviewable CMDB previews", async ({ page }) => {
  const outputDir = resolvePreviewOutputDir();
  const captures: PreviewCapture[] = [];

  await fs.mkdir(outputDir, { recursive: true });

  await page.setViewportSize({ width: 1440, height: 1024 });
  await page.goto("/admin-app/#/Home");
  await expect(page.getByRole("link", { name: /home/i })).toBeVisible();
  await expect(page.getByText(/cmdb operations console/i)).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "home-desktop.png"),
  });
  captures.push({
    file: "home-desktop.png",
    route: "/admin-app/#/Home",
    surface: "Home desktop",
  });

  await page.goto("/admin-app/#/Landing");
  await expect(page.getByText(/dashboard unavailable/i)).toHaveCount(0);
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "landing.png"),
  });
  captures.push({
    file: "landing.png",
    route: "/admin-app/#/Landing",
    surface: "Landing page",
  });

  await page.goto("/admin-app/#/Service");
  await expect(page.getByText("COMMERCE")).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "service-list.png"),
  });
  captures.push({
    file: "service-list.png",
    route: "/admin-app/#/Service",
    surface: "Service list",
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/admin-app/#/Home");
  await expect(page.getByRole("link", { name: /home/i })).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "home-mobile.png"),
  });
  captures.push({
    file: "home-mobile.png",
    route: "/admin-app/#/Home",
    surface: "Home mobile",
  });

  await writeManifest(outputDir, captures);
});
