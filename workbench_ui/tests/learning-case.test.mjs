import assert from "node:assert/strict";
import test from "node:test";
import {
  agentToolAuthorizationCase,
  evaluateAuthorization,
  runAuthorizationSimulation,
} from "../src/learningCase.js";

test("paired controls allow explicit local consent and deny injected instructions", () => {
  const [positive, negative] = runAuthorizationSimulation();

  assert.equal(positive.allowed, true);
  assert.equal(positive.decision, "ALLOW_LOCAL_WRITE");
  assert.equal(positive.toolAdapterReached, true);
  assert.equal(positive.externalAction, false);

  assert.equal(negative.allowed, false);
  assert.equal(negative.decision, "DENY_UNTRUSTED_INSTRUCTION");
  assert.equal(negative.toolAdapterReached, false);
  assert.equal(negative.externalAction, false);
});

test("tool availability cannot replace trusted origin, purpose, and consent", () => {
  const denied = evaluateAuthorization(agentToolAuthorizationCase.authority, {
    id: "CTRL-NEGATIVE-002",
    instructionOrigin: "untrusted_document",
    consent: "absent",
    tool: "local_note.write",
    purpose: "Save a user-approved note to the local project",
  });

  assert.equal(denied.checks.toolAllowed, true);
  assert.equal(denied.checks.purposeAllowed, true);
  assert.equal(denied.checks.trustedOrigin, false);
  assert.equal(denied.checks.currentConsent, false);
  assert.equal(denied.allowed, false);
});
