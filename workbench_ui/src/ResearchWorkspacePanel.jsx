// A research workspace: the bounded container real investigation happens in.
//
// The server has always published this section and nothing rendered it. When
// you have no workspace yet - which is the case until a programme's contract is
// reviewed - it shows a worked example instead, badged as one.
//
// The example travels through this same component, so it is a preview rather
// than a mock-up: the day a real workspace exists, this renders your own data
// in the identical layout. The one thing it must never do is let an example be
// mistaken for a record, which is why the badge is not subtle and the ids say
// "example".
//
// Self-contained: no imports from App.jsx, which would be circular.

import { EXAMPLE_WORKSPACE, WORKSPACE_PREREQUISITES } from "./exampleWorkspace.js";
import "./ResearchWorkspacePanel.css";

const COUNT_FIELDS = [
  ["hypotheses", "Hypotheses", "Questions posed, none of them proven"],
  ["actionRequests", "Action requests", "Bounded intents, each needing a decision"],
  ["actionReceipts", "Receipts", "What was actually run, and what it produced"],
  ["sessions", "Sessions", "Working periods inside this workspace"],
  ["lessons", "Lessons", "What you concluded and carried forward"],
];

function WorkspaceCard({ workspace, isExample }) {
  const { counts } = workspace;
  return (
    <article className={isExample ? "workspace-card is-example" : "workspace-card"}>
      <header>
        <div>
          {isExample && <span className="workspace-card__badge">Example &middot; not your data</span>}
          <h3>{workspace.title}</h3>
          <p className="workspace-card__goal">{workspace.goal}</p>
        </div>
      </header>

      <dl className="workspace-card__meta">
        <div>
          <dt>Programme</dt>
          <dd>{workspace.programmeId || "not recorded"}</dd>
        </div>
        <div>
          <dt>Operating posture</dt>
          <dd>{workspace.posture || "not recorded"}</dd>
        </div>
        <div>
          <dt>State</dt>
          <dd>{workspace.status}</dd>
        </div>
      </dl>

      {workspace.unreadable ? (
        // Counts are withheld rather than shown as zero: the server could not
        // read this workspace, and zero would be a claim it cannot support.
        <p className="workspace-card__unreadable">
          This workspace could not be read, so nothing about its contents is
          shown. {workspace.error}
        </p>
      ) : (
        counts && (
          <ul className="workspace-card__counts">
            {COUNT_FIELDS.map(([key, label, meaning]) => (
              <li key={key}>
                <strong>{counts[key]}</strong>
                <span>{label}</span>
                <small>{meaning}</small>
              </li>
            ))}
          </ul>
        )
      )}

      <footer className="workspace-card__boundary">
        A workspace is bounded by the contract it was opened under. Everything
        recorded inside it carries that authority reference, so nothing can
        later be read as evidence gathered under different permission.
      </footer>
    </article>
  );
}

export default function ResearchWorkspacePanel({ research }) {
  if (!research?.available) return null;

  // Two different absences. A missing store is a setup problem; an empty store
  // is an ordinary starting point, and saying so wrongly would send you to fix
  // something that is not broken.
  if (!research.configured) {
    return (
      <section className="surface research-panel" aria-labelledby="research-title">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Where investigation happens</span>
            <h2 id="research-title">Research workspace</h2>
          </div>
        </div>
        <p className="research-panel__empty">
          No private research store is configured, so no workspace state is
          measured. This is a setup step, not an empty workspace.
        </p>
      </section>
    );
  }

  const real = research.workspaces || [];
  const showingExample = real.length === 0;
  const cards = showingExample ? [EXAMPLE_WORKSPACE] : real;

  return (
    <section className="surface research-panel" aria-labelledby="research-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Where investigation happens</span>
          <h2 id="research-title">Research workspace</h2>
        </div>
        {!showingExample && (
          <span className="eyebrow">
            {real.length} {real.length === 1 ? "workspace" : "workspaces"}
          </span>
        )}
      </div>

      {showingExample && (
        <p className="research-panel__preview">
          You have no research workspace yet, so this shows a worked example of
          what one looks like. It is sample data and nothing below is yours.
          When you open a real workspace it appears here in exactly this layout.
        </p>
      )}

      {cards.map((workspace) => (
        <WorkspaceCard
          key={workspace.id}
          workspace={workspace}
          isExample={showingExample}
        />
      ))}

      {showingExample && (
        <div className="research-panel__gate">
          <span className="eyebrow">What has to be true first</span>
          <ul>
            {WORKSPACE_PREREQUISITES.map((item) => (
              <li key={item.id} className={item.met ? "is-met" : "is-pending"}>
                <strong>{item.label}</strong>
                <span>{item.met ? "satisfied" : "outstanding"}</span>
                <small>{item.detail}</small>
              </li>
            ))}
          </ul>
          <p>
            A workspace inherits its authority from a reviewed contract, which is
            why it cannot exist before the review. That ordering is the point:
            it makes it impossible to record research under permission nobody
            confirmed.
          </p>
        </div>
      )}
    </section>
  );
}
