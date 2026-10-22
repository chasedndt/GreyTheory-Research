// Review material: what the compiler concluded, beside what it read.
//
// This exists so "review the compiled scope" is an act you can perform here
// rather than an instruction to go and find files. Asking someone to confirm
// something without showing it to them produces a rubber stamp, which is the
// one outcome the review gate exists to prevent.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { useState } from "react";
import "./ReviewPanel.css";

const CAPTURE_LABEL = {
  verbatim: "verbatim — the publisher's own text",
  structured_export: "structured export — machine-readable, as published",
  operator_extract: "operator extract — a paraphrase someone made",
};

export default function ReviewPanel({ review }) {
  const [programmeId, setProgrammeId] = useState(null);
  const [openDoc, setOpenDoc] = useState(null);
  if (!review?.available || !review.programmes.length) return null;

  const active =
    review.programmes.find((entry) => entry.programmeId === programmeId)
    || review.programmes[0];

  return (
    <section className="surface review-panel" aria-labelledby="review-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">What you would be confirming</span>
          <h2 id="review-title">Review material</h2>
        </div>
        {review.programmes.length > 1 && (
          <div className="review-panel__switch" role="group" aria-label="Programme">
            {review.programmes.map((entry) => (
              <button
                key={entry.programmeId}
                type="button"
                className={entry.programmeId === active.programmeId ? "is-selected" : ""}
                aria-pressed={entry.programmeId === active.programmeId}
                onClick={() => { setProgrammeId(entry.programmeId); setOpenDoc(null); }}
              >
                {entry.programmeId}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="review-panel__scope">
        {active.scope.map((group) => (
          <div key={group.kind} className="review-panel__scope-group">
            <span className="eyebrow">{group.title} · {group.count}</span>
            {group.count ? (
              <ul>{group.values.map((value) => <li key={value}>{value}</li>)}</ul>
            ) : (
              <p className="review-panel__none">none recorded</p>
            )}
          </div>
        ))}
      </div>

      {active.resolutions.length > 0 && (
        <div className="review-panel__resolutions">
          <span className="eyebrow">Must be settled before this can compile clean</span>
          <ul>
            {active.resolutions.map((item) => (
              <li key={item.id} className={item.resolved ? "is-resolved" : "is-pending"}>
                <strong>{item.title}</strong>
                <span>{item.resolved ? "settled" : "unresolved"}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="review-panel__documents">
        <span className="eyebrow">Sources it was compiled from</span>
        {active.documents.map((doc) => {
          const isOpen = openDoc === doc.id;
          return (
            <article
              key={doc.id}
              className={doc.hashAgrees ? "review-panel__doc" : "review-panel__doc is-mismatched"}
            >
              <button
                type="button"
                className="review-panel__doc-head"
                aria-expanded={isOpen}
                onClick={() => setOpenDoc(isOpen ? null : doc.id)}
              >
                <strong>{doc.title}</strong>
                <small>{CAPTURE_LABEL[doc.captureMode] || doc.captureMode}</small>
                <span className="review-panel__bytes">{doc.bytes} bytes</span>
              </button>
              {!doc.hashAgrees && (
                <p className="review-panel__mismatch">
                  The stored content does not match the hash it declared. Reading
                  it proves nothing until that is resolved.
                </p>
              )}
              {isOpen && (
                <pre className="review-panel__content">{doc.content}</pre>
              )}
              {isOpen && doc.truncated && (
                <p className="review-panel__truncated">
                  Shown to the display limit; the full document remains on disk.
                </p>
              )}
            </article>
          );
        })}
      </div>

      <footer className="review-panel__boundary">
        <p>
          Taken from the registry's own stored copy — the bytes that were
          actually compiled, not a working-tree file. Reviewing confirms a clean
          compile was read by a person. It does not resolve ambiguity and grants
          no authority to touch anything.
        </p>
      </footer>
    </section>
  );
}
