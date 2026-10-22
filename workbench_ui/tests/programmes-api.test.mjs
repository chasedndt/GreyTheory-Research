/**
 * The registered-programmes adapter, and what to do next with each one.
 *
 * Two failures would mislead: reporting a contract as reviewed when only one of
 * the two stored facts says so, and stating how many questions block a
 * programme when the section does not carry that number at all.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { programmesFromSnapshot } from "../src/workbenchApi.js";
import { programmeNextStep } from "../src/programmeReadiness.js";

function record(id, subtitle, over = {}) {
  const { attributes = {}, ...rest } = over;
  return {
    id,
    title: id,
    status: "attention",
    subtitle,
    detail: subtitle === "blocked" ? "blocked" : "awaiting_review",
    attributes: {
      human_reviewed: "false",
      max_authority: "LOCAL_FIXTURE",
      version: "1",
      ...attributes,
    },
    ...rest,
  };
}

function snapshotWith(records, metrics) {
  return {
    sections: [{
      id: "programmes",
      title: "Programmes",
      status: "attention",
      metrics: metrics || [
        { label: "Registered", value: String(records.length) },
        { label: "Need attention", value: String(records.length) },
      ],
      records,
    }],
  };
}

test("a missing programmes section is unavailable", () => {
  assert.equal(programmesFromSnapshot({ sections: [] }).available, false);
  assert.equal(programmesFromSnapshot(undefined).available, false);
});

test("registered programmes carry their contract state and version", () => {
  const view = programmesFromSnapshot(snapshotWith([
    record("bugcrowd-ynab-public", "blocked"),
    record("hackerone-gitlab-public", "pending_review"),
  ]));

  assert.deepEqual(view.programmes.map((p) => p.id), [
    "bugcrowd-ynab-public", "hackerone-gitlab-public",
  ]);
  assert.equal(view.programmes[0].contractStatus, "blocked");
  assert.equal(view.programmes[1].maxAuthority, "LOCAL_FIXTURE");
  assert.equal(view.programmes[1].version, 1);
  assert.deepEqual(view.counts, { registered: 2, needingAttention: 2 });
});

test("only the exact string true means a person reviewed it", () => {
  for (const [value, expected] of [["true", true], ["false", false], ["True", false], [undefined, false]]) {
    const view = programmesFromSnapshot(snapshotWith([
      record("p", "verified", { attributes: { human_reviewed: value } }),
    ]));
    assert.equal(view.programmes[0].humanReviewed, expected, `for ${JSON.stringify(value)}`);
  }
});

// -- what to do next ---------------------------------------------------------

test("a blocked contract is told to settle and recompile, not to review", () => {
  const next = programmeNextStep({ contractStatus: "blocked", humanReviewed: false });
  assert.match(next.step, /Settle its open questions/);
  assert.match(next.because, /does not resolve ambiguity/);
});

test("a blocked contract never claims how many questions are outstanding", () => {
  // The section carries no ambiguity count, so any number here would be
  // invented precision.
  const next = programmeNextStep({ contractStatus: "blocked", humanReviewed: false });
  assert.doesNotMatch(next.step + next.because, /\d/);
});

test("a clean contract is sent to review, and says the step is yours alone", () => {
  const next = programmeNextStep({ contractStatus: "pending_review", humanReviewed: false });
  assert.match(next.step, /Review the compiled scope/);
  assert.match(next.because, /nobody can take for you/);
});

test("verified requires both the status and the recorded human review", () => {
  const both = programmeNextStep({ contractStatus: "verified", humanReviewed: true });
  assert.match(both.step, /Open a research workspace/);

  // Verified on paper but with no person recorded is not verified enough.
  const halfway = programmeNextStep({ contractStatus: "verified", humanReviewed: false });
  assert.notEqual(halfway.step, both.step);
});

test("every contract state the server can emit has its own step", () => {
  // ContractStatus has four values. A state with no entry would fall to
  // "not reported", which is untrue - it was reported, nobody wrote copy for it.
  for (const status of ["draft", "pending_review", "verified", "blocked"]) {
    const next = programmeNextStep({ contractStatus: status, humanReviewed: true });
    assert.doesNotMatch(next.because, /not reported/, `for ${status}`);
  }
});

test("an unreported state is admitted rather than guessed", () => {
  for (const input of [null, undefined, { contractStatus: "something-else" }]) {
    assert.match(programmeNextStep(input).because, /not reported|nothing can be assumed/);
  }
});
