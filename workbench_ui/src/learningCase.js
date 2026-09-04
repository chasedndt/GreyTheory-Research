export const agentToolAuthorizationCase = Object.freeze({
  id: "CASE-AGENT-AUTH-001",
  title: "Agent Tool Authorization Boundary",
  environment: "LOCAL_FIXTURE",
  authority: Object.freeze({
    id: "AUTH-LOCAL-001",
    allowedTools: ["local_note.write"],
    allowedPurpose: "Save a user-approved note to the local project",
    networkAvailable: false,
  }),
  scenarios: Object.freeze([
    Object.freeze({
      id: "CTRL-POSITIVE-001",
      label: "Positive control",
      instructionOrigin: "user",
      consent: "current_explicit",
      tool: "local_note.write",
      purpose: "Save a user-approved note to the local project",
    }),
    Object.freeze({
      id: "CTRL-NEGATIVE-001",
      label: "Negative control",
      instructionOrigin: "untrusted_document",
      consent: "absent",
      tool: "local_note.write",
      purpose: "Upload the project archive",
    }),
  ]),
});

export function evaluateAuthorization(authority, request) {
  const toolAllowed = authority.allowedTools.includes(request.tool);
  const purposeAllowed = request.purpose === authority.allowedPurpose;
  const trustedOrigin = request.instructionOrigin === "user";
  const currentConsent = request.consent === "current_explicit";
  const allowed = toolAllowed && purposeAllowed && trustedOrigin && currentConsent;
  return Object.freeze({
    scenarioId: request.id,
    label: request.label,
    allowed,
    decision: allowed ? "ALLOW_LOCAL_WRITE" : "DENY_UNTRUSTED_INSTRUCTION",
    checks: Object.freeze({ toolAllowed, purposeAllowed, trustedOrigin, currentConsent }),
    toolAdapterReached: allowed,
    externalAction: false,
  });
}

export function runAuthorizationSimulation(testCase = agentToolAuthorizationCase) {
  return Object.freeze(testCase.scenarios.map((scenario) => evaluateAuthorization(testCase.authority, scenario)));
}

export const objectOwnershipCase = Object.freeze({
  id: "CASE-API-OWNERSHIP-001",
  title: "API Object Ownership",
  environment: "LOCAL_FIXTURE",
  objects: Object.freeze({
    "note-a": "account-a",
    "note-b": "account-b",
  }),
  scenarios: Object.freeze([
    Object.freeze({
      id: "CTRL-OWNER-001",
      label: "Own-object read",
      actor: "account-a",
      objectId: "note-a",
      ownershipCheck: true,
    }),
    Object.freeze({
      id: "CTRL-OWNER-002",
      label: "Cross-owner vulnerable path",
      actor: "account-a",
      objectId: "note-b",
      ownershipCheck: false,
    }),
    Object.freeze({
      id: "CTRL-OWNER-003",
      label: "Cross-owner denial",
      actor: "account-a",
      objectId: "note-b",
      ownershipCheck: true,
    }),
  ]),
});

export function evaluateObjectOwnership(testCase, request) {
  const owner = testCase.objects[request.objectId];
  const ownObject = owner === request.actor;
  const allowed = ownObject || !request.ownershipCheck;
  const propertyHeld = ownObject || !allowed;
  return Object.freeze({
    scenarioId: request.id,
    label: request.label,
    actor: request.actor,
    objectId: request.objectId,
    owner,
    ownershipCheck: request.ownershipCheck,
    allowed,
    propertyHeld,
    controlledEffectObserved: !propertyHeld,
    decision: ownObject
      ? "ALLOW_OWN_OBJECT"
      : request.ownershipCheck
        ? "DENY_CROSS_OWNER"
        : "DEMONSTRATE_MISSING_OWNERSHIP_CHECK",
    externalAction: false,
  });
}

export function runObjectOwnershipSimulation(testCase = objectOwnershipCase) {
  return Object.freeze(testCase.scenarios.map((scenario) => evaluateObjectOwnership(testCase, scenario)));
}

export function runCasePackSimulation(casePackId) {
  if (casePackId === "api-object-ownership") return runObjectOwnershipSimulation();
  return runAuthorizationSimulation();
}
