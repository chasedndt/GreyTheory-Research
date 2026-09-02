import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const appSource = await readFile(new URL("../src/App.jsx", import.meta.url), "utf8");
const styles = await readFile(new URL("../src/styles.css", import.meta.url), "utf8");

test("navigation moves focus to the named workspace without forced motion", () => {
  assert.match(appSource, /const workspaceRef = useRef\(null\)/);
  assert.match(appSource, /prefers-reduced-motion: reduce/);
  assert.match(appSource, /workspaceRef\.current\?\.focus\(\{ preventScroll: true \}\)/);
  assert.match(appSource, /<main ref=\{workspaceRef\} id="workspace-main"[^>]+tabIndex="-1"[^>]+aria-label=\{currentNav\.label\}/);
});

test("skip navigation and current-page semantics stay explicit", () => {
  assert.match(appSource, /<a className="skip-link" href="#workspace-main">Skip to workspace<\/a>/);
  assert.match(appSource, /aria-label=\{label\} title=\{label\} aria-current=/);
  assert.match(appSource, /aria-current=\{active === id \? "page" : undefined\}/);
  assert.match(styles, /\.workspace:focus-visible\{outline:2px solid var\(--blue\)/);
});

test("closed mobile navigation leaves the keyboard and accessibility trees", () => {
  assert.match(appSource, /inert=\{isMobile && !mobileNav\}/);
  assert.match(appSource, /aria-hidden=\{isMobile && !mobileNav \? "true" : undefined\}/);
  assert.match(appSource, /aria-expanded=\{mobileNav\} aria-controls="primary-sidebar"/);
});

test("mobile navigation owns focus while open and restores its trigger", () => {
  assert.match(appSource, /mobileNavCloseRef\.current\?\.focus\(\)/);
  assert.match(appSource, /if \(event\.key === "Escape"\)/);
  assert.match(appSource, /focusable\[0\]/);
  assert.match(appSource, /focusable\[focusable\.length - 1\]/);
  assert.match(appSource, /mobileMenuRef\.current\)\?\.focus\(\)/);
});

test("navigation scrollbar stays visible and uses the mission-control palette", () => {
  assert.match(styles, /--scrollbar-track:#071321/);
  assert.match(styles, /--scrollbar-thumb:#3a536b/);
  assert.match(styles, /html\{[^}]*scrollbar-width:thin;scrollbar-color:var\(--scrollbar-thumb\) #030a12\}/);
  assert.match(styles, /\.sidebar nav\{[\s\S]*scrollbar-gutter:stable;[\s\S]*scrollbar-width:thin;[\s\S]*scrollbar-color:var\(--scrollbar-thumb\) var\(--scrollbar-track\)/);
  assert.match(styles, /\.sidebar nav::-webkit-scrollbar-thumb\{[\s\S]*border-radius:999px;[\s\S]*background:var\(--scrollbar-thumb\)/);
  assert.match(styles, /\.sidebar nav::-webkit-scrollbar-thumb:active\{background:var\(--amber\)\}/);
  assert.doesNotMatch(styles, /\.sidebar nav[^}]*scrollbar-width:none/);
});

test("modal retains escape close and a bounded focus loop", () => {
  assert.match(appSource, /if \(event\.key === "Escape"\) onClose\(\)/);
  assert.match(appSource, /focusable\[0\]/);
  assert.match(appSource, /focusable\[focusable\.length - 1\]/);
});

test("guided learning exposes accessible mission stages and scenario checks", () => {
  assert.match(appSource, /aria-labelledby="mission-plan-title"/);
  assert.match(appSource, /aria-label="Mission stages"/);
  assert.match(appSource, /<fieldset key=\{item\.question\}>/);
  assert.match(appSource, /<legend>\{checkIndex \+ 1\}\. \{item\.question\}<\/legend>/);
  assert.match(appSource, /disabled=\{!labReady\}/);
  assert.match(appSource, /This unlocks practice only; it does not award mastery\./);
});
