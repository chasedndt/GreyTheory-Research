import assert from "node:assert/strict";
import test from "node:test";
import {
  agentToolAuthorizationCase,
  evaluateAuthorization,
  evaluateObjectOwnership,
  objectOwnershipCase,
  runAuthorizationSimulation,
  runCasePackSimulation,
  runObjectOwnershipSimulation,
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

test("object ownership simulation isolates one ownership variable without external action", () => {
  const [ownObject, vulnerablePath, deniedPath] = runObjectOwnershipSimulation();

  assert.equal(ownObject.decision, "ALLOW_OWN_OBJECT");
  assert.equal(ownObject.propertyHeld, true);
  assert.equal(vulnerablePath.decision, "DEMONSTRATE_MISSING_OWNERSHIP_CHECK");
  assert.equal(vulnerablePath.propertyHeld, false);
  assert.equal(vulnerablePath.controlledEffectObserved, true);
  assert.equal(deniedPath.decision, "DENY_CROSS_OWNER");
  assert.equal(deniedPath.propertyHeld, true);
  assert.ok([ownObject, vulnerablePath, deniedPath].every((result) => result.externalAction === false));
  assert.deepEqual(runCasePackSimulation("api-object-ownership"), runObjectOwnershipSimulation());
});

test("identifier knowledge does not replace the actor-object ownership check", () => {
  const denied = evaluateObjectOwnership(objectOwnershipCase, {
    id: "CTRL-OWNER-004",
    label: "Unknown cross-owner reference",
    actor: "account-a",
    objectId: "note-b",
    ownershipCheck: true,
  });

  assert.equal(denied.allowed, false);
  assert.equal(denied.owner, "account-b");
  assert.equal(denied.decision, "DENY_CROSS_OWNER");
});
