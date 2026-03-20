import { expect, test } from "@playwright/test";

test("starter app smoke flow works", async ({ page, request }) => {
  const landingRoute: string | null = null;
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

  const adminYamlResponse = await request.get("http://127.0.0.1:5173/ui/admin/admin.yaml");
  expect(adminYamlResponse.status()).toBe(200);

  const runResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/api/runs") && response.status() === 200,
  );

  await page.goto("/app/#/Home");
  await runResponsePromise;

  await expect(
    page.getByText(/failed to initialize the schema or data provider/i),
  ).toHaveCount(0);
  await expect(page.getByText(/run overview/i)).toBeVisible();
  await expect(page.getByTestId("entry-purpose")).toBeVisible();
  await expect(page.getByTestId("entry-primary-cta")).toBeVisible();
  await expect(page.getByTestId("entry-proof-strip")).toBeVisible();

  const homeMenuLink = page.getByRole("link", { name: /run overview/i });
  await expect(homeMenuLink).toBeVisible();

  if (landingRoute) {
    await page.goto(landingRoute);
    await expect(page.getByText(/landing error/i)).toHaveCount(0);
  }

  await page.goto("/app/#/phases");
  await expect(
    page.getByText(/phases/i).first(),
  ).toBeVisible();

  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});

test("entry page remains discoverable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/app/#/Home");

  await expect(page.getByTestId("entry-purpose")).toBeVisible();
  await expect(page.getByTestId("entry-primary-cta")).toBeVisible();
});
