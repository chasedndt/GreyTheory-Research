/**
 * The research workspace adapter.
 *
 * The failure that matters here is inventing certainty about a workspace the
 * server could not read. A blocked record arrives with no attributes at all, so
 * anything that defaults its counts to zero is making a confident claim about
 * contents nobody has seen.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { researchFromSnapshot } from "../src/workbenchApi.js";

function workspace(id, over = {}) {
  const { attributes = {}, ...rest } = over;
  return {
    id,
    title: `Workspace ${id}`,
    status: "ready",
    subtitle: "active",
    detail: "Understand how sessions are issued.",
    references: [`authority:${"a".repeat(64)}`],
    attributes: {
      programme_id: "hackerone-gitlab-public",
      posture: "LOCAL_FIXTURE",
      sessions: "2",
      active_sessions: "1",
      hypotheses: "5",
      action_requests: "3",
      action_receipts: "3",
      lessons: "1",
      ...attributes,
    },
    ...rest,
  };
}

function snapshotWith(records, over = {}) {
  return {
    sections: [{
      id: "research",
      title: "Research",
      status: "ready",
      metrics: [{ label: "Workspaces", value: String(records.length) }],
      records,
      ...over,
    }],
  };
}

test("a missing research section is unavailable", () => {
  assert.equal(researchFromSnapshot({ sections: [] }).available, false);
  assert.equal(researchFromSnapshot(undefined).available, false);
});

test("no store configured is distinguished from an empty store", () => {
  const missing = researchFromSnapshot(snapshotWith([], { status: "unknown" }));
  assert.equal(missing.available, true);
  assert.equal(missing.configured, false, "a setup problem, not an empty workspace");

  const empty = researchFromSnapshot(snapshotWith([], { status: "empty" }));
  assert.equal(empty.configured, true, "an ordinary starting point");
  assert.deepEqual(empty.workspaces, []);
});

test("a workspace carries its programme, posture, goal and counts", () => {
  const [item] = researchFromSnapshot(snapshotWith([workspace("ws-1")])).workspaces;

  assert.equal(item.programmeId, "hackerone-gitlab-public");
  assert.equal(item.posture, "LOCAL_FIXTURE");
  assert.equal(item.status, "active");
  assert.match(item.goal, /sessions are issued/);
  assert.equal(item.counts.hypotheses, 5);
  assert.equal(item.counts.activeSessions, 1);
  assert.match(item.authorityRef, /^authority:/);
});

test("an unreadable workspace withholds counts rather than inventing zeroes", () => {
  const broken = {
    id: "ws-broken",
    title: "ws-broken",
    status: "blocked",
    detail: "workspace failed its integrity check",
  };
  const [item] = researchFromSnapshot(snapshotWith([broken])).workspaces;

  assert.equal(item.unreadable, true);
  assert.equal(item.counts, null, "zero would be a claim about unread contents");
  assert.match(item.error, /integrity check/);
});

test("a blocked section is reported as blocked rather than empty", () => {
  const view = researchFromSnapshot(snapshotWith([], { status: "blocked" }));
  assert.equal(view.blocked, true);
});

test("the active workspace is named only when the server knows it", () => {
  const known = researchFromSnapshot(snapshotWith([workspace("ws-1")], {
    metrics: [{ label: "Workspaces", value: "1" }, { label: "Active", value: "ws-1" }],
  }));
  assert.equal(known.activeId, "ws-1");

  const unknown = researchFromSnapshot(snapshotWith([workspace("ws-1")], {
    metrics: [{ label: "Workspaces", value: "1" }, { label: "Active", value: "unknown" }],
  }));
  assert.equal(unknown.activeId, null, "'unknown' is a placeholder, not an id");
});
