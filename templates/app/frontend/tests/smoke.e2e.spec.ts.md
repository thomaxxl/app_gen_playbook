import { expect, test } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";

type RouteExpectation = {
  heading: RegExp;
  path: string;
  section: RegExp;
};

type JsonApiResource = {
  attributes?: Record<string, unknown>;
  id: string;
  type?: string;
};

type JsonApiDocument = {
  data: JsonApiResource | JsonApiResource[];
};

const observerRoutes: RouteExpectation[] = [
  {
    heading: /run overview/i,
    path: "/app/#/overview",
    section: /current run summary/i,
  },
  {
    heading: /phase status/i,
    path: "/app/#/phases",
    section: /phase breakdown/i,
  },
  {
    heading: /artifacts & evidence/i,
    path: "/app/#/artifacts",
    section: /package readiness/i,
  },
  {
    heading: /handoffs & messages/i,
    path: "/app/#/handoffs",
    section: /recent handoffs/i,
  },
  {
    heading: /blockers & verification/i,
    path: "/app/#/blockers",
    section: /active blockers/i,
  },
  {
    heading: /workers & timeline/i,
    path: "/app/#/workers",
    section: /lane summaries/i,
  },
  {
    heading: /files & change requests/i,
    path: "/app/#/files",
    section: /recent run files/i,
  },
];

function collectObserverErrors(page: Page) {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedResponses: string[] = [];

  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });

  page.on("pageerror", (error) => {
    pageErrors.push(error.message);
  });

  page.on("response", (response) => {
    const url = response.url();
    if (!url.startsWith("http://127.0.0.1:5173") && !url.startsWith("http://127.0.0.1:5656")) {
      return;
    }
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${url}`);
    }
  });

  return { consoleErrors, failedResponses, pageErrors };
}

function firstResource(document: JsonApiDocument): JsonApiResource {
  if (!Array.isArray(document.data) || document.data.length === 0) {
    throw new Error("Expected at least one resource in the JSON:API list payload.");
  }

  return document.data[0];
}

function singleResource(document: JsonApiDocument): JsonApiResource {
  if (Array.isArray(document.data)) {
    if (document.data.length === 0) {
      throw new Error("Expected a single related resource, but the payload was empty.");
    }
    return document.data[0];
  }

  return document.data;
}

async function loadFirstRunRelationshipProof(request: APIRequestContext) {
  const runsResponse = await request.get("http://127.0.0.1:5656/api/runs");
  expect(runsResponse.status()).toBe(200);
  const runsPayload = (await runsResponse.json()) as JsonApiDocument;
  const firstRun = firstResource(runsPayload);

  const projectResponse = await request.get(`http://127.0.0.1:5656/api/runs/${firstRun.id}/project`);
  expect(projectResponse.status()).toBe(200);
  const projectPayload = (await projectResponse.json()) as JsonApiDocument;
  const project = singleResource(projectPayload);
  const projectLabel = String(
    project.attributes?.name
      ?? project.attributes?.slug
      ?? project.id,
  );

  return {
    projectLabel,
    runId: String(firstRun.id),
  };
}

async function expectObserverRoute(page: Page, route: RouteExpectation) {
  await page.goto(route.path);
  await expect(page.getByText(route.heading).first()).toBeVisible();
  await expect(page.getByText(route.section).first()).toBeVisible();
  await expect(
    page.getByText(/could not load current-run data from the live api/i),
  ).toHaveCount(0);
  await expect(
    page.getByText(/failed to initialize the schema or data provider/i),
  ).toHaveCount(0);
}

test("observer routes load without blank screens, loops, or crashes", async ({
  page,
  request,
}) => {
  const { consoleErrors, failedResponses, pageErrors } = collectObserverErrors(page);

  const adminYamlResponse = await request.get("http://127.0.0.1:5173/ui/admin/admin.yaml");
  expect(adminYamlResponse.status()).toBe(200);

  await page.goto("/app/");
  await expect.poll(() => page.url()).toContain("/app/#/overview");
  await expect(page.getByTestId("entry-purpose").last()).toBeVisible();
  await expect(page.getByTestId("entry-primary-cta")).toBeVisible();
  await expect(page.getByText(/current run/i).first()).toBeVisible();
  await expect(page.getByText(/pending handoffs/i).first()).toBeVisible();

  for (const route of observerRoutes) {
    await expectObserverRoute(page, route);
  }

  await page.goto("/app/#/Run");
  await expect(page.getByText(/^run$/i).first()).toBeVisible();
  await expect(page.getByText(/not found/i)).toHaveCount(0);
  await expect(page.getByText(/either you typed a wrong url/i)).toHaveCount(0);
  await expect(page.getByText(/title/i).first()).toBeVisible();
  await expect(page.getByRole("button", { name: /create/i })).toHaveCount(0);
  await expect(page.getByRole("link", { name: /create/i })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /delete/i })).toHaveCount(0);
  await expect(page.getByRole("link", { name: /delete/i })).toHaveCount(0);

  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});

test("observer relationship surfaces resolve through dialog and show-tab paths", async ({
  page,
  request,
}) => {
  const { projectLabel, runId } = await loadFirstRunRelationshipProof(request);

  await page.goto("/app/#/Run");
  await expect(page.getByText(/^run$/i).first()).toBeVisible();

  const relatedRecordButton = page.getByRole("button", { name: projectLabel }).first();
  await expect(relatedRecordButton).toBeVisible();
  await relatedRecordButton.click();

  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("button", { name: /^EDIT$/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /^VIEW$/i })).toBeVisible();
  await expect(page.getByText(projectLabel).last()).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);

  await page.goto(`/app/#/Run/${runId}/show`);
  const projectTab = page.getByRole("tab", { name: /project/i });
  await expect(projectTab).toBeVisible();
  await projectTab.click();
  await expect(projectTab).toHaveAttribute("aria-selected", "true");
  await expect(page.getByText(projectLabel).last()).toBeVisible();
  await expect(page.getByText(/no related record/i)).toHaveCount(0);
});

test("observer landing remains usable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/#/overview");

  await expect(page.getByTestId("entry-purpose").last()).toBeVisible();
  await expect(page.getByTestId("entry-primary-cta")).toBeVisible();
  await expect(page.getByText(/current run/i).first()).toBeVisible();
  await expect(page.getByText(/pending handoffs/i).first()).toBeVisible();
});
