/**
 * The automatic refresh policy.
 *
 * Every test here is about restraint rather than function. Each refresh is a
 * real request from the operator's address to a bug bounty platform, so the
 * failures that matter are: refreshing too often, refreshing in a burst, and
 * refreshing something the operator never asked for.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  DEFAULT_INTERVAL_MS,
  MANUAL_COOLDOWN_MS,
  MINIMUM_INTERVAL_MS,
  SPACING_MS,
  ageOf,
  canRefresh,
  clampInterval,
  describeAge,
  dueCount,
  nextDue,
  pageStatus,
  refreshPlan,
} from "../src/refreshPolicy.js";

const NOW = Date.parse("2026-09-15T12:00:00Z");
const MINUTE = 60000;

function row(id, minutesAgo, over = {}) {
  const verified = minutesAgo !== null;
  return {
    id,
    platform: "hackerone",
    handle: id.split(":")[1],
    verified,
    lookup: verified
      ? { retrievedAt: new Date(NOW - minutesAgo * MINUTE).toISOString() }
      : null,
    ...over,
  };
}

// -- the floor cannot be lowered ---------------------------------------------

test("an interval below the floor is clamped up, not honoured", () => {
  for (const requested of [0, 1000, 60000, MINIMUM_INTERVAL_MS - 1]) {
    assert.equal(clampInterval(requested), MINIMUM_INTERVAL_MS, `for ${requested}`);
  }
});

test("a longer interval than the floor is respected", () => {
  assert.equal(clampInterval(MINIMUM_INTERVAL_MS * 4), MINIMUM_INTERVAL_MS * 4);
});

test("a nonsensical interval falls back to the default rather than to zero", () => {
  for (const bad of [NaN, undefined, null, "soon", -1]) {
    const value = clampInterval(bad);
    assert.ok(value >= MINIMUM_INTERVAL_MS, `for ${String(bad)}`);
  }
});

test("the floor is not merely a suggestion in nextDue either", () => {
  const rows = [row("hackerone:gitlab", 5)];
  // Five minutes old, asking for a one-minute interval: still not due, because
  // the clamp applies inside the decision, not only at the edges.
  assert.equal(nextDue(rows, NOW, 60000), null);
});

// -- only what the operator already chose ------------------------------------

test("a programme never looked up is never refreshed automatically", () => {
  const rows = [row("hackerone:github", null), row("hackerone:shopify", null)];

  assert.equal(nextDue(rows, NOW, DEFAULT_INTERVAL_MS), null);
  assert.equal(dueCount(rows, NOW, DEFAULT_INTERVAL_MS), 0);
});

test("enabling refresh cannot itself cause a first request", () => {
  // A board of suggestions with one thing actually read: only that one is ever
  // eligible, however overdue the others would notionally be. Ages are now in
  // days because the cadence is daily - a two-hour-old read is not due.
  const rows = [
    row("hackerone:gitlab", 30 * 60),
    row("hackerone:github", null),
    row("hackerone:mozilla", null),
  ];
  const due = nextDue(rows, NOW, DEFAULT_INTERVAL_MS);

  assert.equal(due.id, "hackerone:gitlab");
  assert.equal(dueCount(rows, NOW, DEFAULT_INTERVAL_MS), 1);
});

// -- one at a time, oldest first ---------------------------------------------

const DAY = 24 * 60;

test("only one programme is returned, however many are overdue", () => {
  const rows = [row("a:one", 2 * DAY), row("a:two", 3 * DAY), row("a:three", 4 * DAY)];
  const due = nextDue(rows, NOW, DEFAULT_INTERVAL_MS);

  assert.equal(typeof due, "object");
  assert.equal(Array.isArray(due), false, "a batch would arrive as a burst");
});

test("the oldest goes first so nothing starves", () => {
  const rows = [row("a:recent", 26 * 60), row("a:oldest", 9 * DAY), row("a:middle", 2 * DAY)];
  assert.equal(nextDue(rows, NOW, DEFAULT_INTERVAL_MS).id, "a:oldest");
});

test("nothing is due when everything was read within the day", () => {
  // Hours-old reads are not due: the cadence is daily, and a page that changes
  // roughly monthly does not repay hourly checking.
  const rows = [row("a:one", 2 * 60), row("a:two", 20 * 60)];
  assert.equal(nextDue(rows, NOW, DEFAULT_INTERVAL_MS), null);
});

// -- ages are observed, never implied ----------------------------------------

test("a programme never read has no age and says so", () => {
  assert.equal(ageOf(row("a:one", null), NOW), null);
  assert.equal(describeAge(null), "never looked up");
});

test("a clock skew into the future reads as just now, not as a negative age", () => {
  const future = { verified: true, lookup: { retrievedAt: new Date(NOW + 5 * MINUTE).toISOString() } };
  assert.equal(ageOf(future, NOW), 0);
});

test("an unparseable timestamp is treated as unknown rather than as ancient", () => {
  const broken = { verified: true, lookup: { retrievedAt: "not a date" } };
  // Ancient would make it permanently due and refresh it on every tick.
  assert.equal(ageOf(broken, NOW), null);
  assert.equal(nextDue([{ ...broken, id: "a:one" }], NOW, DEFAULT_INTERVAL_MS), null);
});

test("ages read as a person would say them", () => {
  assert.equal(describeAge(30 * 1000), "just now");
  assert.equal(describeAge(1 * MINUTE), "1 minute ago");
  assert.equal(describeAge(42 * MINUTE), "42 minutes ago");
  assert.equal(describeAge(60 * MINUTE), "1 hour ago");
  assert.equal(describeAge(5 * 60 * MINUTE), "5 hours ago");
  assert.equal(describeAge(26 * 60 * MINUTE), "1 day ago");
});

// -- a person may re-check sooner than the daily cadence ---------------------

test("the automatic cadence is a full day and cannot be shortened", () => {
  assert.equal(MINIMUM_INTERVAL_MS, 24 * 60 * 60 * 1000);
  assert.equal(DEFAULT_INTERVAL_MS, MINIMUM_INTERVAL_MS, "there is no shorter default");
});

test("a page never read is a first look, not a re-check", () => {
  // Nothing is being re-requested, so no cooldown applies.
  assert.equal(canRefresh(row("a:one", null), NOW).allowed, true);
});

test("a page read within the cooldown cannot be hammered", () => {
  const recent = canRefresh(row("a:one", 30), NOW);

  assert.equal(recent.allowed, false);
  assert.ok(recent.waitMs > 0);
  assert.match(recent.reason, /Re-check available in/);
});

test("the cooldown is per programme, not global", () => {
  // Checking one must not lock out another; they are separate pages.
  assert.equal(canRefresh(row("a:justchecked", 5), NOW).allowed, false);
  assert.equal(canRefresh(row("a:untouched", null), NOW).allowed, true);
});

test("a person may re-check hours before the daily sweep would", () => {
  const age = MANUAL_COOLDOWN_MS + 60000;
  const ready = canRefresh(row("a:one", age / 60000), NOW);

  assert.equal(ready.allowed, true, "four hours is enough to catch a same-day change");
  assert.equal(nextDue([row("a:one", age / 60000)], NOW, DEFAULT_INTERVAL_MS), null,
    "while the automatic cadence still would not fire");
});

// -- the light describes the page, never the programme -----------------------

test("an unchecked page claims nothing", () => {
  const status = pageStatus(row("a:one", null), NOW);
  assert.equal(status.tone, "unknown");
  assert.match(status.label, /Not checked/);
});

test("a 200 reads as reachable and explicitly not as accepting submissions", () => {
  const status = pageStatus({ ...row("a:one", 10), lookup: { ...row("a:one", 10).lookup, status: 200 } }, NOW);

  assert.equal(status.tone, "live");
  assert.match(status.label, /Reachable/);
  // The distinction the whole light rests on: a published page is not a claim
  // that the programme is open for submissions.
  assert.match(status.detail, /not a statement about whether it is accepting/);
});

test("a non-200 reads as a problem with the handle, not as silence", () => {
  const base = row("a:one", 10);
  const status = pageStatus({ ...base, lookup: { ...base.lookup, status: 404 } }, NOW);

  assert.equal(status.tone, "down");
  assert.match(status.label, /404/);
  assert.match(status.detail, /handle may have changed/);
});

test("a page not read for over a day reads as stale rather than live", () => {
  const base = row("a:one", 3 * DAY);
  const status = pageStatus({ ...base, lookup: { ...base.lookup, status: 200 } }, NOW);

  assert.equal(status.tone, "stale");
  assert.match(status.detail, /a while ago/);
});

// -- a manual refresh states its cost first ----------------------------------

test("a refresh plan counts its requests and spaces them", () => {
  const rows = [row("a:one", 100), row("a:two", 200), row("a:three", null)];
  const plan = refreshPlan(rows);

  assert.equal(plan.requests, 2, "the unread one is not swept in");
  assert.equal(plan.spacingMs, SPACING_MS);
  assert.equal(plan.estimatedMs, SPACING_MS);
});

test("a plan over nothing costs nothing", () => {
  const plan = refreshPlan([row("a:one", null)]);
  assert.equal(plan.requests, 0);
  assert.equal(plan.estimatedMs, 0);
});
