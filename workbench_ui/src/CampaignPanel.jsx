// Where each engagement actually stands, read from the campaign section.
//
// The panel exists because "blocked" and "unfinished" look identical in prose
// and are not the same thing. A stage waiting on an operator decision is drawn
// differently from one waiting on work, so the difference is visible at a
// glance rather than buried in a sentence.
//
// Self-contained on purpose: no imports from App.jsx, which would be circular.

import "./CampaignPanel.css";

const MARKER_LABEL = {
  ok: "satisfied",
  gov: "awaiting a decision",
  todo: "not yet done",
};

export default function CampaignPanel({ campaign }) {
  if (!campaign?.available) return null;

  return (
    <section className="surface campaign-panel" aria-labelledby="campaign-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Where each engagement stands</span>
          <h2 id="campaign-title">From scope to proof</h2>
        </div>
      </div>

      <ul className="campaign-panel__list">
        {campaign.campaigns.map((entry) => (
          <li key={entry.programmeId} className="campaign-panel__item">
            {/* With a single entry the caller has already named the bounty and
                its state, so repeating both here would say the same thing
                twice in one card. Shown only when several are listed. */}
            {campaign.campaigns.length > 1 && (
              <div className="campaign-panel__head">
                <strong>{entry.programmeId}</strong>
                <span
                  className={
                    entry.blockedByGovernance
                      ? "campaign-panel__tag campaign-panel__tag--decision"
                      : "campaign-panel__tag"
                  }
                >
                  {entry.blockedByGovernance
                    ? "Waiting on you"
                    : `Stage: ${entry.currentStage}`}
                </span>
              </div>
            )}

            <ol className="campaign-panel__rail" aria-label="Stages">
              {entry.stages.map((stage) => (
                <li
                  key={stage.name}
                  className={`campaign-panel__stage is-${stage.marker}`}
                  aria-current={stage.name === entry.currentStage ? "step" : undefined}
                >
                  <span className="campaign-panel__dot" aria-hidden="true" />
                  <span className="campaign-panel__stage-name">{stage.name}</span>
                  <span className="campaign-panel__sr">
                    {MARKER_LABEL[stage.marker] || stage.marker}
                  </span>
                </li>
              ))}
            </ol>

            {/* The reason, not just the position. A stage name without its
                cause is a progress bar, and a progress bar cannot say
                "waiting on you" as distinct from "unfinished". */}
            <p className="campaign-panel__because">{entry.because}</p>
            {entry.nextAction ? (
              <p className="campaign-panel__next">
                <span className="eyebrow">What moves it forward</span>
                {entry.nextAction}
              </p>
            ) : null}
          </li>
        ))}
      </ul>

      <footer className="campaign-panel__boundary">
        <p>
          Stages report what was observed. A stage marked <em>waiting on you</em>{" "}
          needs a decision only you may make, not more work. Nothing on this
          panel grants authority, and nothing here has been submitted.
        </p>
      </footer>
    </section>
  );
}
