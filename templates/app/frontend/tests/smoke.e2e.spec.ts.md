# `frontend/tests/smoke.e2e.spec.ts`

See also:

- [../../../../specs/contracts/frontend/validation.md](../../../../specs/contracts/frontend/validation.md)
- [../playwright.config.ts.md](../playwright.config.ts.md)

This is the minimum browser-level smoke gate for the starter app.

For a non-starter domain, replace the starter resource names and visible seed
data with the values declared in:

- `../../../../runs/current/artifacts/architecture/resource-naming.md`
- `../../../../runs/current/artifacts/product/sample-data.md`
- `../../../../runs/current/artifacts/ux/navigation.md`

```ts
import { expect, test } from "@playwright/test";

test("starter app smoke flow works", async ({ page, request }) => {
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

  const collectionResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/api/collections") && response.status() === 200,
  );

  await page.goto("/admin-app/#/Home");
  await collectionResponsePromise;

  await expect(
    page.getByText(/failed to initialize the schema or data provider/i),
  ).toHaveCount(0);
  await expect(page.getByText(/home/i)).toBeVisible();

  const homeMenuLink = page.getByRole("link", { name: /home/i });
  await expect(homeMenuLink).toBeVisible();

  await page.goto("/admin-app/#/Landing");
  await expect(page.getByText(/landing error/i)).toHaveCount(0);

  await page.goto("/admin-app/#/Collection");
  await expect(page.getByText("Spring Planning")).toBeVisible();

  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(failedResponses).toEqual([]);
});
```

Notes:

- If the generated app relies on sparse or incomplete normalized relationship
  metadata, extend this smoke suite to prove at least one fallback-driven
  `tomany` relationship tab loads rows and at least one `toone` relationship
  opens the related-record dialog.
- The sparse relationship scenario SHOULD use the same domain/resource names
  documented in the app's own run-owned architecture and UX artifacts rather
  than hardcoding the starter `Collection` example.
