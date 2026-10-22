/**
 * The onboarding state.
 *
 * The property under test throughout: a step is done because something really
 * happened, never because it was skipped past. A wizard that congratulates you
 * for work you have not done is the same fabrication this product exists to
 * refuse, and it would be especially corrosive here - someone with no security
 * background has no way to tell they are being flattered.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  ONBOARDING_STORAGE_KEY,
  currentStep,
  onboardingProgress,
  onboardingSteps,
  readCollapsed,
  writeCollapsed,
} from "../src/onboarding.js";

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

// -- a cold install is honest about having done nothing ----------------------

test("nothing is done on a cold install", () => {
  const steps = onboardingSteps();

  assert.ok(steps.length > 0);
  assert.ok(steps.every((step) => step.done === false));
  assert.equal(onboardingProgress(steps).done, 0);
});

test("every step says why it matters and what to do", () => {
  for (const step of onboardingSteps()) {
    assert.ok(step.title, `${step.id} title`);
    assert.ok(step.why, `${step.id} needs a reason, not just an instruction`);
    assert.ok(step.action, `${step.id} action`);
    assert.ok(step.route, `${step.id} route`);
  }
});

test("the first thing asked for is the connection", () => {
  // Nothing is kept until it is connected, so congratulating someone on later
  // steps while their work is not being saved would be actively misleading.
  assert.equal(onboardingSteps()[0].id, "connect");
  assert.equal(currentStep(onboardingSteps()).id, "connect");
});

// -- done means it actually happened -----------------------------------------

test("connecting is the only thing that completes the connect step", () => {
  assert.equal(onboardingSteps({ connected: true })[0].done, true);
  assert.equal(onboardingSteps({ connected: false })[0].done, false);
});

test("a registered programme completes the programmes step and is counted", () => {
  const steps = onboardingSteps({
    programmes: { programmes: [{ id: "a", humanReviewed: false }, { id: "b", humanReviewed: false }] },
  });
  const programmes = steps.find((s) => s.id === "programmes");

  assert.equal(programmes.done, true);
  assert.match(programmes.action, /2 are compiled/);
});

test("registering a programme does not count as reviewing it", () => {
  // The distinction the whole gate rests on: compiled is not reviewed.
  const steps = onboardingSteps({
    programmes: { programmes: [{ id: "a", humanReviewed: false }] },
  });

  assert.equal(steps.find((s) => s.id === "programmes").done, true);
  assert.equal(steps.find((s) => s.id === "review").done, false);
});

test("a recorded human review completes the review step", () => {
  const steps = onboardingSteps({
    programmes: { programmes: [{ id: "a", humanReviewed: true }] },
  });
  const review = steps.find((s) => s.id === "review");

  assert.equal(review.done, true);
  assert.match(review.action, /1 reviewed/);
});

test("a worked-through lesson completes the curriculum step", () => {
  const none = onboardingSteps({ completedLessons: [] }).find((s) => s.id === "learn");
  const some = onboardingSteps({ completedLessons: ["security-ethics"] }).find((s) => s.id === "learn");

  assert.equal(none.done, false);
  assert.match(none.action, /Security ethics/);
  assert.equal(some.done, true);
});

test("an archived shortlist entry does not count as working on something", () => {
  // `active` is the working set; archived is a shelf, and saying otherwise
  // would report work that is not happening.
  const steps = onboardingSteps({ shortlist: { active: [], archived: [{ programmeId: "a" }] } });
  assert.equal(steps.find((s) => s.id === "shortlist").done, false);

  const working = onboardingSteps({ shortlist: { active: [{ programmeId: "a" }] } });
  assert.equal(working.find((s) => s.id === "shortlist").done, true);
});

// -- the order reflects what the system requires -----------------------------

test("reviewing comes before choosing what to work on", () => {
  const ids = onboardingSteps().map((step) => step.id);
  // A workspace inherits authority from a review, so the order is a real
  // dependency rather than a tutorial preference.
  assert.ok(ids.indexOf("review") < ids.indexOf("shortlist"));
  assert.ok(ids.indexOf("learn") < ids.indexOf("review"));
});

test("currentStep walks forward and ends at null", () => {
  const partly = onboardingSteps({
    connected: true,
    programmes: { programmes: [{ id: "a", humanReviewed: false }] },
  });
  assert.equal(currentStep(partly).id, "learn");

  const everything = onboardingSteps({
    connected: true,
    programmes: { programmes: [{ id: "a", humanReviewed: true }] },
    completedLessons: ["security-ethics"],
    shortlist: { active: [{ programmeId: "a" }] },
  });
  assert.equal(currentStep(everything), null);
  assert.equal(onboardingProgress(everything).complete, true);
});

// -- the connect step explains itself rather than nagging --------------------

test("the connect step says why the token is asked for every time", () => {
  const connect = onboardingSteps()[0];
  assert.match(connect.note, /not stored in the browser/);
});

// -- only the collapsed preference is remembered -----------------------------

test("the collapsed preference round-trips and defaults to open", () => {
  const storage = fakeStorage();
  assert.equal(readCollapsed(storage), false);

  writeCollapsed(true, storage);
  assert.equal(storage.data[ONBOARDING_STORAGE_KEY], "yes");
  assert.equal(readCollapsed(storage), true);
});

test("unavailable storage leaves it open rather than hiding it", () => {
  assert.equal(readCollapsed(throwingStorage), false);
  assert.equal(writeCollapsed(true, throwingStorage), true);
});
