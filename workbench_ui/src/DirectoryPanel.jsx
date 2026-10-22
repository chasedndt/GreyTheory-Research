// Look up what a platform publishes about one programme.
//
// This is the only control in the application that sends a request from your
// machine, so it says so on the button rather than in small print underneath.
// Nothing here fetches on load, on focus, or as a side effect of anything else:
// a request leaves only when you press it.
//
// What it cannot do is as important as what it can. It reads one programme you
// can already name - it cannot browse or enumerate a platform's directory, and
// what comes back is public, untrusted source material rather than scope
// anybody has reviewed.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { useState } from "react";
import "./DirectoryPanel.css";

const PLATFORMS = [
  ["hackerone", "HackerOne"],
  ["bugcrowd", "Bugcrowd"],
  ["intigriti", "Intigriti"],
  ["yeswehack", "YesWeHack"],
];

//: Mirrors the identifier rule the server enforces, so an obviously malformed
//: handle is caught here rather than after a pointless round trip.
const HANDLE = /^[a-z0-9][a-z0-9._-]{0,63}$/;

function bytes(count) {
  if (!count) return "0 bytes";
  if (count < 1024) return `${count} bytes`;
  return `${(count / 1024).toFixed(1)} kB`;
}

export default function DirectoryPanel({ directory, persistenceMode, onLookUp }) {
  const [platform, setPlatform] = useState("hackerone");
  const [handle, setHandle] = useState("");
  const [busy, setBusy] = useState(false);

  if (!directory?.available) return null;

  const connected = persistenceMode === "interactive";
  const trimmed = handle.trim().toLowerCase();
  const valid = HANDLE.test(trimmed);
  const ready = connected && valid && !busy && Boolean(onLookUp);
  const label = PLATFORMS.find(([id]) => id === platform)?.[1] || platform;

  async function submit(event) {
    event.preventDefault();
    if (!ready) return;
    setBusy(true);
    try {
      await onLookUp({ platform, handle: trimmed });
      setHandle("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="surface directory-panel" aria-labelledby="directory-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">The only outbound request in this app</span>
          <h2 id="directory-title">Look up a programme</h2>
        </div>
        {directory.counts.read > 0 && (
          <span className="eyebrow">{directory.counts.read} read · {bytes(directory.counts.bytes)}</span>
        )}
      </div>

      <p className="directory-panel__what">
        Reads what a platform publishes openly about one programme you can
        already name. It cannot browse or list a directory, it sends no
        credentials, and it never touches the programme&rsquo;s own systems.
      </p>

      <form className="directory-panel__form" onSubmit={submit}>
        <label>
          <span>Platform</span>
          <select
            value={platform}
            disabled={!connected || busy}
            onChange={(event) => setPlatform(event.target.value)}
          >
            {PLATFORMS.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
          </select>
        </label>
        <label>
          <span>Programme handle</span>
          <input
            type="text"
            value={handle}
            placeholder="gitlab"
            autoComplete="off"
            spellCheck="false"
            disabled={!connected || busy}
            onChange={(event) => setHandle(event.target.value)}
          />
          <small>
            The name in the programme&rsquo;s own URL &mdash; the{" "}
            <code>gitlab</code> in <code>{`${label.toLowerCase()}.com/gitlab`}</code>.
          </small>
        </label>
        {/* The verb is on the button. A request leaving the machine should
            never be something you discover after the fact. */}
        <button type="submit" className="button button--primary" disabled={!ready}>
          {busy ? "Sending request…" : `Send a request to ${label}`}
        </button>
      </form>

      {!connected && (
        <p className="directory-panel__refusal" role="status">
          Connect the local application first. In preview nothing is sent and
          nothing is kept.
        </p>
      )}
      {connected && handle.trim() && !valid && (
        <p className="directory-panel__refusal" role="status">
          A handle is lower-case letters, digits, dots, dashes or underscores
          &mdash; not a full URL.
        </p>
      )}

      {directory.lookups.length > 0 && (
        <div className="directory-panel__results">
          <span className="eyebrow">Retrieved and kept</span>
          <ul>
            {directory.lookups.map((item) => (
              <li key={item.identifier}>
                <div>
                  <strong>{item.identifier}</strong>
                  <small>{item.url}</small>
                </div>
                <span className="directory-panel__facts">
                  {bytes(item.bodyBytes)} · {item.contentType} ·{" "}
                  <code>{item.bodySha256.slice(0, 12)}</code>
                </span>
                {/* Carried on every row, because a saved copy of a public page
                    sitting in your workbench is the easiest thing here to
                    mistake for reviewed scope. */}
                <span className="directory-panel__trust">
                  {item.dataClass} · {item.trust} · grants no authority
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <footer className="directory-panel__boundary">
        <p>{directory.note}</p>
      </footer>
    </section>
  );
}
