// Layout rules that a rendered pass caught and a source read can protect.
//
// Read this for what it is. These are assertions over CSS text, so they prove
// the rule is still written down - not that the page lays out correctly. The
// actual evidence is the measured browser pass recorded in `design-qa.md`:
// title widths, panel overflow, and tooltip bounds read from the live DOM at
// six viewport widths.
//
// The pairing is deliberate. A rendered pass finds the defect; a source
// assertion stops it silently returning when someone tidies the stylesheet.

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const styles = await readFile(new URL("../src/styles.css", import.meta.url), "utf8");

test("the mission picker drops to two columns before its titles ellipsise", () => {
  // Four across leaves each title about 29px at a 1280 viewport, which rendered
  // as "Age...", "Obj...", "Ses...". A mission you cannot read is not a mission
  // you can choose, so the layout wraps well before the collision point.
  assert.match(
    styles,
    /@media\(max-width:1560px\)\{\.mission-picker\{grid-template-columns:1fr 1fr\}/,
  );
  assert.match(
    styles,
    /@media\(max-width:1560px\)\{[^}]*\}\.mission-picker>div\{grid-column:1\/-1\}/,
  );
});

test("the picker's own columns stay flexible rather than fixed", () => {
  // A fixed pixel width here would reintroduce the truncation at a different
  // breakpoint instead of fixing it.
  assert.match(
    styles,
    /\.mission-picker\{display:grid;grid-template-columns:minmax\(210px,\.72fr\) repeat\(3,minmax\(0,1fr\)\)/,
  );
  assert.match(styles, /\.mission-picker>button\{display:grid;grid-template-columns:28px minmax\(0,1fr\) 22px/);
});

test("trajectory tooltips at the ends of a run anchor inside the panel", () => {
  // A centred 170px tooltip on the first or last node hung 85px past the panel
  // edge. Because an absolutely positioned box still counts toward scrollable
  // overflow, that gave the main column a horizontal scroll with nothing
  // hovered at all.
  assert.match(styles, /\.trajectory-node:first-child \.trajectory-tooltip\{left:0;right:auto/);
  assert.match(styles, /\.trajectory-node:last-child \.trajectory-tooltip\{left:auto;right:0/);
});

test("the end tooltips keep their anchoring while they are shown", () => {
  // The shared hover rule sets `translate(-50%,0)`. Without these, hovering
  // would snap an end tooltip back to centred and out of the panel again.
  assert.match(
    styles,
    /\.trajectory-node:first-child:hover \.trajectory-tooltip[^{]*\{transform:translate\(0,0\)\}/,
  );
  assert.match(
    styles,
    /\.trajectory-node:last-child:hover \.trajectory-tooltip[^{]*\{transform:translate\(0,0\)\}/,
  );
});

test("the tooltip arrow follows the box it points from", () => {
  // An anchored tooltip with a centred arrow points at empty space.
  assert.match(styles, /\.trajectory-node:first-child \.trajectory-tooltip:after\{left:11px\}/);
  assert.match(
    styles,
    /\.trajectory-node:last-child \.trajectory-tooltip:after\{left:auto;right:11px;transform:translateX\(50%\) rotate\(45deg\)\}/,
  );
});

test("the trajectory grid still lets tooltips escape their row", () => {
  // The earlier fix for clipped tooltips. Re-adding `overflow:hidden` here
  // would clip them again, which is how this defect arrived the first time.
  assert.match(styles, /\.trajectory-grid\{display:block;margin-top:0;overflow:visible\}/);
  assert.match(styles, /\.trajectory-row \.skill-run\{min-height:58px;border:0;overflow:visible\}/);
});
