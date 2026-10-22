/**
 * The campaign snapshot adapter.
 *
 * The server sends every attribute as a string, and the whole journey arrives
 * as one compact field rather than a record per stage. Both are easy to parse
 * loosely and wrong to: "blocked" must mean the exact string, and a stage
 * marker that goes missing must not quietly become a satisfied one.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { campaignFromSnapshot } from "../src/workbenchApi.js";

function snapshotWith(records) {
  return { sections: [{ id: "campaign", title: "Campaign", records }] };
}

const RECORD = {
  id: "campaign:hackerone-gitlab-public",
  title: "hackerone-gitlab-public",
  status: "blocked",
  subtitle: "stage: programme",
  detail: "hackerone-gitlab-public has 19 in-scope assets but no human verification",
  attributes: {
    current_stage: "programme",
    next_action: "review the compiled contract",
    blocked_by_governance: "true",
    stages: "programme=gov,curriculum=todo,study=todo,plan=todo,evidence=gov,draft=todo,submission=todo",
    premature_stages: "",
    practised_topics: "0",
    posture: "LOCAL_FIXTURE",
    grants_authority: "false",
    submitted: "false",
  },
};

test("a missing campaign section is unavailable rather than empty-but-present", () => {
  assert.equal(campaignFromSnapshot({ sections: [] }).available, false);
  assert.equal(campaignFromSnapshot(undefined).available, false);
  assert.equal(campaignFromSnapshot({}).available, false);
});

test("a present section with no records is still unavailable", () => {
  const campaign = campaignFromSnapshot(snapshotWith([]));
  assert.equal(campaign.available, false);
  assert.deepEqual(campaign.campaigns, []);
});

test("a record carries its programme, stage and the reason for it", () => {
  const [entry] = campaignFromSnapshot(snapshotWith([RECORD])).campaigns;

  assert.equal(entry.programmeId, "hackerone-gitlab-public");
  assert.equal(entry.currentStage, "programme");
  assert.match(entry.because, /no human verification/);
  assert.equal(entry.nextAction, "review the compiled contract");
  assert.equal(entry.posture, "LOCAL_FIXTURE");
  assert.equal(entry.practisedTopics, 0);
});

test("the compact stage field expands to every stage in order", () => {
  const [entry] = campaignFromSnapshot(snapshotWith([RECORD])).campaigns;

  assert.equal(entry.stages.length, 7);
  assert.deepEqual(
    entry.stages.map((stage) => stage.name),
    ["programme", "curriculum", "study", "plan", "evidence", "draft", "submission"],
  );
  assert.equal(entry.stages[0].marker, "gov");
  assert.equal(entry.stages[1].marker, "todo");
});

test("only the exact string true means blocked by governance", () => {
  const cases = [
    ["true", true],
    ["false", false],
    ["True", false],
    ["", false],
    [undefined, false],
  ];
  for (const [value, expected] of cases) {
    const attributes = { ...RECORD.attributes, blocked_by_governance: value };
    const [entry] = campaignFromSnapshot(
      snapshotWith([{ ...RECORD, attributes }]),
    ).campaigns;
    assert.equal(entry.blockedByGovernance, expected, `for ${JSON.stringify(value)}`);
  }
});

test("a malformed stage marker degrades to not-done rather than satisfied", () => {
  const attributes = { ...RECORD.attributes, stages: "programme,curriculum=ok" };
  const [entry] = campaignFromSnapshot(
    snapshotWith([{ ...RECORD, attributes }]),
  ).campaigns;

  // "programme" has no "=marker" at all. Reading that as satisfied would show
  // a green stage nobody reported, which is the failure this guards against.
  assert.equal(entry.stages[0].marker, "todo");
  assert.equal(entry.stages[1].marker, "ok");
});

test("several programmes each get their own entry", () => {
  const second = { ...RECORD, id: "campaign:b", title: "bugcrowd-ynab-public" };
  const campaign = campaignFromSnapshot(snapshotWith([RECORD, second]));

  assert.equal(campaign.available, true);
  assert.deepEqual(
    campaign.campaigns.map((entry) => entry.programmeId),
    ["hackerone-gitlab-public", "bugcrowd-ynab-public"],
  );
});
