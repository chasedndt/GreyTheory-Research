// What you are working, and what you have set aside.
//
// Two views of one collection, so this is a segmented control rather than
// tabs: the list region is re-rendered in place instead of swapping real
// panels. That makes buttons with aria-current the honest semantics, and it
// avoids the common failure of "half-tabs" - tab roles with no tabpanel and no
// arrow-key handling.
//
// Archiving is deliberately not confirmed. It is reversible and deletes
// nothing, so a dialog on every one would only train you to click through the
// dialogs that do matter. The durable undo is Restore, which lives permanently
// in the Archived view rather than inside a message that times out.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { useRef, useState } from "react";
import "./ShortlistPanel.css";

const OUTCOME_LABEL = {
  unset: "",
  finished: "finished",
  not_started: "never started",
  out_of_scope_now: "out of scope now",
  no_longer_eligible: "no longer eligible",
};

function Empty({ view, archivedCount, onShowArchived }) {
  if (view === "archived") {
    // States the rule of the place before anyone relies on it, which is the
    // one moment an empty archive is genuinely useful.
    return (
      <p className="shortlist-panel__empty">
        Nothing is set aside yet. Archiving moves a programme off your active
        list without deleting anything, and you can restore it at any time.
      </p>
    );
  }
  if (archivedCount > 0) {
    // Everything archived is not the same as nothing shortlisted, and without
    // this exit a person who archives their last programme hits a dead end.
    return (
      <p className="shortlist-panel__empty">
        Nothing on your active list. You have {archivedCount}{" "}
        {archivedCount === 1 ? "programme" : "programmes"} set aside &mdash;{" "}
        <button type="button" className="shortlist-panel__link" onClick={onShowArchived}>
          open the archive
        </button>{" "}
        to bring one back.
      </p>
    );
  }
  return (
    <p className="shortlist-panel__empty">
      Nothing shortlisted yet. Shortlisting a programme records that you intend
      to work it &mdash; it grants no authority and changes nothing about scope.
    </p>
  );
}

export default function ShortlistPanel({
  shortlist,
  persistenceMode,
  onArchive,
  onRestore,
}) {
  const [view, setView] = useState("active");
  const [busyId, setBusyId] = useState(null);
  const listRef = useRef(null);

  if (!shortlist?.available) return null;

  const { active = [], archived = [], counts = { active: 0, archived: 0 } } = shortlist;
  const rows = view === "archived" ? archived : active;
  const connected = persistenceMode === "interactive";

  async function run(action, entry) {
    if (!connected || busyId) return;
    setBusyId(entry.programmeId);
    // The row moves to the other segment. If it was the last one here, the
    // view you are looking at empties and the thing you just acted on is
    // somewhere you cannot see - so follow it rather than leaving a blank
    // panel behind.
    const wasLast = rows.length === 1;
    try {
      await action({ programmeId: entry.programmeId, revision: entry.revision });
      if (wasLast) setView(view === "archived" ? "active" : "archived");
    } finally {
      setBusyId(null);
      // The row has left this list. Focus the container rather than the next
      // row's own control: landing on another row's Archive button would let a
      // repeated keypress cascade through the list.
      listRef.current?.focus();
    }
  }

  return (
    <section className="surface shortlist-panel" aria-labelledby="shortlist-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Your working set</span>
          <h2 id="shortlist-title">Shortlist</h2>
        </div>
        <div className="shortlist-panel__switch" role="group" aria-label="Shortlist view">
          {/* The count is announced as part of the name, not left as decoration:
              without it a screen reader hears "Set aside" and cannot tell
              whether the archive holds anything before opening it. */}
          <button
            type="button"
            aria-current={view === "active" ? "true" : undefined}
            aria-label={`Being worked, ${counts.active}`}
            className={view === "active" ? "is-selected" : ""}
            onClick={() => setView("active")}
          >
            Being worked <span>{counts.active}</span>
          </button>
          <button
            type="button"
            aria-current={view === "archived" ? "true" : undefined}
            aria-label={`Set aside, ${counts.archived}`}
            className={view === "archived" ? "is-selected" : ""}
            onClick={() => setView("archived")}
          >
            Set aside <span>{counts.archived}</span>
          </button>
        </div>
      </div>

      {rows.length === 0 ? (
        <Empty
          view={view}
          archivedCount={counts.archived}
          onShowArchived={() => setView("archived")}
        />
      ) : (
        <ul
          className="shortlist-panel__list"
          ref={listRef}
          tabIndex={-1}
          aria-label={view === "archived" ? "Set aside" : "Being worked"}
        >
          {rows.map((entry) => {
            const outcome = OUTCOME_LABEL[entry.outcome] || "";
            const busy = busyId === entry.programmeId;
            return (
              <li key={entry.programmeId}>
                <div className="shortlist-panel__entry">
                  <strong>{entry.programmeId}</strong>
                  <p>{entry.detail}</p>
                  {outcome && <small>Set aside as {outcome}</small>}
                </div>
                {entry.isArchived ? (
                  <button
                    type="button"
                    className="shortlist-panel__action"
                    disabled={!connected || busy}
                    // Named per item, so a screen reader hears which one.
                    aria-label={`Restore ${entry.programmeId} to your active list`}
                    onClick={() => run(onRestore, entry)}
                  >
                    {busy ? "Restoring…" : "Restore"}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="shortlist-panel__action"
                    disabled={!connected || busy}
                    aria-label={`Set ${entry.programmeId} aside`}
                    onClick={() => run(onArchive, entry)}
                  >
                    {busy ? "Setting aside…" : "Set aside"}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <footer className="shortlist-panel__boundary">
        <p>
          {connected
            ? shortlist.note
            : "Connect the local application to change your shortlist. In preview nothing is persisted."}
        </p>
      </footer>
    </section>
  );
}
