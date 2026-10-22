/**
 * The review snapshot adapter.
 *
 * Two shapes are easy to get wrong here and both would mislead a reviewer: the
 * server's "none recorded" placeholder is a message rather than an asset, and
 * hash agreement must mean the exact string "true" rather than anything truthy.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { reviewFromSnapshot } from "../src/workbenchApi.js";
import { reviewability } from "../src/reviewability.js";

function record(kind, over = {}) {
  const { attributes = {}, ...rest } = over;
  return {
    id: `review:p:${kind}`,
    title: kind,
    status: "ready",
    subtitle: "p",
    detail: "",
    attributes: { programme_id: "p", kind, ...attributes },
    ...rest,
  };
}

function snapshotWith(records) {
  return { sections: [{ id: "review", title: "Review material", records }] };
}

test("a missing review section is unavailable", () => {
  assert.equal(reviewFromSnapshot({ sections: [] }).available, false);
  assert.equal(reviewFromSnapshot(undefined).available, false);
});

test("scope groups split their detail into individual values", () => {
  const snap = snapshotWith([
    record("in-scope", { detail: "gitlab.com\nregistry.gitlab.com", attributes: { count: "2" } }),
  ]);
  const [entry] = reviewFromSnapshot(snap).programmes;
  const group = entry.scope.find((item) => item.kind === "in-scope");

  assert.equal(group.count, 2);
  assert.deepEqual(group.values, ["gitlab.com", "registry.gitlab.com"]);
});

test("an empty group renders no values rather than the placeholder text", () => {
  const snap = snapshotWith([
    record("out-of-scope", { detail: "none recorded", attributes: { count: "0" } }),
  ]);
  const [entry] = reviewFromSnapshot(snap).programmes;
  const group = entry.scope.find((item) => item.kind === "out-of-scope");

  assert.equal(group.count, 0);
  assert.deepEqual(group.values, [], "'none recorded' is a message, not an asset");
});

test("all three scope groups exist even when the server sends none", () => {
  const [entry] = reviewFromSnapshot(snapshotWith([record("source_document", {
    attributes: { capture_mode: "verbatim", hash_agrees: "true", bytes: "10" },
  })])).programmes;

  assert.deepEqual(entry.scope.map((g) => g.kind), ["in-scope", "out-of-scope", "prohibited"]);
});

test("a source document carries its content, capture mode and size", () => {
  const snap = snapshotWith([
    record("source_document", {
      title: "gitlab-scope-csv",
      detail: "identifier,asset_type",
      attributes: { capture_mode: "structured_export", hash_agrees: "true", bytes: "6686", truncated: "false" },
    }),
  ]);
  const [doc] = reviewFromSnapshot(snap).programmes[0].documents;

  assert.equal(doc.title, "gitlab-scope-csv");
  assert.equal(doc.captureMode, "structured_export");
  assert.equal(doc.bytes, 6686);
  assert.equal(doc.hashAgrees, true);
  assert.equal(doc.truncated, false);
  assert.match(doc.content, /identifier/);
});

test("only the exact string true means the hashes agreed", () => {
  for (const [value, expected] of [["true", true], ["false", false], ["True", false], [undefined, false]]) {
    const snap = snapshotWith([
      record("source_document", { attributes: { hash_agrees: value, bytes: "1" } }),
    ]);
    const [doc] = reviewFromSnapshot(snap).programmes[0].documents;
    assert.equal(doc.hashAgrees, expected, `for ${JSON.stringify(value)}`);
  }
});

test("human resolutions carry whether they are settled", () => {
  const snap = snapshotWith([
    record("human_resolution", { title: "wildcard-vs-listed", attributes: { resolved: "false" } }),
    record("human_resolution", { id: "review:p:r2", title: "settled", attributes: { resolved: "true" } }),
  ]);
  const { resolutions } = reviewFromSnapshot(snap).programmes[0];

  assert.equal(resolutions.length, 2);
  assert.equal(resolutions.find((r) => r.title === "wildcard-vs-listed").resolved, false);
  assert.equal(resolutions.find((r) => r.title === "settled").resolved, true);
});

test("records without a programme id are ignored rather than grouped under undefined", () => {
  const orphan = record("in-scope", { attributes: { programme_id: "" } });
  assert.equal(reviewFromSnapshot(snapshotWith([orphan])).available, false);
});

test("a programme carries whether a person has already reviewed it", () => {
  const snap = snapshotWith([
    record("programme_state", { attributes: { human_reviewed: "true", contract_status: "verified" } }),
  ]);
  const [entry] = reviewFromSnapshot(snap).programmes;

  assert.equal(entry.humanReviewed, true);
  assert.equal(entry.contractStatus, "verified");
});

test("only the exact string true means a person reviewed it", () => {
  for (const [value, expected] of [["true", true], ["false", false], ["True", false], [undefined, false]]) {
    const snap = snapshotWith([record("programme_state", { attributes: { human_reviewed: value } })]);
    const [entry] = reviewFromSnapshot(snap).programmes;
    assert.equal(entry.humanReviewed, expected, `for ${JSON.stringify(value)}`);
  }
});

test("a programme the server says nothing about is treated as unreviewed", () => {
  const [entry] = reviewFromSnapshot(snapshotWith([
    record("in-scope", { detail: "gitlab.com", attributes: { count: "1" } }),
  ])).programmes;

  // The safe default offers the gate rather than skipping it.
  assert.equal(entry.humanReviewed, false);
  assert.equal(entry.contractStatus, "unknown");
});

// -- whether the review control may be offered at all -------------------------

const READY_ENTRY = {
  programmeId: "p",
  humanReviewed: false,
  resolutions: [{ id: "r1", title: "settled", resolved: true }],
  documents: [{ id: "d1", hashAgrees: true }],
};

test("a clean unreviewed contract may be reviewed", () => {
  assert.equal(reviewability(READY_ENTRY).reviewable, true);
});

test("an already-reviewed contract is not offered again", () => {
  const result = reviewability({ ...READY_ENTRY, humanReviewed: true });
  assert.equal(result.reviewable, false);
  assert.match(result.reason, /already recorded reading/);
});

test("an unresolved question is named before anything else that is wrong", () => {
  const result = reviewability({
    ...READY_ENTRY,
    resolutions: [{ id: "r1", title: "wildcard-vs-listed", resolved: false }],
    documents: [{ id: "d1", hashAgrees: false }],
  });

  assert.equal(result.reviewable, false);
  // It is what a blocked contract is actually waiting on, so it is said first.
  assert.match(result.reason, /settled before this can compile clean/);
  assert.match(result.reason, /does not resolve ambiguity/);
});

test("content disagreeing with its own hash cannot be reviewed", () => {
  const result = reviewability({ ...READY_ENTRY, documents: [{ id: "d1", hashAgrees: false }] });
  assert.equal(result.reviewable, false);
  assert.match(result.reason, /does not match the hash it declared/);
});

test("there is nothing to have read when no sources are stored", () => {
  const result = reviewability({ ...READY_ENTRY, documents: [] });
  assert.equal(result.reviewable, false);
  assert.match(result.reason, /nothing here to have read/);
});

test("a missing entry refuses rather than throwing", () => {
  assert.equal(reviewability(undefined).reviewable, false);
  assert.equal(reviewability(null).reviewable, false);
});

test("several programmes each get their own entry", () => {
  const snap = snapshotWith([
    record("in-scope", { attributes: { count: "1" }, detail: "a.test" }),
    { ...record("in-scope", { attributes: { count: "1" }, detail: "b.test" }), id: "review:q:in", attributes: { programme_id: "q", kind: "in-scope", count: "1" } },
  ]);
  const { programmes } = reviewFromSnapshot(snap);

  assert.deepEqual(programmes.map((entry) => entry.programmeId), ["p", "q"]);
});
