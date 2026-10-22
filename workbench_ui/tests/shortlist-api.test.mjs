/**
 * The shortlist snapshot adapter.
 *
 * Two failures would mislead the operator in opposite directions: showing an
 * open programme as set aside hides work they still have, and treating an
 * empty shortlist as unavailable makes the panel vanish exactly when they have
 * just archived their last item.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { shortlistFromSnapshot } from "../src/workbenchApi.js";

function entry(programmeId, over = {}) {
  const { attributes = {}, ...rest } = over;
  return {
    id: `shortlist:${programmeId}`,
    title: programmeId,
    status: "ready",
    subtitle: "being worked",
    detail: "On your active list.",
    attributes: {
      programme_id: programmeId,
      kind: "shortlist_entry",
      status: "active",
      outcome: "unset",
      shortlisted_at: "2026-09-15T12:01:00+00:00",
      updated_at: "2026-09-15T12:01:00+00:00",
      revision: "0",
      grants_authority: "false",
      ...attributes,
    },
    ...rest,
  };
}

function snapshotWith(records, note = "Archiving is reversible.") {
  return { sections: [{ id: "shortlist", title: "Shortlist", records, note }] };
}

test("a missing shortlist section is unavailable", () => {
  assert.equal(shortlistFromSnapshot({ sections: [] }).available, false);
  assert.equal(shortlistFromSnapshot(undefined).available, false);
});

test("an empty shortlist is available so it can render its own empty state", () => {
  const view = shortlistFromSnapshot(snapshotWith([]));

  assert.equal(view.available, true, "a panel that vanishes when emptied is a dead end");
  assert.deepEqual(view.counts, { active: 0, archived: 0 });
});

test("entries are split by status with symmetric counts", () => {
  const view = shortlistFromSnapshot(snapshotWith([
    entry("gitlab"),
    entry("ynab", { attributes: { status: "archived", outcome: "finished" }, detail: "paid out" }),
    entry("mcp-sdk"),
  ]));

  assert.deepEqual(view.active.map((item) => item.programmeId), ["gitlab", "mcp-sdk"]);
  assert.deepEqual(view.archived.map((item) => item.programmeId), ["ynab"]);
  assert.deepEqual(view.counts, { active: 2, archived: 1 });
});

test("only the exact string archived sets something aside", () => {
  for (const [value, expected] of [
    ["archived", true], ["active", false], ["Archived", false], [undefined, false],
  ]) {
    const view = shortlistFromSnapshot(snapshotWith([
      entry("p", { attributes: { status: value } }),
    ]));
    assert.equal(view.archived.length, expected ? 1 : 0, `for ${JSON.stringify(value)}`);
  }
});

test("an archived entry carries its outcome and reason", () => {
  const view = shortlistFromSnapshot(snapshotWith([
    entry("ynab", {
      attributes: { status: "archived", outcome: "out_of_scope_now" },
      detail: "scope shrank in August",
    }),
  ]));
  const [item] = view.archived;

  assert.equal(item.outcome, "out_of_scope_now");
  assert.equal(item.detail, "scope shrank in August");
});

test("the revision is a number so a command can pin its write", () => {
  const view = shortlistFromSnapshot(snapshotWith([
    entry("p", { attributes: { revision: "7" } }),
    entry("q", { attributes: { revision: undefined } }),
  ]));

  assert.equal(view.active.find((i) => i.programmeId === "p").revision, 7);
  assert.equal(view.active.find((i) => i.programmeId === "q").revision, 0);
});

test("records of other kinds are ignored rather than shown as entries", () => {
  const view = shortlistFromSnapshot(snapshotWith([
    entry("p"),
    { id: "shortlist:note", title: "something else", attributes: { kind: "other" } },
  ]));

  assert.equal(view.active.length, 1);
});

test("the rule of the place is carried through to the panel", () => {
  const view = shortlistFromSnapshot(snapshotWith([], "Archiving is reversible and deletes nothing."));
  assert.match(view.note, /reversible/);
});
