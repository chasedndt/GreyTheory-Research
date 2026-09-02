export const CASE_PACKS = [
  {
    id: "agent-authorization-boundary",
    version: "1.0.0",
    number: "01",
    title: "Agent Tool Authorization Boundary",
    status: "Ready locally",
    tone: "green",
    duration: "35 min",
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
  "Durable egress and OS key binding accepted",
  "Programme bundle reviewed without ambiguity",
  "Operator explicitly raises the posture",
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
    duration: "35 min",
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
