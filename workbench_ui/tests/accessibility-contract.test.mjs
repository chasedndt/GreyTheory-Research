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

test("desktop hides the mobile trigger while the mobile breakpoint restores it", () => {
  assert.match(styles, /\.icon-button\.mobile-menu\{display:none\}/);
  assert.match(styles, /@media\(max-width:760px\)\{[\s\S]*\.icon-button\.mobile-menu\{display:grid\}/);
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

test("mobile boundary footer follows content instead of obscuring panels", () => {
  assert.match(styles, /@media\(max-width:760px\)\{[\s\S]*\.workspace\{[^}]*padding-bottom:0\}/);
  assert.match(styles, /@media\(max-width:760px\)\{[\s\S]*\.global-footer\{position:static;/);
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

test("case views implement roving keyboard tabs and labelled tab panels", () => {
  assert.match(appSource, /if \(event\.key === "ArrowRight"\)/);
  assert.match(appSource, /else if \(event\.key === "ArrowLeft"\)/);
  assert.match(appSource, /else if \(event\.key === "Home"\)/);
  assert.match(appSource, /else if \(event\.key === "End"\)/);
  assert.match(appSource, /aria-controls="case-panel-canvas"[\s\S]*tabIndex=\{mode === "canvas" \? 0 : -1\}/);
  assert.match(appSource, /id=\{`case-panel-\$\{mode\}`\} role="tabpanel" aria-labelledby=\{`case-tab-\$\{mode\}`\} tabIndex=\{0\}/);
});

test("truthful preview actions expose their state to assistive technology", () => {
  assert.match(appSource, /disabled aria-label="Evidence export is disabled in the research preview"/);
  assert.match(appSource, /role="status" aria-live="polite"/);
  assert.match(appSource, /Preview review packet/);
  assert.match(appSource, /No file was exported, no reviewer was contacted, and no approval was granted\./);
  assert.match(appSource, /aria-label="Open local learner profile"/);
});
