import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const appSource = await readFile(new URL("../src/App.jsx", import.meta.url), "utf8");
const styles = await readFile(new URL("../src/styles.css", import.meta.url), "utf8");
// The guided-learning surface moved out of App.jsx: the old Learn page asked
// questions before it taught anything, so it was replaced by an ordered
// curriculum that opens the real lessons. These are read so the accessibility
// properties it used to guard are still guarded, at their new addresses.
const curriculumSource = await readFile(new URL("../src/CurriculumView.jsx", import.meta.url), "utf8");
const lessonSource = await readFile(new URL("../src/LessonDialog.jsx", import.meta.url), "utf8");

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

test("the curriculum exposes its tracks and ordered steps to assistive technology", () => {
  // Each track is a labelled region, and its lessons are an ordered list that
  // announces which track it belongs to - so the path is navigable without
  // seeing the layout that conveys it visually.
  assert.match(curriculumSource, /aria-labelledby=\{`track-\$\{track\.id\}`\}/);
  assert.match(curriculumSource, /aria-label=\{`\$\{track\.title\} lessons in order`\}/);
  assert.match(curriculumSource, /aria-labelledby="next-title"/);
});

test("practice stays gated behind having read something, and says so", () => {
  // This gate moved off the old Learn page rather than being dropped: it also
  // carries the guided journey from its learn stage into practise.
  assert.match(curriculumSource, /const labReady = /);
  assert.match(curriculumSource, /disabled=\{!labReady\}/);
  assert.match(curriculumSource, /This unlocks practice only; it does not award mastery\./);
});

test("lesson checks group their options and announce every response", () => {
  // Replaces the old fieldset/legend assertions. The property being protected
  // is that questions are grouped and every reaction reaches a screen reader -
  // a labelled group with live regions serves that better than a fieldset did.
  assert.match(lessonSource, /role="group" aria-label="Answer options"/);
  assert.match(lessonSource, /aria-pressed=\{isChosen\}/);
  assert.match(lessonSource, /className="lesson-hints" aria-live="polite"/);
  assert.match(lessonSource, /lesson-verdict\$\{verdict\.correct \? " is-correct" : " is-wrong"\}`} aria-live="polite"/);
});

test("a wrong answer buys a hint and never the answer", () => {
  // The rule that makes the number of attempts an honest signal.
  assert.match(lessonSource, /A wrong answer unlocks a hint, never the answer\./);
  assert.match(lessonSource, /setHintsShown\(\(current\) => Math\.min\(current \+ 1/);
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

test("governed coach exposes its data and authority boundaries in every mode", () => {
  assert.match(appSource, /Public learning context only/);
  assert.match(appSource, /Do not paste credentials, tokens, private programme data, target URLs, or captures/);
  assert.match(appSource, /kind: "request_coach_guidance"/);
  assert.match(appSource, /data_class: "PUBLIC"/);
  assert.match(appSource, /humanAcknowledged: true/);
  assert.match(appSource, /className="coach-launch" aria-label="Open AI research coach"/);
  assert.match(appSource, /Guidance is inferred and cannot perform actions or award mastery/);
  assert.match(appSource, /kind: "clear_coach_history"/);
  assert.match(appSource, /aria-label=\{confirmClear \? "Confirm clearing coach history" : "Clear coach history"\}/);
  assert.match(appSource, /Research, evidence, and mastery were unchanged/);
  assert.match(appSource, /aria-live="polite"/);
  assert.match(styles, /\.modal--coach\{width:min\(880px,100%\);overflow:hidden\}/);
  assert.match(styles, /\.coach-provenance\{display:grid/);
  assert.match(styles, /\.coach-history-bar\{display:flex/);
});
