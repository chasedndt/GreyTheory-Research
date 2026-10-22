/**
 * The hint preference.
 *
 * The failure that matters is silent withholding: a learner who has expressed
 * no preference, or whose browser storage is unavailable, must still be taught.
 * Every degraded path therefore resolves to "show hints", never to hiding them.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  HINTS_STORAGE_KEY,
  readHintPreference,
  writeHintPreference,
} from "../src/helpPreference.js";

function fakeStorage(initial = {}) {
  const data = { ...initial };
  return {
    getItem: (key) => (key in data ? data[key] : null),
    setItem: (key, value) => { data[key] = String(value); },
    data,
  };
}

const throwingStorage = {
  getItem() { throw new Error("storage disabled"); },
  setItem() { throw new Error("storage disabled"); },
};

test("a learner who has chosen nothing is taught by default", () => {
  assert.equal(readHintPreference(fakeStorage()), true);
});

test("an explicit choice is honoured in both directions", () => {
  assert.equal(readHintPreference(fakeStorage({ [HINTS_STORAGE_KEY]: "false" })), false);
  assert.equal(readHintPreference(fakeStorage({ [HINTS_STORAGE_KEY]: "true" })), true);
});

test("only the exact string false hides hints", () => {
  // Anything else is a corrupted or foreign value, and guessing that it means
  // "hide" would withhold teaching on the strength of a typo.
  for (const value of ["False", "0", "no", "", "null", "{}"]) {
    assert.equal(
      readHintPreference(fakeStorage({ [HINTS_STORAGE_KEY]: value })),
      true,
      `for ${JSON.stringify(value)}`,
    );
  }
});

test("unavailable storage degrades to showing hints rather than hiding them", () => {
  assert.equal(readHintPreference(throwingStorage), true);
  assert.equal(readHintPreference(null), true);
});

test("the preference round-trips through storage", () => {
  const storage = fakeStorage();
  writeHintPreference(false, storage);
  assert.equal(storage.data[HINTS_STORAGE_KEY], "false");
  assert.equal(readHintPreference(storage), false);

  writeHintPreference(true, storage);
  assert.equal(readHintPreference(storage), true);
});

test("a failed write neither throws nor misreports what was chosen", () => {
  // The choice still applies to this session even when it cannot be persisted.
  assert.equal(writeHintPreference(false, throwingStorage), false);
  assert.equal(writeHintPreference(true, throwingStorage), true);
});
