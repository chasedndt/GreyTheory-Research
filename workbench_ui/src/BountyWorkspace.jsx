// One bounty at a time: its journey, and the material behind it.
//
// The campaign and review panels each used to list every programme, so working
// a single bounty meant reading three stacked copies of everything and holding
// the match in your head. This selects one bounty and shows only that one --
// where it stands, what moves it forward, and the compiled scope beside the
// sources it came from.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { useState } from "react";
import CampaignPanel from "./CampaignPanel.jsx";
import RecordReview from "./RecordReview.jsx";
import ReviewPanel from "./ReviewPanel.jsx";
import StudyPlan from "./StudyPlan.jsx";
import "./BountyWorkspace.css";

export default function BountyWorkspace({
  campaign,
  review,
  curriculum,
  persistenceMode,
  onRecordReview,
  shortlist,
  onShortlist,
}) {
  const campaigns = campaign?.available ? campaign.campaigns : [];
  const reviews = review?.available ? review.programmes : [];
  const studyPlans = curriculum?.available ? curriculum.programmes : [];

  // A bounty exists if either half knows about it; neither half is required,
  // so a programme with a campaign but no stored sources still appears.
  const ids = [...new Set([
    ...campaigns.map((entry) => entry.programmeId),
    ...reviews.map((entry) => entry.programmeId),
    ...studyPlans.map((entry) => entry.programmeId),
  ])];

  const [selected, setSelected] = useState(null);
  if (!ids.length) return null;

  const activeId = ids.includes(selected) ? selected : ids[0];
  // Read from the shortlist rather than tracked here: one source of truth, so
  // the button cannot disagree with the panel below it.
  const isShortlisted = (shortlist?.active || []).some((e) => e.programmeId === activeId);
  const isSetAside = (shortlist?.archived || []).some((e) => e.programmeId === activeId);
  const activeCampaign = campaigns.find((entry) => entry.programmeId === activeId) || null;
  const activeReview = reviews.find((entry) => entry.programmeId === activeId) || null;
  const activeStudy = studyPlans.find((entry) => entry.programmeId === activeId) || null;

  return (
    <section className="surface bounty-workspace" aria-labelledby="bounty-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">One bounty at a time</span>
          <h2 id="bounty-title">Bounty workspace</h2>
        </div>
        {/* The way onto the shortlist. Without it the shortlist panel can only
            ever show its empty state, since nothing else can add to it. */}
        {onShortlist && !isShortlisted && !isSetAside && (
          <button
            type="button"
            className="button button--secondary"
            disabled={persistenceMode !== "interactive"}
            onClick={() => onShortlist(activeId)}
          >
            Add to shortlist
          </button>
        )}
        {isShortlisted && <span className="eyebrow">On your shortlist</span>}
        {isSetAside && <span className="eyebrow">Set aside &middot; restore it from your shortlist</span>}
      </div>

      <div className="bounty-workspace__tabs" role="tablist" aria-label="Bounty">
        {ids.map((id) => {
          const entry = campaigns.find((item) => item.programmeId === id);
          const isActive = id === activeId;
          return (
            <button
              key={id}
              type="button"
              role="tab"
              id={`bounty-tab-${id}`}
              aria-selected={isActive}
              aria-controls={`bounty-panel-${id}`}
              tabIndex={isActive ? 0 : -1}
              className={isActive ? "is-selected" : ""}
              onClick={() => setSelected(id)}
            >
              <strong>{id}</strong>
              {entry ? (
                <small className={entry.blockedByGovernance ? "is-decision" : ""}>
                  {entry.blockedByGovernance ? "waiting on you" : entry.currentStage}
                </small>
              ) : null}
            </button>
          );
        })}
      </div>

      <div
        className="bounty-workspace__body"
        id={`bounty-panel-${activeId}`}
        role="tabpanel"
        aria-labelledby={`bounty-tab-${activeId}`}
        tabIndex={0}
      >
        {/* Each child receives exactly one programme, so its own switcher has
            nothing to switch between and does not render. The workspace owns
            selection; the panels only know how to draw one bounty. */}
        <CampaignPanel
          campaign={activeCampaign ? { available: true, campaigns: [activeCampaign] } : null}
        />
        <StudyPlan
          curriculum={activeStudy ? { available: true, programmes: [activeStudy] } : null}
        />
        <ReviewPanel
          review={activeReview ? { available: true, programmes: [activeReview] } : null}
        />
        {/* The gate belongs directly under the material it is about, so the
            act of confirming and the thing being confirmed stay together. */}
        {activeReview && onRecordReview && (
          <RecordReview
            entry={activeReview}
            persistenceMode={persistenceMode}
            onRecordReview={onRecordReview}
          />
        )}
        {!activeReview && (
          <p className="bounty-workspace__empty">
            No stored source material for this bounty. Register it from a saved
            bundle to review what its scope was compiled from.
          </p>
        )}
      </div>
    </section>
  );
}
