/**
 * Where you actually are, shown as the first thing on the page.
 *
 * This is not a tour and not a checklist. Every step is marked done because the
 * underlying fact is true - the registry records a human review, the lesson
 * store records worked-through checks, the shortlist holds an active entry -
 * and never because someone clicked "next". A wizard that congratulates you for
 * steps you have not taken is the same fabrication problem in a friendlier
 * costume, and it would be worse here than most places: the whole product is an
 * argument that claims must be backed by something.
 *
 * Because it reflects real state it does not need dismissing, and it does not
 * disappear once "complete". It becomes a status board: open the application
 * cold in a month and it still says what is done and what is next.
 *
 * The order is the order the system actually requires. You cannot open a
 * research workspace before a contract is reviewed, because a workspace
 * inherits its authority from that review - so "review a programme" genuinely
 * precedes it rather than being an arbitrary tutorial sequence.
 */

//: Only the "have you seen this" preference is stored. Progress itself is never
//: stored here: it is read from the things that actually happened.
export const ONBOARDING_STORAGE_KEY = "greytheory.onboardingCollapsed";

export function readCollapsed(storage) {
  const target = storage || (() => { try { return globalThis.localStorage; } catch { return null; } })();
  if (!target) return false;
  try {
    return target.getItem(ONBOARDING_STORAGE_KEY) === "yes";
  } catch {
    return false;
  }
}

export function writeCollapsed(collapsed, storage) {
  const target = storage || (() => { try { return globalThis.localStorage; } catch { return null; } })();
  if (!target) return Boolean(collapsed);
  try {
    target.setItem(ONBOARDING_STORAGE_KEY, collapsed ? "yes" : "no");
  } catch {
    /* storage optional */
  }
  return Boolean(collapsed);
}

/**
 * The five things that take someone from a cold install to real research.
 *
 * `done` is computed from evidence every time. Nothing here is remembered.
 */
export function onboardingSteps({
  connected = false,
  programmes = null,
  completedLessons = [],
  shortlist = null,
  directory = null,
} = {}) {
  const registered = programmes?.programmes || [];
  const reviewed = registered.filter((item) => item.humanReviewed);
  const activeShortlist = shortlist?.active || [];
  const checkedPages = directory?.lookups || [];

  return [
    {
      id: "connect",
      title: "Connect the local application",
      why:
        "Everything you do is recorded on this machine and nowhere else. Until "
        + "the application is connected you are looking at a preview: nothing "
        + "you do is kept.",
      action: "Paste the session token your server printed when it started.",
      route: "settings",
      done: Boolean(connected),
      // Stated because the friction is real and the reason is not obvious.
      note:
        "The token is asked for on every load on purpose. It is the only thing "
        + "standing between any other program on this machine and your research, "
        + "so it is not stored in the browser.",
    },
    {
      id: "programmes",
      title: "See the programmes you have",
      why:
        "A programme is a bug bounty scope compiled from sources saved on this "
        + "machine. It is the thing that decides what may ever be tested.",
      action: registered.length
        ? `${registered.length} are compiled and waiting on the home page.`
        : "None are registered yet.",
      route: "programmes",
      done: registered.length > 0,
    },
    {
      id: "learn",
      title: "Start the curriculum",
      why:
        "Twenty-eight lessons from no background to independent work. Each is "
        + "read before it is tested, and a wrong answer gives you a hint rather "
        + "than the answer.",
      action: completedLessons.length
        ? `${completedLessons.length} worked through so far.`
        : "Begin with Security ethics - it is the first lesson for a reason.",
      route: "learn",
      done: completedLessons.length > 0,
    },
    {
      id: "review",
      title: "Review a programme's scope",
      why:
        "Reviewing records that a person read the compiled scope beside the "
        + "sources it came from. It is the one step nobody can take for you, and "
        + "nothing real can happen before it.",
      action: reviewed.length
        ? `${reviewed.length} reviewed.`
        : "Open a bounty, read its source documents, then record your review.",
      route: "mission",
      done: reviewed.length > 0,
    },
    {
      id: "shortlist",
      title: "Choose what you are working on",
      why:
        "Shortlisting records an intention. It grants no authority and changes "
        + "nothing about scope - it simply keeps your working set honest.",
      action: activeShortlist.length
        ? `${activeShortlist.length} on your active list.`
        : `Add one from the board${checkedPages.length ? "" : " - and check its page while you are there"}.`,
      route: "mission",
      done: activeShortlist.length > 0,
    },
  ];
}

/** The first step not yet done, or null when everything is. */
export function currentStep(steps = []) {
  return steps.find((step) => !step.done) || null;
}

export function onboardingProgress(steps = []) {
  const done = steps.filter((step) => step.done).length;
  return {
    done,
    total: steps.length,
    percent: steps.length === 0 ? 0 : Math.round((done / steps.length) * 100),
    complete: steps.length > 0 && done === steps.length,
  };
}
