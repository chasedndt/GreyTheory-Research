// "What am I looking at?" - a disclosure beside the thing it explains.
//
// Deliberately a real button with aria-expanded/aria-controls rather than a
// hover tooltip: hover excludes keyboard and touch users, and this application
// treats guidance as content, not decoration.
//
// It is content-agnostic on purpose. The component knows how to disclose; it
// never knows what is being explained, so teaching copy stays in one place
// instead of being duplicated into every panel that wants to show it.
//
// Returns a fragment rather than a wrapping span: the panel holds paragraphs
// and lists, which are flow content and may not sit inside phrasing content.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { useEffect, useId, useState } from "react";
import { HINTS_CHANGED_EVENT, readHintPreference } from "./helpPreference.js";
import "./HelpHint.css";

export default function HelpHint({ label = "What to look for", children }) {
  const [open, setOpen] = useState(false);
  const [enabled, setEnabled] = useState(() => readHintPreference());
  const panelId = `help-${useId().replace(/:/g, "")}`;

  useEffect(() => {
    const onChange = (event) => {
      const next = event?.detail?.enabled;
      setEnabled(typeof next === "boolean" ? next : readHintPreference());
    };
    globalThis.addEventListener?.(HINTS_CHANGED_EVENT, onChange);
    return () => globalThis.removeEventListener?.(HINTS_CHANGED_EVENT, onChange);
  }, []);

  // Hidden entirely when the learner has asked for independent practice. The
  // Settings toggle promises hints are "hidden", so leaving a dead control
  // behind would make that promise false.
  if (!enabled || !children) return null;

  return (
    <>
      <button
        type="button"
        className="help-hint__trigger"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={open ? `Hide: ${label}` : label}
        onClick={() => setOpen((value) => !value)}
      >
        ?
      </button>
      <div id={panelId} role="note" className="help-hint__panel" hidden={!open}>
        <strong>{label}</strong>
        {children}
      </div>
    </>
  );
}
