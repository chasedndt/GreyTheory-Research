/**
 * The bounty board's join between suggestion and evidence.
 *
 * One invariant carries this whole design: a row is verified because something
 * was actually retrieved, never because the shipped list says so. Prior
 * knowledge goes stale - a programme can close, move platform, or change its
 * handle - so the list may only ever propose, and the lookup decides.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { KNOWN_PROGRAMMES, REWARD_POSTURE, boardRows, knownProgramme } from "../src/knownProgrammes.js";

function lookupFor(identifier, over = {}) {
  const [platform, handle] = identifier.split(":");
  return {
    identifier,
    platform,
    handle,
    url: `https://${platform}.com/${handle}`,
    status: 200,
    contentType: "text/html",
    bodySha256: "a".repeat(64),
    bodyBytes: 4096,
    retrievedAt: "2026-09-15T12:00:00+00:00",
    dataClass: "PUBLIC",
    trust: "UNTRUSTED",
    ...over,
  };
}

test("nothing is verified before anything has been retrieved", () => {
  const rows = boardRows([]);

  assert.equal(rows.length, KNOWN_PROGRAMMES.length);
  assert.ok(rows.every((row) => row.verified === false));
  assert.ok(rows.every((row) => row.lookup === null));
});

test("a row becomes verified only because a lookup exists for it", () => {
  const rows = boardRows([lookupFor("hackerone:gitlab")]);
  const gitlab = rows.find((row) => row.id === "hackerone:gitlab");
  const other = rows.find((row) => row.id === "hackerone:github");

  assert.equal(gitlab.verified, true);
  assert.equal(gitlab.lookup.bodyBytes, 4096);
  assert.equal(other.verified, false, "its neighbour is unaffected");
});

test("the shipped list cannot make a row verified by itself", () => {
  // Every entry ships without any retrieved evidence attached; the only route
  // to verified is through a lookup passed in.
  for (const entry of KNOWN_PROGRAMMES) {
    assert.equal("lookup" in entry, false, `${entry.id} must ship no evidence`);
    assert.equal("verified" in entry, false, `${entry.id} must not claim verification`);
  }
});

test("every shipped entry names a real platform and a usable handle", () => {
  const platforms = new Set(["hackerone", "bugcrowd", "intigriti", "yeswehack"]);
  for (const entry of KNOWN_PROGRAMMES) {
    assert.ok(platforms.has(entry.platform), `${entry.id} platform`);
    // Must satisfy the same rule the server enforces, or Look up cannot work.
    assert.match(entry.handle, /^[a-z0-9][a-z0-9._-]{0,63}$/, `${entry.id} handle`);
    assert.equal(entry.id, `${entry.platform}:${entry.handle}`, `${entry.id} identifier`);
    assert.ok(entry.name && entry.why, `${entry.id} needs a name and a reason`);
  }
});

test("shipped identifiers are unique", () => {
  const ids = KNOWN_PROGRAMMES.map((entry) => entry.id);
  assert.equal(ids.length, new Set(ids).size);
});

test("a programme you found yourself is not second-class", () => {
  const rows = boardRows([lookupFor("bugcrowd:somethingelse")]);
  const found = rows.find((row) => row.id === "bugcrowd:somethingelse");

  assert.ok(found, "a lookup outside the list still appears");
  assert.equal(found.verified, true);
  assert.equal(found.suggested, false);
});

test("retrieved rows sort above suggestions", () => {
  const rows = boardRows([lookupFor("hackerone:mozilla")]);

  assert.equal(rows[0].id, "hackerone:mozilla");
  assert.ok(rows.slice(1).every((row) => row.verified === false));
});

test("every entry declares whether it pays, and none names a figure", () => {
  for (const entry of KNOWN_PROGRAMMES) {
    assert.ok(REWARD_POSTURE[entry.rewards], `${entry.id} needs a known reward posture`);
    // An amount taken from memory is a number someone might act on, and bounty
    // ranges move without notice. Nothing in this file may carry one.
    const text = `${entry.name} ${entry.target} ${entry.why}`;
    assert.doesNotMatch(text, /[$£€]\s?\d/, `${entry.id} must not state an amount`);
  }
});

test("a programme you found yourself admits its reward posture is unknown", () => {
  const rows = boardRows([{
    identifier: "bugcrowd:mystery",
    platform: "bugcrowd",
    handle: "mystery",
    retrievedAt: "2026-09-15T12:00:00+00:00",
    bodyBytes: 100,
    bodySha256: "b".repeat(64),
    contentType: "text/html",
  }]);
  const found = rows.find((row) => row.id === "bugcrowd:mystery");

  assert.equal(found.rewards, "unknown");
  assert.match(REWARD_POSTURE.unknown.detail, /own page is the only authority/);
});

test("knownProgramme resolves a shipped entry and refuses an unknown one", () => {
  assert.equal(knownProgramme("hackerone:gitlab").name, "GitLab");
  assert.equal(knownProgramme("hackerone:nope"), null);
});
