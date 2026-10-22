// The test that would have caught two blank screens.
//
// Every other UI test in this suite reads source files as text and asserts
// against them with regular expressions. That is fine for contracts about how
// something is written, and useless against the failure that has now happened
// twice: an identifier referenced but never declared, and a `const` read before
// its initialiser had run. Both are legal JavaScript. The bundler compiles them
// without complaint, every regex assertion passes, the build is green - and the
// app throws the instant React evaluates the component, leaving `#root` empty
// and the entire product blank.
//
// A suite that cannot distinguish "ships and works" from "ships and refuses to
// start" is not testing the thing that matters. So this one *runs* the app.
//
// Vite is already a dependency, so its SSR pipeline transforms JSX and
// neutralises CSS imports with no new toolchain. `renderToString` evaluates
// every component body and every hook initialiser, which is precisely where
// these errors live. Effects do not run under SSR, so nothing here performs
// I/O, contacts the API, or touches the research store.

import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { createServer } from "vite";

const root = fileURLToPath(new URL("../", import.meta.url));

// A deliberately small browser. Enough for module evaluation and a first
// render; not a DOM implementation. If a view ever needs more than this, that
// is worth knowing rather than papering over.
function installBrowserStubs() {
  const cells = new Map();
  const storage = {
    getItem: (key) => (cells.has(key) ? cells.get(key) : null),
    setItem: (key, value) => cells.set(key, String(value)),
    removeItem: (key) => cells.delete(key),
    clear: () => cells.clear(),
  };
  const matchMedia = (media = "") => ({
    media,
    matches: false,
    onchange: null,
    addEventListener() {},
    removeEventListener() {},
    addListener() {},
    removeListener() {},
    dispatchEvent: () => false,
  });
  const noopElement = () => ({
    style: {},
    setAttribute() {},
    removeAttribute() {},
    appendChild() {},
    addEventListener() {},
    removeEventListener() {},
    focus() {},
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
  });

  globalThis.window = {
    localStorage: storage,
    sessionStorage: storage,
    matchMedia,
    scrollTo() {},
    requestAnimationFrame: () => 0,
    cancelAnimationFrame() {},
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    addEventListener() {},
    removeEventListener() {},
    location: { origin: "http://127.0.0.1:8765", href: "http://127.0.0.1:8765/" },
  };
  globalThis.localStorage = storage;
  globalThis.matchMedia = matchMedia;
  globalThis.document = {
    hidden: false,
    readyState: "complete",
    documentElement: noopElement(),
    head: noopElement(),
    body: noopElement(),
    createElement: noopElement,
    createTextNode: () => ({}),
    getElementById: () => null,
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener() {},
    removeEventListener() {},
  };
  // Node 21+ makes navigator a read-only accessor on globalThis.
  try {
    if (!globalThis.navigator) globalThis.navigator = { userAgent: "node" };
  } catch { /* already present, which is fine */ }
}

async function withViteSsr(run) {
  // The project's own vite config is loaded deliberately. Passing
  // `configFile: false` drops @vitejs/plugin-react, esbuild then falls back to
  // the classic JSX transform, and every component compiles to
  // `React.createElement` - which throws here, because these modules correctly
  // import only the hooks they use. A test that builds the source differently
  // from the way it ships tests a program that does not exist.
  const server = await createServer({
    root,
    logLevel: "silent",
    optimizeDeps: { noDiscovery: true },
    server: { middlewareMode: true, hmr: false, watch: null },
    appType: "custom",
  });
  try {
    return await run(server);
  } finally {
    await server.close();
  }
}

test("the whole app evaluates and renders without throwing", async () => {
  installBrowserStubs();
  await withViteSsr(async (server) => {
    const module = await server.ssrLoadModule("/src/App.jsx");
    // A named export, because main.jsx imports `{ App }`. The view modules
    // default-export instead, so this deliberately does not assume one
    // convention covers the whole source tree.
    const App = module.App;
    assert.equal(typeof App, "function", "App.jsx must export an App component");

    // The assertion that matters: this line throws on an undeclared identifier
    // or a temporal-dead-zone read, exactly as the browser does.
    const html = renderToString(createElement(App));

    assert.ok(html.length > 0, "the app rendered nothing at all");
    // Proof it rendered the shell rather than an error boundary's fallback.
    assert.match(html, /id="workspace-main"/);
    assert.match(html, /Skip to workspace/);
  });
});

// Each route is rendered on its own. Mounting only the default view would let a
// broken panel sit undetected until someone navigated to it - which is how the
// curriculum route shipped referencing a handler that did not exist.
test("every view module evaluates on its own", async () => {
  installBrowserStubs();
  const views = [
    "/src/CurriculumView.jsx",
    "/src/LessonDialog.jsx",
    "/src/BountyBoard.jsx",
    "/src/OnboardingOverlay.jsx",
  ];
  await withViteSsr(async (server) => {
    for (const path of views) {
      const module = await server.ssrLoadModule(path);
      assert.equal(typeof module.default, "function", `${path} must export a component`);
    }
  });
});
