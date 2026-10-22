// Where you are, as the first thing on the page.
//
// Not a tour and not a wizard. Every step is marked done because the underlying
// fact is true - a contract records a human review, the lesson store records
// worked-through checks - so it cannot be clicked past, and it stays useful
// after the first day as an honest status board rather than something to
// dismiss.
//
// When the application is not connected this is the whole point of the screen:
// nothing is being kept, and saying that plainly matters more than anything
// else on the page.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { Check } from "@phosphor-icons/react/dist/csr/Check";
import { ArrowRight } from "@phosphor-icons/react/dist/csr/ArrowRight";
import { CaretDown } from "@phosphor-icons/react/dist/csr/CaretDown";
import { ShieldCheck } from "@phosphor-icons/react/dist/csr/ShieldCheck";
import { currentStep, onboardingProgress, onboardingSteps } from "./onboarding.js";
import "./OnboardingPanel.css";

export default function OnboardingPanel({
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

  // Collapsing is allowed once you are connected. Before that, hiding the one
  // thing that makes your work persist would be doing you a disservice.
  const canCollapse = Boolean(connected);
  const isCollapsed = canCollapse && collapsed;

  return (
    <section
      className={`surface onboarding ${connected ? "" : "is-urgent"} ${isCollapsed ? "is-collapsed" : ""}`.trim()}
      aria-labelledby="onboarding-title"
    >
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            {connected ? "Where you are" : "Nothing is being kept yet"}
          </span>
          <h2 id="onboarding-title">
            {progress.complete ? "You are set up" : "Getting to real research"}
          </h2>
        </div>
        <div className="onboarding__head-right">
          <span className="onboarding__count">{progress.done} of {progress.total}</span>
          {canCollapse && (
            <button
              type="button"
              className="onboarding__collapse"
              aria-expanded={!isCollapsed}
              aria-controls="onboarding-steps"
              onClick={() => onToggleCollapsed(!isCollapsed)}
            >
              <CaretDown />
              <span className="sr-only">{isCollapsed ? "Show the steps" : "Hide the steps"}</span>
            </button>
          )}
        </div>
      </div>

      <div className="onboarding__bar" role="img" aria-label={`${progress.done} of ${progress.total} steps done`}>
        <span style={{ width: `${progress.percent}%` }} />
      </div>

      {!connected && (
        <p className="onboarding__urgent">
          You are looking at a preview. Nothing you do is saved, no programme can
          be shortlisted, and no review can be recorded until the local
          application is connected.
        </p>
      )}

      <ol className="onboarding__steps" id="onboarding-steps" hidden={isCollapsed}>
        {steps.map((step, index) => {
          const isCurrent = current?.id === step.id;
          return (
            <li
              key={step.id}
              className={[step.done ? "is-done" : "", isCurrent ? "is-current" : ""].join(" ").trim()}
            >
              <span className="onboarding__mark" aria-hidden="true">
                {step.done ? <Check /> : index + 1}
              </span>
              <div className="onboarding__body">
                <strong>{step.title}</strong>
                <p className="onboarding__why">{step.why}</p>
                <p className="onboarding__action">{step.action}</p>
                {step.note && <p className="onboarding__note">{step.note}</p>}
              </div>
              {!step.done && (
                <button
                  type="button"
                  className={isCurrent ? "button button--primary" : "button button--secondary"}
                  onClick={() => (step.id === "connect" && onConnect ? onConnect() : navigate(step.route))}
                >
                  {step.id === "connect" ? "Connect" : "Go there"} <ArrowRight />
                </button>
              )}
            </li>
          );
        })}
      </ol>

      <footer className="onboarding__boundary" hidden={isCollapsed}>
        <ShieldCheck />
        <p>
          Every step here is ticked because the thing actually happened &mdash;
          a contract that records a review, a lesson whose checks you worked
          through. None of it can be clicked past, and none of it awards mastery
          or grants authority over any programme.
        </p>
      </footer>
    </section>
  );
}
