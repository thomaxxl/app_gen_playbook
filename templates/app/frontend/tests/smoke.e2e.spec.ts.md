# `frontend/tests/smoke.e2e.spec.ts`

```ts
import { expect, test } from "@playwright/test";
import type { APIRequestContext, Locator, Page } from "@playwright/test";

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

type RelationshipDialogCandidate = {
  label: string;
  linkTestId: string;
  path: string;
  resourceName: string;
};

type RelationshipTabCandidate = {
  fetchSource: string;
  path: string;
  resourceName: string;
  routePath: string;
  tabLabel: string;
};

function collectFrontendErrors(page: Page) {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedResponses: string[] = [];
  const apiResponses: string[] = [];

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
    if (url.startsWith("http://127.0.0.1:5656")) {
      apiResponses.push(url);
    }
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${url}`);
    }
  });

  return { apiResponses, consoleErrors, failedResponses, pageErrors };
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

async function assertBasicPageHealth(page: Page) {
  await expect(page.getByText(/not found/i)).toHaveCount(0);
  await expect(page.getByText(/either you typed a wrong url/i)).toHaveCount(0);
  await expect(page.getByText(/failed to initialize the schema or data provider/i)).toHaveCount(0);
}

async function firstVisible(locator: Locator): Promise<Locator | null> {
  const count = await locator.count();
  for (let index = 0; index < count; index += 1) {
    const candidate = locator.nth(index);
    if (await candidate.isVisible()) {
      return candidate;
    }
  }
  return null;
}

async function findListRelationshipDialogCandidate(
  page: Page,
  request: APIRequestContext,
  resources: AdminResource[],
): Promise<RelationshipDialogCandidate> {
  for (const resource of resources) {
    await page.goto(`/app/#/${resource.name}`);
    await assertBasicPageHealth(page);
    const button = await firstVisible(page.locator('[data-testid^="relationship-dialog-link:list:"]'));
    if (!button) {
      continue;
    }
    const label = (await button.innerText()).trim();
    const linkTestId = await button.getAttribute("data-testid");
    if (!label || label === "-" || !linkTestId) {
      continue;
    }
    return {
      label,
      linkTestId,
      path: `/app/#/${resource.name}`,
      resourceName: resource.name,
    };
  }

  throw new Error("Could not find a generated list relationship dialog candidate.");
}

async function findSummaryRelationshipDialogCandidate(
  page: Page,
  request: APIRequestContext,
  resources: AdminResource[],
): Promise<RelationshipDialogCandidate> {
  for (const resource of resources) {
    const recordId = await loadFirstRecordId(request, resource);
    if (!recordId) {
      continue;
    }

    const path = `/app/#/${resource.name}/${recordId}/show`;
    await page.goto(path);
    await assertBasicPageHealth(page);

    const button = await firstVisible(page.locator('[data-testid^="relationship-dialog-link:summary:"]'));
    if (!button) {
      continue;
    }
    const label = (await button.innerText()).trim();
    const linkTestId = await button.getAttribute("data-testid");
    if (!label || label === "-" || !linkTestId) {
      continue;
    }
    return {
      label,
      linkTestId,
      path,
      resourceName: resource.name,
    };
  }

  throw new Error("Could not find a generated summary/show relationship dialog candidate.");
}

