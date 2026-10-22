// Where you are, floating above every panel in the application.
//
// An overlay rather than a panel on one page: the steps span the whole product,
// so anchoring them to Mission Control would mean losing your place the moment
// you navigated to the thing a step told you to go and do.
//
// Not a tour and not a wizard. Every step is marked done because the underlying
// fact is true - a contract that records a human review, a lesson whose checks
// were worked through - so it cannot be clicked past, and it stays useful long
// after the first day as an honest status board.
//
// It collapses to a pill once connected. Before that it does not collapse at
// all: nothing you do is being kept, and letting you hide that would be doing
// you a disservice.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { Check } from "@phosphor-icons/react/dist/csr/Check";
import { ArrowRight } from "@phosphor-icons/react/dist/csr/ArrowRight";
import { CaretDown } from "@phosphor-icons/react/dist/csr/CaretDown";
import { Compass } from "@phosphor-icons/react/dist/csr/Compass";
import { ShieldCheck } from "@phosphor-icons/react/dist/csr/ShieldCheck";
import { currentStep, onboardingProgress, onboardingSteps } from "./onboarding.js";
import "./OnboardingOverlay.css";

export default function OnboardingOverlay({
  connected,
  programmes,
  completedLessons,
  shortlist,
  directory,
  collapsed,
  onToggleCollapsed,
  onConnect,
  navigate,
}) {
  const steps = onboardingSteps({ connected, programmes, completedLessons, shortlist, directory });
  const progress = onboardingProgress(steps);
  const current = currentStep(steps);

  // Collapsing needs a connection. Hiding the one step that makes your work
  // persist is not a choice worth offering.
  const canCollapse = Boolean(connected);
  const isCollapsed = canCollapse && collapsed;

  if (isCollapsed) {
    return (
      <div className="onboarding-overlay is-pill">
        <button
          type="button"
          className="onboarding-overlay__pill"
          aria-expanded="false"
          aria-controls="onboarding-overlay-body"
          onClick={() => onToggleCollapsed(false)}
        >
          <Compass />
          <span>
            {progress.complete ? "Set up" : current ? current.title : "Getting started"}
          </span>
          <b>{progress.done}/{progress.total}</b>
        </button>
      </div>
    );
  }

  return (
    <aside
      className={`onboarding-overlay ${connected ? "" : "is-urgent"}`.trim()}
      aria-labelledby="onboarding-overlay-title"
    >
      <div className="onboarding-overlay__head">
        <div>
          <span className="eyebrow">
            {connected ? "Where you are" : "Nothing is being kept yet"}
          </span>
          <h2 id="onboarding-overlay-title">
            {progress.complete ? "You are set up" : "Getting to real research"}
          </h2>
        </div>
        <div className="onboarding-overlay__head-right">
          <span className="onboarding-overlay__count">{progress.done}/{progress.total}</span>
          {canCollapse && (
            <button
              type="button"
              className="onboarding-overlay__collapse"
              aria-expanded="true"
              aria-controls="onboarding-overlay-body"
              onClick={() => onToggleCollapsed(true)}
            >
              <CaretDown />
              <span className="sr-only">Collapse the guide</span>
            </button>
          )}
        </div>
      </div>

      <div className="onboarding-overlay__bar" role="img" aria-label={`${progress.done} of ${progress.total} steps done`}>
        <span style={{ width: `${progress.percent}%` }} />
      </div>

      <div id="onboarding-overlay-body">
        {!connected && (
          <p className="onboarding-overlay__urgent">
            This is a preview. Nothing you do is saved, no programme can be
            shortlisted, and no review can be recorded until the local
            application is connected.
          </p>
        )}

        <ol className="onboarding-overlay__steps">
          {steps.map((step, index) => {
            const isCurrent = current?.id === step.id;
            return (
              <li
                key={step.id}
                className={[step.done ? "is-done" : "", isCurrent ? "is-current" : ""].join(" ").trim()}
              >
                <span className="onboarding-overlay__mark" aria-hidden="true">
                  {step.done ? <Check /> : index + 1}
                </span>
                <div className="onboarding-overlay__body">
                  <strong>{step.title}</strong>
                  {/* Only the step you are on explains itself in full. The rest
                      stay one line, so the overlay never becomes a wall. */}
                  {isCurrent && <p className="onboarding-overlay__why">{step.why}</p>}
                  <p className="onboarding-overlay__action">{step.action}</p>
                  {isCurrent && step.note && (
                    <p className="onboarding-overlay__note">{step.note}</p>
                  )}
                  {isCurrent && (
                    <button
                      type="button"
                      className="button button--primary"
                      onClick={() => (step.id === "connect" && onConnect ? onConnect() : navigate(step.route))}
                    >
                      {step.id === "connect" ? "Connect now" : "Take me there"} <ArrowRight />
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ol>

        <footer className="onboarding-overlay__boundary">
          <ShieldCheck />
          <p>
            Each step is ticked because the thing actually happened. None of it
            can be clicked past, and none of it awards mastery or grants
            authority over any programme.
          </p>
        </footer>
      </div>
    </aside>
  );
}
