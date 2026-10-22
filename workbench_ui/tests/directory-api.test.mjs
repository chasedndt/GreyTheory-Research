/**
 * The directory-lookup adapter.
 *
 * The failure that matters: letting a saved copy of a public page reach the
 * panel without the two facts that describe what it is. A lookup that arrives
 * missing its data class or trust would be rendered beside reviewed scope with
 * nothing to tell them apart.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { directoryFromSnapshot } from "../src/workbenchApi.js";

function lookup(identifier, over = {}) {
  const { attributes = {}, ...rest } = over;
  const [platform, handle] = identifier.split(":");
  return {
    id: `lookup:${identifier}`,
    title: identifier,
    status: "ready",
    subtitle: `${platform} · application/json`,
    detail: `https://${platform}.com/${handle}`,
    attributes: {
      identifier,
      kind: "directory_lookup",
      platform,
      handle,
      url: `https://${platform}.com/${handle}`,
      status: "200",
      content_type: "application/json",
      body_sha256: "a".repeat(64),
      body_bytes: "2048",
      retrieved_at: "2026-09-15T12:00:00+00:00",
      data_class: "PUBLIC",
      trust: "UNTRUSTED",
      grants_authority: "false",
      ...attributes,
    },
    ...rest,
  };
}

function snapshotWith(records, over = {}) {
  return {
    sections: [{
      id: "directory",
      title: "Directory lookups",
      status: "ready",
      metrics: [
        { label: "Programmes read", value: String(records.length) },
        { label: "Bytes retrieved", value: "2048" },
      ],
      records,
      note: "This is public, untrusted source material - not a scope contract.",
      ...over,
    }],
  };
}

test("a missing directory section is unavailable", () => {
  assert.equal(directoryFromSnapshot({ sections: [] }).available, false);
  assert.equal(directoryFromSnapshot(undefined).available, false);
});

test("no store configured is distinguished from nothing read", () => {
  const missing = directoryFromSnapshot(snapshotWith([], { status: "unknown" }));
  assert.equal(missing.configured, false);

  const empty = directoryFromSnapshot(snapshotWith([], { status: "empty" }));
  assert.equal(empty.configured, true);
  assert.deepEqual(empty.lookups, []);
});

test("a lookup carries where it came from, its size and its hash", () => {
  const [item] = directoryFromSnapshot(snapshotWith([lookup("hackerone:gitlab")])).lookups;

  assert.equal(item.platform, "hackerone");
  assert.equal(item.handle, "gitlab");
  assert.equal(item.url, "https://hackerone.com/gitlab");
  assert.equal(item.status, 200);
  assert.equal(item.bodyBytes, 2048);
  assert.equal(item.bodySha256.length, 64);
});

test("what the content is travels with it", () => {
  // Dropping these would let a saved marketing page sit beside reviewed scope
  // with nothing distinguishing them.
  const [item] = directoryFromSnapshot(snapshotWith([lookup("bugcrowd:ynab")])).lookups;

  assert.equal(item.dataClass, "PUBLIC");
  assert.equal(item.trust, "UNTRUSTED");
});

test("records of other kinds are ignored rather than shown as lookups", () => {
  const view = directoryFromSnapshot(snapshotWith([
    lookup("hackerone:gitlab"),
    { id: "directory:other", title: "x", attributes: { kind: "something_else" } },
  ]));

  assert.equal(view.lookups.length, 1);
});

test("a blocked section is reported as blocked rather than empty", () => {
  assert.equal(directoryFromSnapshot(snapshotWith([], { status: "blocked" })).blocked, true);
});

test("the boundary note reaches the panel", () => {
  const view = directoryFromSnapshot(snapshotWith([lookup("hackerone:gitlab")]));
  assert.match(view.note, /not a scope contract/);
});
