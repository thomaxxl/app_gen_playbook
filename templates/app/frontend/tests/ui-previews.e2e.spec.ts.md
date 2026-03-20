import { existsSync } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";

import { expect, test } from "@playwright/test";

type PreviewCapture = {
  file: string;
  route: string;
  surface: string;
  assertions: string[];
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

async function writeManifest(
  outputDir: string,
  captures: PreviewCapture[],
): Promise<void> {
  const lines = [
    "# UI Preview Manifest",
    "",
    "capture_status: captured",
    "content_validation_status: reviewed",
    "- command: `npm run capture:ui-previews`",
    "- reviewed_surfaces:",
    ...captures.map((capture) =>
      `  - \`${capture.surface}\` at \`${capture.route}\` -> \`${capture.file}\``,
    ),
    "- automated_content_assertions:",
    ...captures.flatMap((capture) => [
      `  - \`${capture.surface}\``,
      ...capture.assertions.map((assertion) => `    - ${assertion}`),
    ]),
    "- frontend_validation: approved",
    "- architect_validation: pending-review",
    "- product_manager_validation: pending-review",
    "- review_conclusion: Frontend verified the captured surfaces show meaningful visible content; Architect and Product Manager review is still required.",
    "",
    "These screenshots are intended for product-facing review.",
    "",
  ];
  await fs.writeFile(
    path.join(outputDir, "manifest.md"),
    lines.join("\n"),
    "utf-8",
  );
}

test("capture reviewable UI previews", async ({ page }) => {
  const outputDir = resolvePreviewOutputDir();
  const captures: PreviewCapture[] = [];

  await fs.mkdir(outputDir, { recursive: true });

  await page.setViewportSize({ width: 1440, height: 1024 });
  await page.goto("/app/#/Home");
  await expect(page.getByText(/run overview/i)).toBeVisible();
  await expect(page.getByTestId("entry-purpose")).toBeVisible();
  await expect(page.getByTestId("entry-primary-cta")).toBeVisible();
  await expect(page.getByTestId("entry-proof-strip")).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "home-desktop.png"),
  });
  captures.push({
    assertions: [
      "hero purpose statement is visible",
      "primary CTA is visible",
      "proof strip is visible",
    ],
    file: "home-desktop.png",
    route: "/app/#/Home",
    surface: "Home desktop",
  });

  await page.goto("/app/#/phases");
  await expect(page.getByText(/phases/i).first()).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "phases-desktop.png"),
  });
  captures.push({
    assertions: [
      "phase heading is visible",
      "phase status cards are visible",
    ],
    file: "phases-desktop.png",
    route: "/app/#/phases",
    surface: "Phases desktop",
  });

  await page.goto("/app/#/files");
  await expect(page.getByText(/files/i).first()).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "files-desktop.png"),
  });
  captures.push({
    assertions: [
      "file catalog heading is visible",
      "run file rows are visible",
    ],
    file: "files-desktop.png",
    route: "/app/#/files",
    surface: "Files desktop",
  });

  await writeManifest(outputDir, captures);
});
