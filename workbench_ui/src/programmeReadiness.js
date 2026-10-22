/**
 * What to do next with a registered programme.
 *
 * Kept out of the component for the same reason `reviewability` is: this is a
 * decision, not a shape, and it is the sentence a learner actually acts on. The
 * UI tests here are pure JS with no React harness, so a rule written inside JSX
 * is a rule nobody can test.
 *
 * The constraint worth remembering: the programmes section does not carry an
 * ambiguity count, so nothing here may state how many questions are
 * outstanding. Naming a number the data does not contain would be inventing
 * precision, which is the failure this project cares most about avoiding.
 */

export const PROGRAMME_STEPS = {
  draft: {
    step: "Compile it from its saved sources",
    because:
      "It exists as a record but has not been compiled into a contract yet, so "
      + "there is no scope to read and nothing to review.",
    tone: "attention",
  },
  blocked: {
    step: "Settle its open questions, then recompile",
    because:
      "Its contract did not compile clean, so there is nothing yet that a "
      + "review could confirm. Reviewing does not resolve ambiguity.",
    tone: "blocked",
  },
  pending_review: {
    step: "Review the compiled scope",
    because:
      "It compiled clean and is waiting for a person to read the scope beside "
      + "the sources it came from. This is the only step nobody can take for you.",
    tone: "attention",
  },
  verified: {
    step: "Open a research workspace",
    because:
      "A person has reviewed this contract, so work recorded against it "
      + "inherits authority somebody actually confirmed.",
    tone: "ready",
  },
};

const UNKNOWN = {
  step: "Inspect this programme",
  because: "Its contract state was not reported, so nothing can be assumed about it.",
  tone: "unknown",
};

export function programmeNextStep(programme) {
  if (!programme) return UNKNOWN;

  // A contract counts as verified only when a person is also recorded as
  // having reviewed it. The two facts are stored separately and both are
  // checked, because a contract that reads verified with nobody named is
  // precisely what the review gate exists to catch.
  if (programme.contractStatus === "verified") {
    return programme.humanReviewed
      ? PROGRAMME_STEPS.verified
      // Falls to review rather than through to the table below: a plain lookup
      // on "verified" would hand back the step the check above just declined,
      // quietly defeating the two-fact rule and telling someone to open a
      // workspace the store would refuse.
      : PROGRAMME_STEPS.pending_review;
  }

  return PROGRAMME_STEPS[programme.contractStatus] || UNKNOWN;
}
