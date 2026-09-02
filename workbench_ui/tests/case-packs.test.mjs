import assert from "node:assert/strict";
import test from "node:test";

import { CASE_PACKS, DEMO_RUNS, LIVE_PROGRAMME_GATES, MISSION_SEGMENTS, PROGRAMME_READINESS, casePackById } from "../src/casePacks.js";

test("case-pack preview exposes one local pack and keeps live activation gated", () => {
  assert.equal(CASE_PACKS.length, 3);
  assert.equal(CASE_PACKS.filter((item) => item.status === "Ready locally").length, 1);
  assert.equal(casePackById("agent-authorization-boundary").primaryCard, "tool-authorization-failure");
  assert.equal(LIVE_PROGRAMME_GATES.length, 5);
  assert.ok(LIVE_PROGRAMME_GATES.every((item) => !/ready now|enabled/i.test(item)));
});

test("demo suite separates guided, full, and independent transfer runs", () => {
  assert.deepEqual(DEMO_RUNS.map((item) => item.id), ["guided-preview", "learner-mission", "transfer-check"]);
  assert.match(DEMO_RUNS[2].status, /human review/);
});

test("guided mission is an exact thirty-minute bounded learning loop", () => {
  assert.equal(CASE_PACKS[0].duration, "30 min");
  assert.equal(CASE_PACKS[0].version, "1.1.0");
  assert.equal(DEMO_RUNS[1].duration, "30 min");
  assert.deepEqual(MISSION_SEGMENTS.map((segment) => segment.id), ["learn", "practise", "prove", "reflect", "assess"]);
  assert.equal(MISSION_SEGMENTS.reduce((total, segment) => total + segment.minutes, 0), 30);
  assert.ok(MISSION_SEGMENTS.every((segment) => segment.outcome && segment.deliverable && segment.boundary));
});

test("programme readiness remains offline and preserves ambiguity", () => {
  assert.deepEqual(PROGRAMME_READINESS.map((programme) => programme.platform), ["HackerOne", "Bugcrowd", "Direct VDP"]);
  assert.ok(PROGRAMME_READINESS.every((programme) => programme.source && programme.nextAction));
  assert.equal(PROGRAMME_READINESS.find((programme) => programme.id === "ynab").blocked, true);
  assert.ok(PROGRAMME_READINESS.every((programme) => !/connected|active testing/i.test(programme.caseState)));
});
