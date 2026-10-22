// The review gate: recording that a person read this compiled contract.
//
// This is the act that turns PENDING_REVIEW into VERIFIED, and it is a claim
// about having *read* something. So it sits directly beneath the source
// documents rather than in a menu elsewhere - you confirm what is in front of
// you, not something you navigated away from.
//
// When the server would refuse the command, the control is disabled and the
// refusal is shown. A control that silently vanishes reads as a bug, and the
// reason is the lesson.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { useState } from "react";
import { reviewability } from "./reviewability.js";
import "./RecordReview.css";

export default function RecordReview({ entry, persistenceMode, onRecordReview }) {
  const [reviewer, setReviewer] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!entry) return null;

  const { reviewable, reason } = reviewability(entry);
  const connected = persistenceMode === "interactive";
  const named = reviewer.trim().length > 0;
  const ready = reviewable && connected && named && confirmed && !busy;

  if (entry.humanReviewed) {
    return (
      <section className="record-review is-settled" aria-labelledby="record-review-title">
        <h3 id="record-review-title">Reviewed</h3>
        <p>
          A person recorded reading this compiled contract; it reads{" "}
          <strong>{entry.contractStatus}</strong>. That did not raise what this
          programme permits - the authority ceiling is set by the programme
          itself, not by having read it.
        </p>
      </section>
    );
  }

  async function submit(event) {
    event.preventDefault();
    if (!ready) return;
    setBusy(true);
    try {
      await onRecordReview({ programmeId: entry.programmeId, reviewer: reviewer.trim() });
      setReviewer("");
      setConfirmed(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="record-review" aria-labelledby="record-review-title">
      <div className="record-review__head">
        <span className="eyebrow">The gate this material exists for</span>
        <h3 id="record-review-title">Record your review</h3>
      </div>

      <p className="record-review__what">
        Reviewing states that <em>you</em> read the sources above and the scope
        compiled from them. It confirms a clean compile was read by a person. It
        does not resolve ambiguity, and it grants no authority to touch
        anything - the programme&rsquo;s own ceiling still applies afterwards.
      </p>

      {!reviewable && (
        <p className="record-review__refusal" role="status">
          {reason}
        </p>
      )}

      {reviewable && !connected && (
        <p className="record-review__refusal" role="status">
          Connect the same-origin local application to record a review. In
          preview nothing is persisted, and a review that is not persisted is
          not a review.
        </p>
      )}

      <form className="record-review__form" onSubmit={submit}>
        <label className="record-review__field">
          <span>Who read it</span>
          <input
            type="text"
            value={reviewer}
            autoComplete="off"
            placeholder="your name"
            disabled={!reviewable || !connected || busy}
            onChange={(event) => setReviewer(event.target.value)}
          />
          <small>
            A person&rsquo;s name. A model may prepare a contract for review but
            cannot be its reviewer, and the local application refuses one that
            names an assistant.
          </small>
        </label>

        <label className="record-review__confirm">
          <input
            type="checkbox"
            checked={confirmed}
            disabled={!reviewable || !connected || busy}
            onChange={(event) => setConfirmed(event.target.checked)}
          />
          <span>
            I opened the source documents above and read the compiled scope
            beside them.
          </span>
        </label>

        <button type="submit" className="button button--primary" disabled={!ready}>
          {busy ? "Recording…" : "Record my review"}
        </button>
      </form>
    </section>
  );
}
