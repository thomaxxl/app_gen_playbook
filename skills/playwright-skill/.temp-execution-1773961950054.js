
(async () => {
  try {
    const { chromium } = require('playwright');

const TARGET_URL = process.env.TARGET_URL || 'http://127.0.0.1:5180/app/';

const forbiddenCopy = [
  'route inventory',
  'recovery copy',
  'contract recovery',
  'starter admin shell',
  'debug copy',
];

function attachCollectors(page, bucket) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      bucket.consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', (error) => {
    bucket.pageErrors.push(error.message);
  });
  page.on('requestfailed', (request) => {
    bucket.failedRequests.push(`${request.method()} ${request.url()} :: ${request.failure()?.errorText || 'unknown failure'}`);
  });
  page.on('request', (request) => {
    const url = request.url();
    if (url.includes('favicon') || url.includes('/assets/')) {
      bucket.assetRequests.push(url);
    }
  });
  page.on('response', (response) => {
    const url = response.url();
    if ((url.includes('favicon') || url.includes('/assets/')) && response.status() >= 400) {
      bucket.assetHttpErrors.push(`${response.status()} ${url}`);
    }
  });
}

async function assertNoForbiddenCopy(page) {
  const bodyText = (await page.locator('body').innerText()).toLowerCase();
  const hits = forbiddenCopy.filter((term) => bodyText.includes(term));
  if (hits.length) {
    throw new Error(`Forbidden internal/debug copy found: ${hits.join(', ')}`);
  }
}

async function run() {
  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const results = {
    consoleErrors: [],
    pageErrors: [],
    failedRequests: [],
    assetRequests: [],
    assetHttpErrors: [],
    iconHrefs: [],
  };

  try {
    const desktopContext = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
    const desktopPage = await desktopContext.newPage();
    attachCollectors(desktopPage, results);

    await desktopPage.goto(`${TARGET_URL}#/Home`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await desktopPage.locator('h1:has-text("Delivery Overview")').waitFor({ timeout: 15000 });
    await desktopPage.getByTestId('entry-primary-cta').waitFor({ timeout: 10000 });
    await desktopPage.locator('text=Portfolio readiness').waitFor({ timeout: 10000 });
    results.iconHrefs.push(await desktopPage.evaluate(() => document.querySelector('link[rel~="icon"]')?.getAttribute('href') || null));
    await assertNoForbiddenCopy(desktopPage);
    await desktopPage.screenshot({ path: '/tmp/qa-console-home-desktop.png', fullPage: true });

    await desktopPage.getByTestId('entry-primary-cta').click();
    await desktopPage.waitForURL('**#/Collection', { timeout: 15000 });
    await desktopPage.locator('text=Projects').waitFor({ timeout: 10000 });
    await desktopPage.locator('text=Alpha Program').waitFor({ timeout: 10000 });
    results.iconHrefs.push(await desktopPage.evaluate(() => document.querySelector('link[rel~="icon"]')?.getAttribute('href') || null));
    await assertNoForbiddenCopy(desktopPage);
    await desktopPage.screenshot({ path: '/tmp/qa-console-collection.png', fullPage: true });
    await desktopContext.close();

    const mobileContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const mobilePage = await mobileContext.newPage();
    attachCollectors(mobilePage, results);

    await mobilePage.goto(`${TARGET_URL}#/Home`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await mobilePage.locator('h1:has-text("Delivery Overview")').waitFor({ timeout: 15000 });
    await mobilePage.getByTestId('entry-primary-cta').waitFor({ timeout: 10000 });
    results.iconHrefs.push(await mobilePage.evaluate(() => document.querySelector('link[rel~="icon"]')?.getAttribute('href') || null));
    await assertNoForbiddenCopy(mobilePage);
    await mobilePage.screenshot({ path: '/tmp/qa-console-home-mobile.png', fullPage: true });
    await mobileContext.close();

    if (results.consoleErrors.length || results.pageErrors.length || results.failedRequests.length || results.assetHttpErrors.length) {
      throw new Error(JSON.stringify(results, null, 2));
    }

    console.log(JSON.stringify({
      decision: 'pass',
      targetUrl: TARGET_URL,
      iconHrefs: results.iconHrefs,
      assetRequests: results.assetRequests,
      screenshots: [
        '/tmp/qa-console-home-desktop.png',
        '/tmp/qa-console-collection.png',
        '/tmp/qa-console-home-mobile.png',
      ],
    }, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});

  } catch (error) {
    console.error('❌ Automation error:', error.message);
    if (error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
})();