async function findRelationshipTabCandidate(
  page: Page,
  request: APIRequestContext,
  resources: AdminResource[],
  direction: "toone" | "tomany",
  options: {
    requireRelationshipRoute: boolean;
  },
): Promise<RelationshipTabCandidate> {
  const { requireRelationshipRoute } = options;
  let sawDirection = false;

  for (const resource of resources) {
    const recordId = await loadFirstRecordId(request, resource);
    if (!recordId) {
      continue;
    }

    const path = `/app/#/${resource.name}/${recordId}/show`;
    await page.goto(path);
    await assertBasicPageHealth(page);

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

      const panels = page.locator(`[data-testid^="relationship-tab-panel:${direction}:"]`);
      const panelCount = await panels.count();
      for (let panelIndex = 0; panelIndex < panelCount; panelIndex += 1) {
        const panel = panels.nth(panelIndex);
        if (!(await panel.isVisible())) {
          continue;
        }

        sawDirection = true;
        const fetchSource = await panel.getAttribute("data-relationship-fetch-source") ?? "";
        const routePath = await panel.getAttribute("data-relationship-route-path") ?? "";

        if (direction === "tomany") {
          const grid = panel.getByRole("grid");
          if (await grid.count() === 0 || !(await grid.first().isVisible())) {
            continue;
          }
          if (requireRelationshipRoute && fetchSource !== "relationship-route") {
            continue;
          }
        } else {
          if (await panel.getByText(/no related record/i).count() > 0) {
            continue;
          }
        }

        return {
          fetchSource,
          path,
          resourceName: resource.name,
          routePath,
          tabLabel,
        };
      }
    }
  }

  if (sawDirection && requireRelationshipRoute) {
    throw new Error(`Found ${direction} relationship tabs but none proved the canonical parent relationship lane.`);
  }

  throw new Error(`Could not find a generated ${direction} relationship tab candidate.`);
}

async function assertRelationshipDialogFlow(
  page: Page,
  candidate: RelationshipDialogCandidate,
) {
  await page.goto(candidate.path);
  await assertBasicPageHealth(page);

  const beforeUrl = page.url();
  await page.getByTestId(candidate.linkTestId).click();
  await expect(page).toHaveURL(beforeUrl);

  const dialog = page.locator('[role="dialog"]').last();
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button", { name: "EDIT" })).toBeVisible();
  await expect(dialog.getByRole("button", { name: "VIEW" })).toBeVisible();
  await expect(dialog.getByText(candidate.label)).toBeVisible();
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
  await assertBasicPageHealth(page);

  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});

test("generated relationship dialogs work from list and summary surfaces", async ({
  page,
  request,
}) => {
  const adminResources = await loadAdminResources(request);
  const listCandidate = await findListRelationshipDialogCandidate(page, request, adminResources);
  const summaryCandidate = await findSummaryRelationshipDialogCandidate(page, request, adminResources);

  await assertRelationshipDialogFlow(page, listCandidate);
  await assertRelationshipDialogFlow(page, summaryCandidate);
});

test("generated relationship tabs prove toone summary and canonical tomany route loading", async ({
  page,
  request,
}) => {
  const { apiResponses } = collectFrontendErrors(page);
  const adminResources = await loadAdminResources(request);

  const tomanyCandidate = await findRelationshipTabCandidate(page, request, adminResources, "tomany", {
    requireRelationshipRoute: true,
  });
  expect(tomanyCandidate.fetchSource).toBe("relationship-route");
  expect(tomanyCandidate.routePath).not.toBe("");
  await expect
    .poll(() => apiResponses.some((url) => url.includes(`/${tomanyCandidate.routePath}`)))
    .toBe(true);

  const tooneCandidate = await findRelationshipTabCandidate(page, request, adminResources, "toone", {
    requireRelationshipRoute: false,
  });
  expect(["embedded", "relationship-route", "id-fallback"]).toContain(tooneCandidate.fetchSource);
});

test("generated entry surface remains usable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/");

  await expect.poll(() => page.url()).toContain("/app/#/");
  await expect(page.getByText(/failed to initialize the schema or data provider/i)).toHaveCount(0);
  await expect(page.locator("main").getByRole("heading").first()).toBeVisible();
});
```

Required smoke coverage:

- this baseline MUST prove both list-surface and summary/show-surface
  relationship dialog behavior
- the dialog proof MUST verify `EDIT` and `VIEW`
- at least one `tomany` tab MUST prove `data-relationship-fetch-source`
  equals `relationship-route`
- at least one `toone` tab MUST prove related content renders through the
  generated tab runtime
- the smoke MUST stay domain-agnostic by discovering resources from
  `admin.yaml` instead of hardcoding one app's route inventory
