// Practice titles: field-flavoured ranks earned by doing the work.
//
// A title is the gamified reward. It is also the single easiest place in this
// product to accidentally make a competence claim, so two rules constrain it:
//
//   1. **A title never travels without its criterion.** "Pentester · 8 of 12
//      scenarios practised" is a rank with its basis attached. "Pentester"
//      alone reads as a credential, so the render always shows both.
//   2. **No title uses the vocabulary of assessment.** Nothing here says
//      master, expert, certified, qualified, or accredited. Those belong to
//      the six evidence-bound human assessments and are never automatic.
//
// Titles are derived from participation the learner actually produced, so an
// unused install has the entry-level title and no amount of clicking changes
// that without running a fixture.
//
// A third rule, learned from a first draft that read as a grab bag: **the
// ladder has one voice.** Every rung is a short noun phrase naming a stance a
// researcher can occupy, so the sequence reads as a progression rather than as
// nine unrelated labels. "Full Deck" also went, because the idiom it borrows
// means the opposite of what the rank is for.

/** Ordered ladder. `need` is distinct scenarios practised. */
export const TITLES = [
  { id: "day-one", need: 0, name: "Day One", blurb: "Reading before touching. The right order." },
  { id: "first-contact", need: 1, name: "First Contact", blurb: "One scenario run end to end." },
  { id: "scope-reader", need: 2, name: "Scope Reader", blurb: "Authority before action." },
  { id: "white-hat", need: 3, name: "White Hat", blurb: "Practising inside the lines." },
  { id: "tripwire", need: 4, name: "Tripwire", blurb: "Notices what others walk past." },
  { id: "evidence-keeper", need: 6, name: "Evidence Keeper", blurb: "Claims that survive a sceptic." },
  { id: "control-runner", need: 8, name: "Pentester", blurb: "Controlled tests, attributable results." },
  { id: "threat-modeller", need: 10, name: "Threat Modeller", blurb: "Ranks by consequence, not curiosity." },
  { id: "full-sweep", need: 12, name: "Full Sweep", blurb: "Every scenario in the local deck practised." },
];

/** Streak flourishes. Cosmetic, and equally tied to a visible number. */
export const STREAK_FLOURISHES = [
  { need: 30, name: "Relentless" },
  { need: 14, name: "Unbroken" },
  { need: 7, name: "In Rhythm" },
  { need: 3, name: "Rolling" },
];

/** The title earned by this participation, with the criterion that earned it. */
export function titleFor(participation) {
  // `= {}` would not cover an explicit null, which a caller can pass.
  const source = participation || {};
  const practised = Number(source.cardsPractised ?? 0) || 0;
  const streak = Number(source.streak ?? 0) || 0;

  let earned = TITLES[0];
  for (const title of TITLES) {
    if (practised >= title.need) earned = title;
  }
  const next = TITLES.find((title) => title.need > practised) || null;
  const flourish = STREAK_FLOURISHES.find((item) => streak >= item.need) || null;

  return {
    ...earned,
    // The basis travels with the title, always.
    criterion: `${practised} of 12 scenarios practised`,
    flourish: flourish ? flourish.name : "",
    flourishCriterion: flourish ? `${streak} day streak` : "",
    next: next
      ? { name: next.name, remaining: next.need - practised }
      : null,
    // Restated so a consumer cannot mistake a rank for an assessment.
    awardsMastery: false,
    isCertification: false,
  };
}

/** Progress toward the next title, 0–1, for a ring or bar. */
export function titleProgress(participation) {
  const practised = Number((participation || {}).cardsPractised ?? 0) || 0;
  const earned = [...TITLES].reverse().find((title) => practised >= title.need) || TITLES[0];
  const next = TITLES.find((title) => title.need > practised);
  if (!next) return 1;
  const span = next.need - earned.need;
  return span <= 0 ? 1 : Math.min(1, Math.max(0, (practised - earned.need) / span));
}
