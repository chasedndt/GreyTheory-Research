export const CASE_PACKS = [
  {
    id: "agent-authorization-boundary",
    version: "1.1.0",
    number: "01",
    title: "Agent Tool Authorization Boundary",
    status: "Ready locally",
    tone: "green",
    duration: "30 min",
    primaryCard: "tool-authorization-failure",
    cards: ["IDOR / BOLA", "Indirect prompt injection", "Tool authorization"],
    objective: "Separate capability from authority, run paired controls, preserve a server-issued fixture receipt, and explain the evidence limits.",
  },
  {
    id: "api-object-ownership",
    version: "1.0.0",
    number: "02",
    title: "API Object Ownership",
    status: "Queued",
    tone: "blue",
    duration: "50 min",
    primaryCard: "idor-bola",
    cards: ["HTTP identity", "IDOR / BOLA", "Business logic"],
    objective: "Use two synthetic accounts to test ownership invariants and produce limitation-aware evidence.",
  },
  {
    id: "session-role-transition",
    version: "1.0.0",
    number: "03",
    title: "Session and Role Transition",
    status: "Queued",
    tone: "blue",
    duration: "55 min",
    primaryCard: "session-management",
    cards: ["Session lifecycle", "BFLA", "Workflow authorization"],
    objective: "Test how logout, rotation, role changes, and workflow state affect permission.",
  },
];

export const LIVE_PROGRAMME_GATES = [
  "Installed Windows workbench accepted",
  "Full Ubuntu worker host proof accepted",
  "Durable egress and approved OS key/recovery accepted",
  "Programme bundle reviewed without ambiguity",
  "Operator explicitly raises the posture",
];

export const MISSION_SEGMENTS = [
  {
    id: "learn",
    label: "Learn",
    minutes: 8,
    outcome: "Explain why capability does not create authority.",
    deliverable: "Two correct practice checks and a plain-language boundary explanation.",
    boundary: "Read and reason only; external material remains untrusted input.",
  },
  {
    id: "practise",
    label: "Practise",
    minutes: 10,
    outcome: "Compare consented and untrusted instructions in one controlled fixture.",
    deliverable: "A positive control, negative control, and local policy decision.",
    boundary: "LOCAL_FIXTURE only; no hostname, account, or programme request.",
  },
  {
    id: "prove",
    label: "Prove",
    minutes: 5,
    outcome: "Connect the observed decision to inspectable evidence.",
    deliverable: "A server-issued receipt with policy and adapter outcomes.",
    boundary: "A receipt proves this fixture run, not a real-world vulnerability.",
  },
  {
    id: "reflect",
    label: "Reflect",
    minutes: 4,
    outcome: "State what changed and what remains unknown.",
    deliverable: "A limitation-aware reflection in the learner's own words.",
    boundary: "AI can prompt reflection but cannot write or approve it for the learner.",
  },
  {
    id: "assess",
    label: "Assess",
    minutes: 3,
    outcome: "Choose and defend the least-authority decision in a new scenario.",
    deliverable: "An independent answer ready for later human review.",
    boundary: "Practice completion is not mastery; a human assessment remains required.",
  },
];

export const PROGRAMME_READINESS = [
  {
    id: "gitlab",
    platform: "HackerOne",
    name: "GitLab public programme",
    source: "2026-08-09 source bundle",
    sourceState: "Saved snapshot",
    reviewState: "Human review required",
    caseState: "Offline case candidate",
    nextAction: "Resolve in-scope asset boundaries before deriving a synthetic case.",
    blocked: false,
  },
  {
    id: "ynab",
    platform: "Bugcrowd",
    name: "YNAB public programme",
    source: "2026-08-09 source bundle",
    sourceState: "Saved snapshot",
    reviewState: "Ambiguity blocked",
    caseState: "Not eligible",
    nextAction: "Preserve the target-group conflict and request a human scope decision.",
    blocked: true,
  },
  {
    id: "mcp",
    platform: "Direct VDP",
    name: "MCP Python SDK",
    source: "2026-08-09 source bundle",
    sourceState: "Policy source only",
    reviewState: "Human review required",
    caseState: "Learning reference",
    nextAction: "Use the policy as reading material; do not infer testing authority.",
    blocked: false,
  },
];

export const DEMO_RUNS = [
  {
    id: "guided-preview",
    title: "Guided preview",
    duration: "8–10 min",
    status: "Ready",
    copy: "A concise walkthrough from authority to receipt for product demonstrations and onboarding.",
  },
  {
    id: "learner-mission",
    title: "Complete learner mission",
    duration: "30 min",
    status: "Ready",
    copy: "The full Learn → Practise → Prove → Reflect → Assess path with explicit evidence limits.",
  },
  {
    id: "transfer-check",
    title: "Independent transfer check",
    duration: "20 min",
    status: "Requires human review",
    copy: "A distinct scenario that tests whether the method transfers without hidden assistance.",
  },
];

export function casePackById(id) {
  return CASE_PACKS.find((item) => item.id === id) || CASE_PACKS[0];
}
