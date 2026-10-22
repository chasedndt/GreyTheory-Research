/**
 * A worked example of a research workspace, for when you have none yet.
 *
 * This is sample data and is labelled as such everywhere it appears. It exists
 * because a real workspace cannot be created until a programme's contract has
 * been compiled clean *and* reviewed by a person - so until you review one,
 * there is nothing truthful to render, and an empty panel would not show you
 * what the surface is for.
 *
 * It is deliberately written in the same view-model shape the real adapter
 * produces, so it travels through the identical component. What you see here is
 * what your own workspace will look like, not an artist's impression of it.
 *
 * Nothing here resembles a real programme or a real fingerprint. The ids say
 * "example" so that a screenshot of this can never be mistaken for evidence.
 */

export const EXAMPLE_WORKSPACE = {
  id: "example-workspace",
  title: "Session handling on an example programme",
  programmeId: "example-programme",
  status: "active",
  posture: "LOCAL_FIXTURE",
  // The first goal is what the read model surfaces as the workspace's line.
  goal:
    "Understand how session identifiers are issued, and whether logging out "
    + "invalidates them server-side or only clears the browser.",
  authorityRef: "example",
  counts: {
    sessions: 1,
    activeSessions: 0,
    hypotheses: 3,
    actionRequests: 2,
    actionReceipts: 2,
    lessons: 1,
  },
};

/**
 * What a person must do before a real workspace can exist. Shown beside the
 * example so the gap reads as a sequence of steps rather than a refusal.
 */
export const WORKSPACE_PREREQUISITES = [
  {
    id: "compiled",
    label: "The programme is compiled from saved sources",
    detail: "All three of your registered programmes already satisfy this.",
    met: true,
  },
  {
    id: "clean",
    label: "Its contract compiles without unresolved questions",
    detail:
      "GitLab and the MCP SDK are clean. YNAB is blocked on two questions a "
      + "person has to settle first.",
    met: true,
  },
  {
    id: "reviewed",
    label: "A person has reviewed it",
    detail:
      "This is the step that is outstanding, and the one only you can take. "
      + "Reviewing records that you read the compiled scope beside its sources.",
    met: false,
  },
  {
    id: "fresh",
    label: "That review is less than seven days old",
    detail: "Scope changes, so a review has a shelf life and then lapses.",
    met: false,
  },
];
