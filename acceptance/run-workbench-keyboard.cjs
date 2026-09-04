const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

function argument(name, fallback = "") {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

const baseUrl = argument("--base-url");
const evidenceDir = path.resolve(argument("--evidence-dir", path.join(process.cwd(), "keyboard-evidence")));
const screenshotDir = path.resolve(argument("--screenshot-dir", path.join(evidenceDir, "screenshots")));
if (!/^http:\/\/127\.0\.0\.1:\d+\/?$/.test(baseUrl)) {
  throw new Error("--base-url must be an HTTP numeric-loopback URL such as http://127.0.0.1:4173/");
}

fs.mkdirSync(evidenceDir, { recursive: true });
fs.mkdirSync(screenshotDir, { recursive: true });

const routes = [
  "Mission Control",
  "Learn",
  "Safe Lab",
  "Programmes",
  "Cases",
  "Hypotheses",
  "Intelligence",
  "Evidence",
  "Reports",
  "Readiness",
  "Demo Suite",
  "Library",
  "Settings",
];

const result = {
  schema: "greytheory.workbench-keyboard-acceptance.v1",
  generatedAt: new Date().toISOString(),
  baseUrl,
  posture: "LOCAL_FIXTURE",
  targetContacted: false,
  checks: [],
  routeTraversal: [],
  screenshots: [],
  consoleErrors: [],
  accepted: false,
};

async function activeDescriptor(page) {
  return page.evaluate(() => {
    const active = document.activeElement;
    return {
      tag: active?.tagName || "",
      role: active?.getAttribute?.("role") || "",
      name: active?.getAttribute?.("aria-label") || active?.textContent?.replace(/\s+/g, " ").trim() || "",
      id: active?.id || "",
    };
  });
}

async function check(name, action) {
  try {
    const detail = await action();
    result.checks.push({ name, passed: true, detail: detail || "passed" });
  } catch (error) {
    result.checks.push({ name, passed: false, detail: error instanceof Error ? error.message : String(error) });
    throw error;
  }
}

async function screenshot(page, filename, fullPage = true) {
  const outputPath = path.join(screenshotDir, filename);
  await page.screenshot({ path: outputPath, fullPage });
  result.screenshots.push(outputPath);
}

async function openFirstEntry(page) {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.evaluate(() => window.scrollTo(0, 0));
}

async function tabToName(page, expectedName, maximum = 32) {
  const visited = [];
  for (let index = 0; index < maximum; index += 1) {
    await page.keyboard.press("Tab");
    const active = await activeDescriptor(page);
    visited.push(active.name);
    if (active.name === expectedName) return visited;
  }
  throw new Error(`Could not reach ${expectedName}; visited: ${visited.join(" -> ")}`);
}

async function activateRouteFromFirstEntry(page, label, capture = false) {
  await openFirstEntry(page);
  const visited = await tabToName(page, label);
  await page.keyboard.press("Enter");
  await page.waitForFunction((name) => {
    const active = document.activeElement;
    return active?.id === "workspace-main" && active.getAttribute("aria-label") === name;
  }, label);
  const focused = await activeDescriptor(page);
  result.routeTraversal.push({ label, visited, focused });
  if (capture) {
    const slug = label.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    await screenshot(page, `route-${slug}.png`);
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") result.consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => result.consoleErrors.push(error.message));

  try {
    await check("first Tab exposes skip navigation and Enter focuses the workspace", async () => {
      await openFirstEntry(page);
      await screenshot(page, "01-desktop-first-entry.png");
      await page.keyboard.press("Tab");
      assert.equal((await activeDescriptor(page)).name, "Skip to workspace");
      await screenshot(page, "02-desktop-skip-link.png", false);
      await page.keyboard.press("Enter");
      assert.equal((await activeDescriptor(page)).id, "workspace-main");
      await screenshot(page, "03-desktop-workspace-focus.png");
      return "Skip link is the first Tab stop and transfers focus to Mission Control.";
    });

    await check("desktop hides the mobile-only navigation trigger", async () => {
      await openFirstEntry(page);
      const display = await page.locator('button[aria-label="Open navigation"]').evaluate((node) => getComputedStyle(node).display);
      assert.equal(display, "none");
      return "Open navigation is display:none above the mobile breakpoint.";
    });

    await check("all primary routes are keyboard reachable and receive named main focus", async () => {
      for (const label of routes) await activateRouteFromFirstEntry(page, label, true);
      return `${routes.length} routes reached from first entry.`;
    });

    await check("Cases implements arrow-key tab selection and labelled panels", async () => {
      await activateRouteFromFirstEntry(page, "Cases");
      const canvas = page.getByRole("tab", { name: "Case canvas" });
      await canvas.focus();
      await screenshot(page, "04-cases-canvas-tab.png");
      await page.keyboard.press("ArrowRight");
      const ledger = page.getByRole("tab", { name: "Research ledger" });
      assert.equal(await ledger.getAttribute("aria-selected"), "true");
      assert.equal((await activeDescriptor(page)).name, "Research ledger");
      const panel = page.getByRole("tabpanel");
      assert.equal(await panel.getAttribute("aria-labelledby"), "case-tab-ledger");
      await screenshot(page, "05-cases-ledger-tab.png");
      await page.keyboard.press("Home");
      assert.equal((await activeDescriptor(page)).name, "Case canvas");
      await page.keyboard.press("End");
      assert.equal((await activeDescriptor(page)).name, "Research ledger");
      return "ArrowRight, Home, and End move selection and focus with roving tabindex.";
    });

    await check("connection dialog traps focus and restores its trigger", async () => {
      await openFirstEntry(page);
      await page.keyboard.press("Tab");
      await page.keyboard.press("Tab");
      assert.match((await activeDescriptor(page)).name, /LOCAL_FIXTURE/);
      await page.keyboard.press("Enter");
      assert.equal((await activeDescriptor(page)).name, "Close");
      await page.keyboard.press("Shift+Tab");
      assert.equal((await activeDescriptor(page)).name, "Connect securely");
      await page.keyboard.press("Tab");
      assert.equal((await activeDescriptor(page)).name, "Close");
      await screenshot(page, "06-connection-dialog-keyboard.png", false);
      await page.keyboard.press("Escape");
      assert.match((await activeDescriptor(page)).name, /LOCAL_FIXTURE/);
      return "Dialog focus wraps in both directions and Escape restores the safety control.";
    });

    await check("Readiness completes a truthful local review-packet preview", async () => {
      await activateRouteFromFirstEntry(page, "Readiness");
      const question = await page.locator(".assessment>p").textContent();
      const answer = question.includes("webpage tells an agent") ? "deny" : "bola";
      const radio = page.locator(`input[type=radio][value=${answer}]`);
      await radio.focus();
      await page.keyboard.press("Space");
      const checkButton = page.getByRole("button", { name: "Check reasoning" });
      await checkButton.focus();
      await page.keyboard.press("Enter");
      await page.getByRole("status").filter({ hasText: /Correct\.|Evidence kept in bounds|Defensible decision/ }).waitFor();
      const packetButton = page.getByRole("button", { name: "Preview review packet" });
      assert.equal(await packetButton.isEnabled(), true);
      await packetButton.focus();
      await page.keyboard.press("Enter");
      await page.getByRole("status").filter({ hasText: "No file was exported" }).waitFor();
      await screenshot(page, "07-readiness-packet-preview.png");
      return "Correct reasoning unlocks a local-only checklist; no export, review, or approval is claimed.";
    });

    await check("no element uses a positive tabindex", async () => {
      const offenders = await page.locator("[tabindex]").evaluateAll((nodes) => nodes.filter((node) => Number(node.getAttribute("tabindex")) > 0).map((node) => node.outerHTML));
      assert.deepEqual(offenders, []);
      return "No positive tabindex values found.";
    });

    await check("mobile drawer owns focus, closes on route selection, and hands focus to Learn", async () => {
      const mobile = await context.newPage();
      await mobile.setViewportSize({ width: 390, height: 844 });
      await mobile.goto(baseUrl, { waitUntil: "networkidle" });
      await screenshot(mobile, "08-mobile-first-entry.png", false);
      await mobile.keyboard.press("Tab");
      assert.equal((await activeDescriptor(mobile)).name, "Skip to workspace");
      await mobile.keyboard.press("Tab");
      assert.equal((await activeDescriptor(mobile)).name, "Open navigation");
      await mobile.keyboard.press("Enter");
      assert.equal((await activeDescriptor(mobile)).name, "Close navigation");
      await mobile.waitForTimeout(250);
      await screenshot(mobile, "09-mobile-drawer-open.png", false);
      await mobile.keyboard.press("Shift+Tab");
      assert.equal((await activeDescriptor(mobile)).name, "Settings");
      await mobile.keyboard.press("Tab");
      assert.equal((await activeDescriptor(mobile)).name, "Close navigation");
      await mobile.keyboard.press("Tab");
      assert.equal((await activeDescriptor(mobile)).name, "Mission Control");
      await mobile.keyboard.press("Tab");
      assert.equal((await activeDescriptor(mobile)).name, "Learn");
      await mobile.keyboard.press("Enter");
      await mobile.waitForFunction(() => document.activeElement?.id === "workspace-main" && document.activeElement.getAttribute("aria-label") === "Learn");
      const drawer = mobile.locator("#primary-sidebar");
      assert.equal(await drawer.getAttribute("inert"), "");
      assert.equal(await drawer.getAttribute("aria-hidden"), "true");
      await screenshot(mobile, "10-mobile-learn-focus.png", false);
      await mobile.close();
      return "Drawer loops focus, becomes inert when closed, and moves focus to the selected workspace.";
    });

    await check("browser console stays free of errors", async () => {
      assert.deepEqual(result.consoleErrors, []);
      return "No console or page errors captured.";
    });

    result.accepted = result.checks.every((item) => item.passed);
  } catch (error) {
    result.failure = error instanceof Error ? error.stack : String(error);
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(evidenceDir, "acceptance.json"), `${JSON.stringify(result, null, 2)}\n`, "utf8");
  }

  if (!result.accepted) process.exitCode = 1;
})();
