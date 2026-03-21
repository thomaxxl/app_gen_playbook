import { existsSync } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";

import { expect, test } from "@playwright/test";

type ReviewSurface = {
  page_label: string;
  path: string;
  preview_required?: boolean;
  qa_live_test_required?: boolean;
  route_id: string;
};

type CaptureSuccess = {
  assertions: string[];
  file: string;
  route: string;
  routeId: string;
  surface: string;
};

type CaptureFailure = {
  detail: string;
  route: string;
  routeId: string;
  surface: string;
};

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
}

function resolveReviewPlanPath(): string {
  if (process.env.REVIEW_PLAN_PATH) {
    return path.resolve(process.cwd(), process.env.REVIEW_PLAN_PATH);
  }

  const playbookReviewPlan = path.resolve(
    process.cwd(),
    "..",
    "..",
    "runs",
    "current",
    "evidence",
    "quality",
    "review-plan.json",
  );
  if (existsSync(playbookReviewPlan)) {
    return playbookReviewPlan;
  }

  return path.resolve(process.cwd(), "..", "evidence", "quality", "review-plan.json");
}

function resolveOutputDir(): string {
  if (process.env.QA_SCREENSHOT_OUTPUT_DIR) {
    return path.resolve(process.cwd(), process.env.QA_SCREENSHOT_OUTPUT_DIR);
  }

  const playbookEvidenceDir = path.resolve(
    process.cwd(),
    "..",
    "..",
    "runs",
    "current",
    "evidence",
    "ui-previews",
    "qa",
  );
  if (existsSync(path.dirname(playbookEvidenceDir))) {
    return playbookEvidenceDir;
  }

  return path.resolve(process.cwd(), "..", "evidence", "ui-previews", "qa");
}

function resolveManifestPath(outputDir: string): string {
  if (process.env.QA_SCREENSHOT_MANIFEST) {
    return path.resolve(process.cwd(), process.env.QA_SCREENSHOT_MANIFEST);
  }
  return path.join(path.dirname(outputDir), "qa-manifest.md");
}

async function loadReviewSurfaces(): Promise<ReviewSurface[]> {
  const reviewPlanPath = resolveReviewPlanPath();
  const payload = JSON.parse(await fs.readFile(reviewPlanPath, "utf-8")) as {
    surfaces?: ReviewSurface[];
  };
  const surfaces = Array.isArray(payload.surfaces) ? payload.surfaces : [];
  return surfaces.filter(
    (surface) =>
      typeof surface.path === "string" &&
      typeof surface.route_id === "string" &&
      typeof surface.page_label === "string" &&
      (surface.qa_live_test_required === true || surface.preview_required === true),
  );
}

async function writeManifest(
  manifestPath: string,
  captures: CaptureSuccess[],
  failures: CaptureFailure[],
): Promise<void> {
  const status = failures.length === 0 ? "captured" : "partial-failure";
  const lines = [
    "# QA Screenshot Manifest",
    "",
    `capture_status: ${status}`,
    "- command: `npm run capture:qa-screenshots`",
    "- reviewed_surfaces:",
    ...captures.map((capture) =>
      `  - \`${capture.surface}\` at \`${capture.route}\` -> \`${capture.file}\``,
    ),
    "- automated_content_assertions:",
    ...captures.flatMap((capture) => [
      `  - \`${capture.surface}\``,
      ...capture.assertions.map((assertion) => `    - ${assertion}`),
    ]),
  ];

  if (failures.length > 0) {
    lines.push("- capture_failures:");
    lines.push(
      ...failures.map(
        (failure) =>
          `  - \`${failure.surface}\` at \`${failure.route}\` -> ${failure.detail}`,
      ),
    );
  }

  lines.push(
    "- review_conclusion: QA screenshot capture refreshed the review-plan routes for final QA review; missing or broken routes remain listed under capture_failures when present.",
    "",
  );

  await fs.writeFile(manifestPath, lines.join("\n"), "utf-8");
}

test("capture QA screenshots for all review-plan surfaces", async ({ page }) => {
  const outputDir = resolveOutputDir();
  const manifestPath = resolveManifestPath(outputDir);
  const captures: CaptureSuccess[] = [];
  const failures: CaptureFailure[] = [];
  const surfaces = await loadReviewSurfaces();

  expect(surfaces.length).toBeGreaterThan(0);
  await fs.mkdir(outputDir, { recursive: true });

  for (const surface of surfaces) {
    const screenshotName = `qa-${surface.route_id.toLowerCase()}-${slugify(surface.page_label)}.png`;
    try {
      await page.setViewportSize({ width: 1440, height: 1024 });
      await page.goto(surface.path, { waitUntil: "domcontentloaded", timeout: 30_000 });
      await page.waitForTimeout(800);

      const bodyText = (await page.locator("body").innerText()).replace(/\s+/g, " ").trim();
      expect(bodyText.length).toBeGreaterThan(20);
      expect(bodyText.toLowerCase()).not.toMatch(
        /application error|cannot read properties|unexpected error|traceback|uncaught/i,
      );

      await page.screenshot({
        fullPage: true,
        path: path.join(outputDir, screenshotName),
      });

      captures.push({
        assertions: [
          "body text is present and non-empty",
          "no obvious runtime error text is visible",
        ],
        file: screenshotName,
        route: surface.path,
        routeId: surface.route_id,
        surface: `${surface.route_id} ${surface.page_label}`,
      });
    } catch (error) {
      failures.push({
        detail: error instanceof Error ? error.message : String(error),
        route: surface.path,
        routeId: surface.route_id,
        surface: `${surface.route_id} ${surface.page_label}`,
      });
    }
  }

  await writeManifest(manifestPath, captures, failures);
  expect(
    failures,
    failures
      .map((failure) => `${failure.routeId} ${failure.route}: ${failure.detail}`)
      .join("\n"),
  ).toHaveLength(0);
});
