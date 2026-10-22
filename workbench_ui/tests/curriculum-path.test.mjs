/**
 * The curriculum path.
 *
 * The property under test is the one the old Learn page broke: a learner is
 * never asked about something they were not first taught. Everything else here
 * is in service of that - ordering, reachability, and progress that cannot
 * quietly become a claim about skill.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  PROGRESS_STORAGE_KEY,
  curriculumPath,
  nextLesson,
  overallProgress,
  readProgress,
  writeProgress,
} from "../src/curriculumPath.js";

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

// -- the path exists and is ordered ------------------------------------------

test("every track carries lessons in teaching order", () => {
  const tracks = curriculumPath([]);

  assert.deepEqual(tracks.map((t) => t.id), ["foundations", "web-api", "agent-security"]);
  for (const track of tracks) {
    assert.ok(track.total > 0, `${track.id} has lessons`);
    assert.deepEqual(
      track.steps.map((s) => s.position),
      track.steps.map((_, i) => i + 1),
      `${track.id} positions are sequential`,
    );
  }
});

test("every step carries the material a learner needs to choose it", () => {
  for (const track of curriculumPath([])) {
    for (const step of track.steps) {
      assert.ok(step.title, `${step.id} title`);
      assert.ok(step.oneLine, `${step.id} needs a line saying what it is about`);
      assert.ok(step.checks > 0, `${step.id} has checks`);
      assert.ok(step.level && step.duration, `${step.id} level and duration`);
    }
  }
});

// -- nothing is asked before it is taught ------------------------------------

test("each track offers exactly one place to begin", () => {
  // The tracks run in parallel rather than as one chain, so each has its own
  // first step. What must never happen is a track showing several equally
  // plausible entry points - the grid of equal tiles this replaces.
  for (const track of curriculumPath([])) {
    const current = track.steps.filter((s) => s.state === "current");
    assert.equal(current.length, 1, `${track.id} has one entry point`);
    assert.equal(current[0].position, 1, `${track.id} starts at its first lesson`);
  }
});

test("across the whole curriculum a cold learner is given one answer", () => {
  // Three parallel entry points is correct for the map; it is useless as an
  // instruction. nextLesson is what turns the map into a single next step.
  const { track, step } = nextLesson([]);

  assert.equal(track.id, "foundations");
  assert.equal(step.position, 1);
});

test("later lessons are not reachable until earlier ones are done", () => {
  const [foundations] = curriculumPath([]);

  assert.equal(foundations.steps[0].state, "current");
  assert.ok(
    foundations.steps.slice(1).every((s) => s.state === "later"),
    "nothing downstream is reachable from a cold start",
  );
});

test("completing a lesson opens the next one and never closes an earlier one", () => {
  const [foundations] = curriculumPath([]);
  const first = foundations.steps[0].id;
  const [afterFirst] = curriculumPath([first]);

  assert.equal(afterFirst.steps[0].state, "done");
  assert.equal(afterFirst.steps[1].state, "current");
  // Revisiting what you already learned must always be allowed.
  assert.notEqual(afterFirst.steps[0].state, "later");
});

test("completing out of order does not unlock the gap that was skipped", () => {
  const [foundations] = curriculumPath([]);
  const third = foundations.steps[2].id;
  const [path] = curriculumPath([third]);

  assert.equal(path.steps[2].state, "done");
  assert.equal(path.steps[0].state, "current", "the gap is still the next thing to do");
  assert.equal(path.steps[1].state, "later", "and what follows the gap stays closed");
});

test("nextLesson walks tracks in order and stops when everything is done", () => {
  const cold = nextLesson([]);
  assert.equal(cold.track.id, "foundations");
  assert.equal(cold.step.position, 1);

  const everything = curriculumPath([]).flatMap((t) => t.steps).map((s) => s.id);
  assert.equal(nextLesson(everything), null);
});

test("a finished track hands over to the next one", () => {
  const [foundations] = curriculumPath([]);
  const allFoundations = foundations.steps.map((s) => s.id);
  const next = nextLesson(allFoundations);

  assert.equal(next.track.id, "web-api");
  assert.equal(next.step.position, 1);
});

// -- progress is encouragement, never a claim --------------------------------

test("overall progress counts lessons, not competence", () => {
  const zero = overallProgress([]);
  assert.equal(zero.done, 0);
  assert.equal(zero.percent, 0);

  const [foundations] = curriculumPath([]);
  const some = overallProgress(foundations.steps.slice(0, 2).map((s) => s.id));
  assert.equal(some.done, 2);
  assert.ok(some.percent > 0 && some.percent < 100);
});

test("an unknown id cannot inflate progress", () => {
  const { done } = overallProgress(["not-a-lesson", "also-not-a-lesson"]);
  assert.equal(done, 0);
});

// -- progress survives, and degrades honestly --------------------------------

test("progress round-trips through storage", () => {
  const storage = fakeStorage();
  writeProgress(["security-ethics", "scope-and-authority"], storage);

  assert.deepEqual(readProgress(storage), ["security-ethics", "scope-and-authority"]);
  assert.ok(storage.data[PROGRESS_STORAGE_KEY]);
});

test("duplicates are collapsed rather than counted twice", () => {
  const storage = fakeStorage();
  writeProgress(["security-ethics", "security-ethics"], storage);
  assert.deepEqual(readProgress(storage), ["security-ethics"]);
});

test("corrupted or unavailable storage reads as no progress, never as progress", () => {
  // Inventing completion would tell a learner they had been taught something
  // they had not, which is worse than losing a streak.
  assert.deepEqual(readProgress(fakeStorage({ [PROGRESS_STORAGE_KEY]: "{not json" })), []);
  assert.deepEqual(readProgress(fakeStorage({ [PROGRESS_STORAGE_KEY]: '{"done":true}' })), []);
  assert.deepEqual(readProgress(fakeStorage({ [PROGRESS_STORAGE_KEY]: '[1,2,3]' })), []);
  assert.deepEqual(readProgress(throwingStorage), []);
});

test("a failed write neither throws nor misreports what was kept", () => {
  assert.deepEqual(writeProgress(["security-ethics"], throwingStorage), ["security-ethics"]);
});
