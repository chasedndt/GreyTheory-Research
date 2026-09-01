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
