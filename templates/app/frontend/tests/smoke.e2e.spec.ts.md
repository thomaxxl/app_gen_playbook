import { expect, test } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";

type AdminResource = {
  endpoint: string;
  name: string;
};

type JsonApiResource = {
  attributes?: Record<string, unknown>;
  id: string;
  type?: string;
};

type JsonApiDocument = {
  data: JsonApiResource | JsonApiResource[];
};

type RelationshipSmokeCandidate = {
  recordId: string;
  resourceName: string;
  showPath: string;
  tabLabel: string;
};

function collectFrontendErrors(page: Page) {
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

function firstResource(document: JsonApiDocument): JsonApiResource | null {
  if (Array.isArray(document.data)) {
    return document.data[0] ?? null;
  }

  return document.data ?? null;
}

function parseAdminResources(adminYaml: string): AdminResource[] {
  const resources: AdminResource[] = [];
  const resourcePattern = /^  ([A-Za-z0-9_]+):\s*$([\s\S]*?)(?=^  [A-Za-z0-9_]+:\s*$|^\S|\Z)/gm;

  for (const match of adminYaml.matchAll(resourcePattern)) {
    const name = match[1];
    const block = match[2] ?? "";
    const endpointMatch = block.match(/^\s+endpoint:\s*([^\s#]+)\s*$/m);
    if (!endpointMatch) {
      continue;
    }
    resources.push({ endpoint: endpointMatch[1], name });
  }

  return resources;
}

async function loadAdminResources(request: APIRequestContext): Promise<AdminResource[]> {
  const response = await request.get("http://127.0.0.1:5173/ui/admin/admin.yaml");
  expect(response.status()).toBe(200);
  return parseAdminResources(await response.text());
}

async function loadFirstRecordId(
  request: APIRequestContext,
  resource: AdminResource,
): Promise<string | null> {
  const response = await request.get(`http://127.0.0.1:5656${resource.endpoint}`);
  if (response.status() !== 200) {
    return null;
  }

  const payload = (await response.json()) as JsonApiDocument;
  const first = firstResource(payload);
  return first ? String(first.id) : null;
}

async function findRelationshipSmokeCandidate(
  page: Page,
  request: APIRequestContext,
  resources: AdminResource[],
): Promise<RelationshipSmokeCandidate> {
  for (const resource of resources) {
    const recordId = await loadFirstRecordId(request, resource);
    if (!recordId) {
      continue;
    }

    const showPath = `/app/#/${resource.name}/${recordId}/show`;
    await page.goto(showPath);
    await expect(page.getByText(/not found/i)).toHaveCount(0);
    await expect(page.getByText(/failed to initialize the schema or data provider/i)).toHaveCount(0);

    const tabs = page.getByRole("tab");
    const tabCount = await tabs.count();
    for (let index = 0; index < tabCount; index += 1) {
      const tab = tabs.nth(index);
      const tabLabel = (await tab.innerText()).trim();
      if (!tabLabel) {
        continue;
      }

      await tab.click();
      await expect(tab).toHaveAttribute("aria-selected", "true");

      const noRelatedRecord = page.getByText(/no related record/i);
      const noRelatedRecords = page.getByText(/no related records/i);
      const emptySingleVisible = (await noRelatedRecord.count()) > 0 && await noRelatedRecord.first().isVisible();
      const emptyManyVisible = (await noRelatedRecords.count()) > 0 && await noRelatedRecords.first().isVisible();

      if (!emptySingleVisible && !emptyManyVisible) {
        return {
          recordId,
          resourceName: resource.name,
          showPath,
          tabLabel,
        };
      }
    }
  }

  throw new Error("Could not find a generated show-page relationship tab with related content.");
}

test("generated app loads without blank screens, loops, or crashes", async ({
  page,
  request,
}) => {
  const { consoleErrors, failedResponses, pageErrors } = collectFrontendErrors(page);

  const adminResources = await loadAdminResources(request);
  expect(adminResources.length).toBeGreaterThan(0);

  await page.goto("/app/");
  await expect.poll(() => page.url()).toContain("/app/#/");
  await expect(page.getByText(/failed to initialize the schema or data provider/i)).toHaveCount(0);
  await expect(page.getByText(/bootstrap-error|home-error|landing-error/i)).toHaveCount(0);
  await expect(page.locator("main").getByRole("heading").first()).toBeVisible();

  const firstListResource = adminResources[0];
  await page.goto(`/app/#/${firstListResource.name}`);
  await expect(page.getByText(/not found/i)).toHaveCount(0);
  await expect(page.getByText(/either you typed a wrong url/i)).toHaveCount(0);

  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});

test("generated relationship surfaces resolve through a show-tab path", async ({
  page,
  request,
}) => {
  const adminResources = await loadAdminResources(request);
  const candidate = await findRelationshipSmokeCandidate(page, request, adminResources);

  await page.goto(candidate.showPath);
  const relationshipTab = page.getByRole("tab", { name: new RegExp(candidate.tabLabel, "i") });
  await expect(relationshipTab).toBeVisible();
  await relationshipTab.click();
  await expect(relationshipTab).toHaveAttribute("aria-selected", "true");
  await expect(page.getByText(/no related record/i)).toHaveCount(0);
  await expect(page.getByText(/no related records/i)).toHaveCount(0);
});

test("generated entry surface remains usable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/");

  await expect.poll(() => page.url()).toContain("/app/#/");
  await expect(page.getByText(/failed to initialize the schema or data provider/i)).toHaveCount(0);
  await expect(page.locator("main").getByRole("heading").first()).toBeVisible();
});
