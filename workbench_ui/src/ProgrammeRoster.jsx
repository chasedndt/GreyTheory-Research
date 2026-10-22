// The bounties you actually have, on the page you open first.
//
// This is a registry, not a feed. Nothing here was fetched from a platform and
// nothing appears that was not compiled from sources saved on this machine. It
// deliberately does not pretend to be a directory of live opportunities,
// because presenting your three compiled programmes as though they were a
// market listing would be the interface lying about where its content came
// from.
//
// Each row answers one question: what do I do with this one next. The rule
// behind that answer lives in programmeReadiness, tested on its own.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { programmeNextStep } from "./programmeReadiness.js";
import "./ProgrammeRoster.css";

const TONE_CLASS = {
  ready: "is-ready",
  attention: "is-attention",
  blocked: "is-blocked",
  unknown: "is-unknown",
};

export default function ProgrammeRoster({ programmes, navigate }) {
  if (!programmes?.available) return null;

  const entries = programmes.programmes || [];

  if (!entries.length) {
    return (
      <section className="surface programme-roster" aria-labelledby="roster-title">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Your bounties</span>
            <h2 id="roster-title">Programmes</h2>
          </div>
        </div>
        <p className="programme-roster__empty">
          No programme is registered yet. A programme arrives by compiling a
          source bundle saved on this machine &mdash; nothing is fetched, and
          registering one grants no authority to test it.
        </p>
      </section>
    );
  }

  return (
    <section className="surface programme-roster" aria-labelledby="roster-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Your bounties &middot; compiled locally, not fetched</span>
          <h2 id="roster-title">Programmes</h2>
        </div>
        <span className="eyebrow">
          {programmes.counts.registered} registered &middot;{" "}
          {programmes.counts.needingAttention} need you
        </span>
      </div>

      <ul className="programme-roster__list">
        {entries.map((programme) => {
          const next = programmeNextStep(programme);
          return (
            <li key={programme.id} className={TONE_CLASS[next.tone] || "is-unknown"}>
              <div className="programme-roster__who">
                <strong>{programme.id}</strong>
                <small>
                  {programme.contractStatus} &middot; v{programme.version} &middot;{" "}
                  ceiling {programme.maxAuthority || "not recorded"}
                </small>
              </div>
              <div className="programme-roster__next">
                <strong>{next.step}</strong>
                <p>{next.because}</p>
              </div>
            </li>
          );
        })}
      </ul>

      <footer className="programme-roster__boundary">
        <button type="button" className="button button--secondary" onClick={() => navigate("programmes")}>
          Open the scope library
        </button>
        <p>
          Every programme here was compiled from saved sources and carries its
          own authority ceiling. None of them is live, and appearing on this
          list grants no permission to touch anything.
        </p>
      </footer>
    </section>
  );
}
