// What a programme's compiled scope asks you to understand.
//
// Extracted from App.jsx so the bounty workspace can render it for the single
// selected bounty. Given one programme its own switcher does not render, which
// is how the workspace ends up owning selection without this component needing
// to know that it exists.
//
// Imports its icon directly rather than from App.jsx, which would be circular.

import { useState } from "react";
import { ShieldCheck } from "@phosphor-icons/react/dist/csr/ShieldCheck";
import HelpHint from "./HelpHint.jsx";
import { lessonForCard } from "./lessons/index.js";

// What to look for, drawn from the written lesson rather than restated here.
// Duplicating teaching copy into this panel would put two versions of the same
// explanation in the product, and the one nobody maintains is the one a learner
// would end up reading.
function hintFor(cardId) {
  const lesson = lessonForCard(cardId);
  if (!lesson) {
    // Said plainly rather than rendering nothing: a silent gap looks like the
    // topic needs no explanation, when in fact none has been written.
    return (
      <p>
        No lesson is written for this topic yet. It was still chosen by this
        programme&rsquo;s own scope &mdash; the line below says which assets
        matched &mdash; but there is no guided material behind it so far.
      </p>
    );
  }
  return (
    <>
      <p>{lesson.oneLine}</p>
      {lesson.proofLooksLike?.length > 0 && (
        <>
          <em>Proof looks like</em>
          <ul>{lesson.proofLooksLike.map((item) => <li key={item}>{item}</li>)}</ul>
        </>
      )}
    </>
  );
}

export default function StudyPlan({ curriculum }) {
  const [programmeId, setProgrammeId] = useState(null);
  if (!curriculum?.available || !curriculum.programmes.length) return null;

  const active =
    curriculum.programmes.find((entry) => entry.programmeId === programmeId)
    || curriculum.programmes[0];

  return (
    <section className="surface study-plan" aria-labelledby="study-plan-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Selected from real programme scope</span>
          <h2 id="study-plan-title">What this programme will ask of you</h2>
        </div>
        {curriculum.programmes.length > 1 && (
          <div className="study-plan__switch" role="group" aria-label="Programme">
            {curriculum.programmes.map((entry) => (
              <button key={entry.programmeId} type="button"
                className={entry.programmeId === active.programmeId ? "is-selected" : ""}
                aria-pressed={entry.programmeId === active.programmeId}
                onClick={() => setProgrammeId(entry.programmeId)}>{entry.programmeId}</button>
            ))}
          </div>
        )}
      </div>
      <ol className="study-plan__topics">
        {active.topics.map((topic) => (
          <li key={topic.cardId}>
            <span className="study-plan__rank">{topic.rank}</span>
            <div>
              <strong>{topic.cardId}</strong>
              <HelpHint label="What to look for">{hintFor(topic.cardId)}</HelpHint>
              <p>{topic.reason}</p>
              {topic.matchedAssets.length > 0
                ? <small>Because the scope lists {topic.matchedAssets.join(", ")}</small>
                : topic.matchedContext.length > 0
                  ? <small>From the programme's own description: {topic.matchedContext.join(", ")}</small>
                  : null}
            </div>
          </li>
        ))}
      </ol>
      {active.notes.length > 0 && (
        <div className="study-plan__notes">
          <span className="eyebrow">This programme prohibits</span>
          <ul>{active.notes.map((note) => <li key={note}>{note}</li>)}</ul>
        </div>
      )}
      <footer className="study-plan__boundary">
        <ShieldCheck />
        <p>Selected by reading compiled programme authority. This is a teaching aid, not a test plan: it says what to understand, never what to attack, and grants no permission to touch any asset.</p>
      </footer>
    </section>
  );
}
