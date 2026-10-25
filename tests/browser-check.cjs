// Optional development-only verification. The application has no Node dependency.
// Install: npm install --prefix .tools --no-save --no-package-lock playwright
// Start the app separately, then run: node tests/browser-check.cjs
// Requires an installed Google Chrome browser.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("../.tools/node_modules/playwright");

(async () => {
  const base = process.env.CAFE_TEST_URL || "http://127.0.0.1:8080";
  const output = path.resolve(__dirname, "../.tools/browser-results");
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    const requests = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });
    page.on("request", (request) => requests.push(request.url()));
    const response = await page.goto(base);
    assert.equal(response.status(), 200);
    assert.match(response.headers()["cache-control"], /no-store/);
    await page.waitForLoadState("networkidle");
    assert.equal(await page.locator(".menu-card:visible").count(), 8);
    assert.ok((await page.locator("#server-name").textContent()).trim());
    assert.equal(await page.locator("#app-version").textContent(), "1.0");
    await page.screenshot({ path: path.join(output, "desktop.png"), fullPage: true });

    const beforeFiltering = requests.length;
    for (const [category, count] of [["Coffee", 3], ["Tea", 2], ["Snacks", 3], ["All", 8]]) {
      await page.getByRole("button", { name: category, exact: true }).click();
      assert.equal(await page.locator(".menu-card:visible").count(), count);
      assert.equal(await page.locator('[aria-pressed="true"]').count(), 1);
      assert.equal(await page.getByRole("button", { name: category, exact: true }).getAttribute("aria-pressed"), "true");
      assert.match(await page.locator("#menu-count").textContent(), new RegExp(`^${count} items`));
      if (category !== "All") {
        assert.deepEqual(await page.locator(".menu-card:visible").evaluateAll((cards) => [...new Set(cards.map((card) => card.dataset.category))]), [category]);
      }
    }
    assert.equal(requests.length, beforeFiltering, "Filtering must not fetch or reload anything");

    const tea = page.getByRole("button", { name: "Tea", exact: true });
    await tea.focus();
    await page.keyboard.press("Enter");
    assert.equal(await page.locator(".menu-card:visible").count(), 2);
    const beforeReload = requests.filter((url) => url === `${base}/`).length;
    await Promise.all([
      page.waitForNavigation(),
      page.getByRole("button", { name: "Reload page", exact: true }).click(),
    ]);
    assert.ok(requests.filter((url) => new URL(url).pathname === "/").length > beforeReload);
    assert.equal(await page.locator(".menu-card:visible").count(), 8);

    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(base);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, "Mobile page must not overflow horizontally");
    for (const [category, count] of [["Coffee", 3], ["Tea", 2], ["Snacks", 3], ["All", 8]]) {
      const button = page.getByRole("button", { name: category, exact: true });
      await button.click();
      assert.equal(await page.locator(".menu-card:visible").count(), count);
      const box = await button.boundingBox();
      assert.ok(box.height >= 44, "Touch targets need a usable height");
    }
    await page.screenshot({ path: path.join(output, "mobile.png"), fullPage: true });

    const health = await page.request.get(`${base}/health`);
    assert.equal(health.status(), 200);
    assert.equal(await health.text(), "OK");
    assert.match(health.headers()["content-type"], /^text\/plain/);
    assert.ok(requests.every((url) => url.startsWith(base)), "All resources must be local");
    assert.deepEqual(errors, [], "No browser errors or failed HTTP responses");

    const noJs = await browser.newContext({ javaScriptEnabled: false });
    const plainPage = await noJs.newPage();
    await plainPage.goto(base);
    assert.equal(await plainPage.locator(".menu-card:visible").count(), 8);
    assert.equal(await plainPage.locator(".filters:visible").count(), 0);
    await noJs.close();
    console.log("PASS: desktop/mobile filters, counts, keyboard, no filter requests, real reload, no overflow, local assets, health, no-JavaScript fallback, and no browser errors.");
    console.log(`Screenshots: ${output}`);
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
