// Learn: the curriculum as a path you walk, not a grid you guess at.
//
// This replaces a page that opened with two scenario questions and four
// "confirm you can explain this" boxes behind about a hundred words of
// summary. Questions before material is interrogation, not teaching - and the
// material it should have been using existed the whole time, reachable only
// from somewhere else.
//
// The rule the page now enforces: you are never asked about something you were
// not first taught. Every entry opens the real lesson - concept, the
// traditional lens, the agent-era lens, a worked example, what proof would look
// like - and only then its checks, where a wrong answer buys a hint rather than
// the answer.
//
// Progress here is a local practice record. It awards no mastery, proves no
// skill, and changes no scope. Mastery stays six separately assessed dimensions
// recorded by a person.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { BookOpen } from "@phosphor-icons/react/dist/csr/BookOpen";
import { Check } from "@phosphor-icons/react/dist/csr/Check";
import { ArrowRight } from "@phosphor-icons/react/dist/csr/ArrowRight";
// LockKey rather than Lock: this Phosphor build does not ship a `Lock` export.
import { LockKey } from "@phosphor-icons/react/dist/csr/LockKey";
import { ShieldCheck } from "@phosphor-icons/react/dist/csr/ShieldCheck";
import { curriculumPath, nextLesson, overallProgress } from "./curriculumPath.js";
import { lessonById } from "./lessons/index.js";
import "./CurriculumView.css";

const STATE_LABEL = {
  done: "Done",
  current: "Start here",
  open: "Open",
  later: "Comes later",
};

function TrackProgress({ done, total }) {
  const percent = total === 0 ? 0 : Math.round((done / total) * 100);
  return (
    <div className="curriculum-track__progress" role="img" aria-label={`${done} of ${total} lessons worked through`}>
      <span style={{ width: `${percent}%` }} />
      <small>{done}/{total}</small>
    </div>
  );
}

export default function CurriculumView({ completed, onOpenLesson, onOpenLab }) {
  const tracks = curriculumPath(completed);
  const overall = overallProgress(completed);
  const next = nextLesson(completed);
  const nextLessonRecord = next ? lessonById(next.step.id) : null;
  // The safe lab opens once something has actually been read. This gate used to
  // live on the old Learn page; it is re-homed rather than dropped, because it
  // also carries the guided journey from its learn stage into practise.
  const labReady = (completed?.length || 0) > 0;

  return (
    <div className="content-page curriculum-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">Learn &middot; from no background to independent work</span>
          <h1>Your curriculum</h1>
          <p>
            Twenty-eight lessons in three tracks, each read before it is tested.
            Nothing here asks you about something it has not taught you first.
          </p>
        </div>
        <div className="time-chip"><BookOpen />{overall.done} of {overall.total} worked through</div>
      </header>

      {next && nextLessonRecord && (
        <section className="surface curriculum-next" aria-labelledby="next-title">
          <div>
            <span className="eyebrow">{next.track.title} &middot; lesson {next.step.position} of {next.track.total}</span>
            <h2 id="next-title">{next.step.title}</h2>
            <p className="curriculum-next__line">{next.step.oneLine}</p>
            <div className="tag-row">
              <Pill>{next.step.level}</Pill>
              <Pill tone="blue">{next.step.duration}</Pill>
              <Pill tone="green">{next.step.checks} checks</Pill>
            </div>
          </div>
          <button
            type="button"
            className="button button--primary"
            onClick={() => onOpenLesson(nextLessonRecord)}
          >
            {overall.done === 0 ? "Begin here" : "Continue"} <ArrowRight />
          </button>
        </section>
      )}

      <div className="curriculum-tracks">
        {tracks.map((track) => (
          <section key={track.id} className="surface curriculum-track" aria-labelledby={`track-${track.id}`}>
            <div className="section-heading">
              <div>
                <span className="eyebrow">Track</span>
                <h2 id={`track-${track.id}`}>{track.title}</h2>
              </div>
              <TrackProgress done={track.done} total={track.total} />
            </div>

            <ol className="curriculum-steps" aria-label={`${track.title} lessons in order`}>
              {track.steps.map((step) => {
                const record = lessonById(step.id);
                // "later" is never disabled: it is signposting, not a barrier.
                // Someone who wants to read ahead is learning, not cheating.
                return (
                  <li key={step.id} className={`is-${step.state}`}>
                    <button type="button" onClick={() => record && onOpenLesson(record)}>
                      <span className="curriculum-steps__mark" aria-hidden="true">
                        {step.state === "done" ? <Check /> : step.state === "later" ? <LockKey /> : step.position}
                      </span>
                      <span className="curriculum-steps__body">
                        <strong>{step.title}</strong>
                        <small>{step.level} &middot; {step.duration} &middot; {step.checks} checks</small>
                        <p>{step.oneLine}</p>
                      </span>
                      <span className={`curriculum-steps__state is-${step.state}`}>
                        {STATE_LABEL[step.state]}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ol>
          </section>
        ))}
      </div>

      <section className="surface curriculum-practise">
        <div>
          <span className="eyebrow">When you have read something</span>
          <h2>Take it into the safe lab</h2>
          <p>
            The lab runs synthetic fixtures on this machine. It proves you can
            apply what a lesson taught, against a controlled case rather than
            anyone&rsquo;s live system.
          </p>
        </div>
        <button
          type="button"
          className="button button--primary"
          onClick={onOpenLab}
          disabled={!labReady}
        >
          Open the safe lab <ArrowRight />
        </button>
        <small>
          {labReady
            ? "This unlocks practice only; it does not award mastery."
            : "Work through one lesson first. Practising something you have not read is guessing, not learning."}
        </small>
      </section>

      <footer className="surface curriculum-boundary">
        <ShieldCheck />
        <p>
          Working through a lesson records that you did it on this machine. It is
          a practice record and nothing more &mdash; it awards no mastery,
          proves no skill to anyone, and grants no authority over any programme.
          Mastery remains six separately assessed dimensions, recorded by a
          person who judged the evidence.
        </p>
      </footer>
    </div>
  );
}

// Local pill so this view carries no dependency on App.jsx.
function Pill({ children, tone = "neutral" }) {
  return <span className={`pill pill--${tone}`}>{children}</span>;
}
