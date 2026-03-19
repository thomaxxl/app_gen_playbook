import { expect, test } from "@playwright/test";

test("cmdb smoke flow works", async ({ page, request }) => {
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

  const itemResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/configuration_items") && response.status() === 200,
  );

  await page.goto("/app/#/Home");
  await itemResponsePromise;

  await expect(
    page.getByText(/failed to initialize the schema or data provider/i),
  ).toHaveCount(0);
  await expect(page.getByRole("link", { name: /home/i })).toBeVisible();
  await expect(page.getByText(/cmdb operations console/i)).toBeVisible();

  await page.goto("/app/#/Landing");
  await expect(page.getByText(/dashboard unavailable/i)).toHaveCount(0);

  await page.goto("/app/#/Service");
  await expect(page.getByText("COMMERCE")).toBeVisible();

  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});
