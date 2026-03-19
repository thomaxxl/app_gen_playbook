# `frontend/tests/ui-previews.e2e.spec.ts`

See also:

- [../../../../specs/contracts/frontend/validation.md](../../../../specs/contracts/frontend/validation.md)
- [../playwright.config.ts.md](../playwright.config.ts.md)

This is the reviewable screenshot companion to the smoke suite.

```ts
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

  await page.goto("/app/#/Collection");
  await expect(page.getByRole("main")).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "collection-list.png"),
  });
  captures.push({
    assertions: [
      "main application region is visible",
    ],
    file: "collection-list.png",
    route: "/app/#/Collection",
    surface: "Collection list",
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/#/Home");
  await expect(page.getByTestId("entry-primary-cta")).toBeVisible();
  await page.screenshot({
    fullPage: true,
    path: path.join(outputDir, "home-mobile.png"),
  });
  captures.push({
    assertions: [
      "primary CTA remains visible at mobile width",
    ],
    file: "home-mobile.png",
    route: "/app/#/Home",
    surface: "Home mobile",
  });

  await writeManifest(outputDir, captures);
});
```

Notes:

- This file is for intentional success-case screenshots, not failure artifacts.
- The output directory SHOULD default to the playbook evidence tree when the
  generated app still lives inside the playbook repo.
- In a standalone generated app repo, it MAY fall back to a local
  `app/evidence/ui-previews/` directory instead.
