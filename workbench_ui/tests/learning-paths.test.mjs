import assert from "node:assert/strict";
import test from "node:test";

import { LEARNING_TOPICS, SKILL_TRACKS, topicById } from "../src/learningPaths.js";
import { INTEGRATION_GUARDRAILS, PROGRAMME_CONNECTORS, PUBLIC_INTELLIGENCE_SOURCES } from "../src/intelligenceSources.js";

test("every learning topic has its own content, progression, and real resources", () => {
  assert.equal(LEARNING_TOPICS.length, 4);
  assert.equal(new Set(LEARNING_TOPICS.map((topic) => topic.lede)).size, LEARNING_TOPICS.length);
  for (const topic of LEARNING_TOPICS) {
    assert.equal(topic.principles.length, 4);
    assert.equal(topic.checkpoints.length, 4);
    assert.equal(topic.practiceChecks.length, 2);
    assert.ok(topic.practiceChecks.every((item) => item.options.length === 3));
    assert.ok(topic.practiceChecks.every((item) => Number.isInteger(item.answer) && item.options[item.answer]));
    assert.ok(topic.practiceChecks.every((item) => item.explanation.length > 30));
    assert.equal(topic.lessons.length, 4);
    assert.ok(topic.resources.every((resource) => resource[2].startsWith("https://")));
  }
  assert.equal(topicById("prompt-boundaries").title, "Prompt-injection boundaries");
  assert.equal(topicById("object-authorization").title, "API object authorization");
});

test("skill tracks expose a complete beginner-to-transfer path", () => {
  assert.deepEqual(SKILL_TRACKS.map((track) => track.lessons.length), [8, 8, 8]);
  assert.ok(SKILL_TRACKS.every((track) => track.completed < track.lessons.length));
  assert.ok(SKILL_TRACKS.every((track) => track.lessons.at(-1)[1] === "Transfer"));
});

test("integration catalogue separates public intelligence from account connectors", () => {
  assert.ok(PUBLIC_INTELLIGENCE_SOURCES.length >= 5);
  assert.ok(PUBLIC_INTELLIGENCE_SOURCES.every((source) => !/target|scan|exploit/i.test(source.mode)));
  assert.ok(PROGRAMME_CONNECTORS.every((source) => source.posture !== "Connected"));
  assert.ok(INTEGRATION_GUARDRAILS.some((rule) => /No hostname/i.test(rule)));
});
