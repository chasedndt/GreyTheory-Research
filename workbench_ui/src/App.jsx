import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  BookmarkSimple,
  CalendarBlank,
  CaretDown,
  Check,
  CheckCircle,
  ChatCircleText,
  Eye,
  FileText,
  Flask,
  Folder,
  Gear,
  Info,
  List,
  LockKey,
  Notebook,
  Receipt,
  Scales,
  SealCheck,
  ShieldCheck,
  SidebarSimple,
  SignOut,
  SquaresFour,
  X,
} from "@phosphor-icons/react";

const navGroups = [
  {
    label: "Research",
    icon: Scales,
    items: [
      ["Overview", SquaresFour],
      ["Ledger", Notebook],
      ["Hypotheses", BookmarkSimple],
      ["Experiments", Flask],
      ["Receipts", Receipt],
      ["Claims", SealCheck],
      ["Reflections", ChatCircleText],
    ],
  },
  {
    items: [
      ["Knowledge", BookOpen],
      ["Artifacts", Folder],
      ["Templates", FileText],
    ],
  },
  {
    items: [
      ["Governance", ShieldCheck],
      ["Workspaces", Folder],
      ["Settings", Gear],
    ],
  },
];

const ledgerRows = [
  {
    step: "1",
    type: "Authority",
    icon: Scales,
    tone: "amber",
    title: "In-scope target: LOCAL_FIXTURE",
    description:
      "Rules: local testing only; no live systems; no real data; human review required.",
    artifact: "authority_v1.0.0.json",
    time: "14:05:12",
    status: "Authority verified",
    statusTone: "verified",
  },
  {
    step: "2",
    type: "Hypothesis",
    icon: BookmarkSimple,
    tone: "amber",
    title:
      "If a user can request a resource by identifier, then the application may allow access to another user's resource.",
    description: "Class: IDOR/BOLA",
    time: "14:06:03",
    status: "Unproven",
    statusTone: "observed",
  },
  {
    step: "3",
    type: "Experiment",
    icon: Flask,
    tone: "amber",
    title: "Attempt to access another user's resource identifier within LOCAL_FIXTURE.",
    description: "Method: Manual request via local proxy",
    artifact: "experiment_0001.har",
    time: "14:07:18",
    status: "Executed",
    statusTone: "verified",
  },
  {
    step: "4",
    type: "Observation",
    icon: Eye,
    tone: "amber",
    title: "Response returned 200 OK with content belonging to a different fixture user.",
    description: "Notes: No authentication bypass observed.",
    time: "14:09:26",
    status: "Observed",
    statusTone: "observed",
  },
  {
    step: "5",
    type: "Check receipt",
    icon: Receipt,
    tone: "neutral",
    title: "Receipt generated for experiment_0001.",
    description: "Includes request, response, and hashes.",
    artifact: "receipt_0001.json  ·  SHA-256 3b7f…9c2a",
    time: "14:10:02",
    status: "Recorded",
    statusTone: "verified",
    receipt: true,
  },
  {
    step: "6",
    type: "Claim",
    icon: BookmarkSimple,
    tone: "amber",
    title: "Possible IDOR/BOLA in document access.",
    description: "Unproven. Requires minimum evidence review.",
    artifact: "Confidence: Low",
    time: "14:10:45",
    status: "Unproven",
    statusTone: "observed",
  },
];

const evidenceRoles = [
  {
    label: "Authority",
    icon: Scales,
    tone: "verified",
    copy: "Confirms in-scope rules and permitted actions.",
  },
  {
    label: "Experiment",
    icon: Flask,
    tone: "verified",
    copy: "Produces artifact(s) under controlled conditions.",
  },
  {
    label: "Observation",
    icon: Eye,
    tone: "observed",
    copy: "Describes what was seen; not yet a claim.",
  },
  {
    label: "Check receipt",
    icon: Receipt,
    tone: "verified",
    copy: "Cryptographically binds artifacts to this record.",
  },
  {
    label: "Claim",
    icon: BookmarkSimple,
    tone: "observed",
    copy: "Researcher statement derived from evidence.",
  },
];

function StatusDot({ tone = "verified" }) {
  return <span className={`status-dot status-dot--${tone}`} aria-hidden="true" />;
}

function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <img src="/brand/mark-512.png" alt="" />
    </div>
  );
}

function Dialog({ title, eyebrow, children, onClose, actions }) {
  const closeRef = useRef(null);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="dialog-layer" role="presentation" onMouseDown={onClose}>
      <section
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="dialog__header">
          <div>
            {eyebrow && <p className="dialog__eyebrow">{eyebrow}</p>}
            <h2 id="dialog-title">{title}</h2>
          </div>
          <button ref={closeRef} className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={20} />
          </button>
        </header>
        <div className="dialog__body">{children}</div>
        {actions && <footer className="dialog__actions">{actions}</footer>}
      </section>
    </div>
  );
}

function EvidenceInspector({ onClose, isDrawer = false }) {
  return (
    <aside className={`inspector ${isDrawer ? "inspector--drawer" : ""}`} aria-label="Evidence inspector">
      <div className="inspector__heading">
        <h2>Evidence inspector</h2>
        {isDrawer ? (
          <button className="icon-button" onClick={onClose} aria-label="Close evidence inspector">
            <X size={19} />
          </button>
        ) : (
          <Info size={17} aria-label="Evidence inspector information" />
        )}
      </div>

      <section className="inspector__section selected-claim">
        <p className="section-kicker">Selected claim</p>
        <p>Possible IDOR/BOLA in document access.</p>
        <span>Unproven. Requires minimum evidence review.</span>
      </section>

      <section className="inspector__section">
        <h3>Claim–evidence roles</h3>
        <div className="role-list">
          {evidenceRoles.map(({ label, icon: Icon, tone, copy }) => (
            <div className="role" key={label}>
              <Icon size={21} weight="regular" />
              <div>
                <div className="role__title">
                  <span>{label}</span>
                  <StatusDot tone={tone} />
                </div>
                <p>{copy}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="inspector__section provenance">
        <h3>Provenance</h3>
        <dl>
          <div><dt>Workspace</dt><dd>LOCAL_FIXTURE</dd></div>
          <div><dt>Ledger ID</dt><dd>GT-2026-08-27-0001</dd></div>
          <div><dt>Created</dt><dd>27 Aug 2026 14:05</dd></div>
          <div><dt>Last updated</dt><dd>27 Aug 2026 14:10</dd></div>
          <div><dt>Author</dt><dd>Researcher (You)</dd></div>
          <div><dt>Data location</dt><dd>Local workspace only</dd></div>
          <div><dt>Sharing</dt><dd>None</dd></div>
        </dl>
      </section>

      <div className="inspector__privacy">
        <ShieldCheck size={18} />
        <p>All evidence is local to this workspace.<br />No data leaves your environment.</p>
      </div>
    </aside>
  );
}

export function App() {
  const [dialog, setDialog] = useState(null);
  const [drawer, setDrawer] = useState(null);
  const [reflection, setReflection] = useState("");
  const [savedReflection, setSavedReflection] = useState("");
  const [notice, setNotice] = useState("");
  const [activeNav, setActiveNav] = useState("Ledger");

  const missingEvidence = useMemo(
    () => [
      "Positive control from the fixture owner account",
      "Negative control proving denied cross-account access",
      "Matching request and response hashes",
    ],
    [],
  );

  function chooseNav(item) {
    setActiveNav(item);
    if (item !== "Ledger") {
      setNotice(`${item} is represented in the shell; this review remains on the Research Ledger.`);
      window.setTimeout(() => setNotice(""), 3600);
    }
    setDrawer(null);
  }

  function saveReflection() {
    const trimmed = reflection.trim();
    if (!trimmed) return;
    setSavedReflection(trimmed);
    setDialog(null);
    setNotice("Reflection saved locally to this review session.");
    window.setTimeout(() => setNotice(""), 3600);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__brand">
          <BrandMark />
          <div>
            <strong>GreyTheory AI</strong>
            <span>Proof-first security research control plane</span>
          </div>
        </div>
        <div className="topbar__title">
          <h1>Research Ledger</h1>
          <p>Evidence-first research. Human governed.</p>
        </div>
        <button className="mobile-menu icon-button" onClick={() => setDrawer("nav")} aria-label="Open navigation">
          <List size={22} />
        </button>
        <div className="topbar__utilities">
          <button className="utility utility--workspace" onClick={() => setNotice("Workspace switching is locked to the local fixture in this review.")}>
            <Folder size={22} />
            <span><small>Workspace</small>LOCAL_FIXTURE</span>
            <CaretDown size={14} />
          </button>
          <div className="utility utility--date">
            <CalendarBlank size={22} />
            <span><strong>27 Aug 2026</strong><small>15:42</small></span>
          </div>
          <button className="utility utility--profile" onClick={() => setNotice("Local researcher profile. No cloud account is connected.")}>
            <span className="avatar">LR</span>
            <span>Researcher</span>
            <CaretDown size={14} />
          </button>
        </div>
      </header>

      <nav className="side-nav" aria-label="Primary navigation">
        <div className="side-nav__scroll">
          {navGroups.map((group, index) => (
            <div className="nav-group" key={index}>
              {group.label && (
                <div className="nav-group__label">
                  <group.icon size={18} weight="duotone" />
                  {group.label}
                </div>
              )}
              {group.items.map(([item, Icon]) => (
                <button
                  key={item}
                  className={`nav-item ${item === activeNav ? "nav-item--active" : ""}`}
                  aria-current={item === activeNav ? "page" : undefined}
                  onClick={() => chooseNav(item)}
                >
                  <Icon size={19} />
                  <span>{item}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
        <div className="side-nav__status">
          <p><StatusDot tone="verified" /> No live-target capability</p>
          <span>Local-first · Human governed <Info size={14} /></span>
        </div>
      </nav>

      <main className="ledger">
        {notice && <div className="notice" role="status">{notice}</div>}
        <section className="ledger__header">
          <button className="back-link" onClick={() => setNotice("Hypothesis index is outside this selected screen.")}>
            <ArrowLeft size={15} /> All hypotheses
          </button>
          <div className="ledger__hero-row">
            <div>
              <div className="ledger__title-row">
                <h2>IDOR/BOLA in document access</h2>
                <span className="state-label"><StatusDot tone="observed" /> Unproven</span>
              </div>
              <dl className="case-meta">
                <div><dt>Workspace</dt><dd>LOCAL_FIXTURE</dd></div>
                <div><dt>Hypothesis ID</dt><dd>GT-2026-08-27-0001</dd></div>
                <div><dt>Category</dt><dd>IDOR/BOLA</dd></div>
                <div><dt>Created</dt><dd>27 Aug 2026 14:05</dd></div>
              </dl>
            </div>
            <div className="authority-summary">
              <div><CheckCircle size={20} weight="fill" /><span><strong>Authority verified</strong><small>Scope &amp; rules confirmed</small></span></div>
              <button className="button button--quiet" onClick={() => setDialog("authority")}>View authority package</button>
            </div>
          </div>
        </section>

        <section className="ledger-table" aria-label="Chronological research ledger">
          <div className="ledger-table__head" aria-hidden="true">
            <span>Step</span><span>Type</span><span>Entry</span><span>Time (27 Aug 2026)</span><span>Status</span>
          </div>
          {ledgerRows.map((row) => {
            const Icon = row.icon;
            return (
              <article className="ledger-row" key={row.step}>
                <span className="ledger-row__step">{row.step}</span>
                <div className={`ledger-row__type ledger-row__type--${row.tone}`}><Icon size={19} /><span>{row.type}</span></div>
                <div className="ledger-row__entry">
                  <strong>{row.title}</strong>
                  <span>{row.description}</span>
                  {row.artifact && <small>{row.artifact} <FileText size={13} /></small>}
                  {row.step === "6" && savedReflection && <small className="reflection-chip"><ChatCircleText size={13} /> Reflection attached</small>}
                </div>
                <time className="ledger-row__time">{row.time}</time>
                <div className="ledger-row__status">
                  <span><StatusDot tone={row.statusTone} /> {row.status}</span>
                  {row.receipt && <button className="button button--quiet button--compact" onClick={() => setDialog("receipt")}>Open receipt</button>}
                </div>
              </article>
            );
          })}
        </section>

        <section className="next-action" aria-label="Next safe action">
          <div className="next-action__copy">
            <strong>Next safe action <ArrowRight size={18} /></strong>
            <p>Review minimum evidence to determine if this claim can advance.</p>
          </div>
          <button className="button button--primary" onClick={() => setDialog("evidence")}>Review minimum evidence</button>
          <button className="button button--quiet" onClick={() => setDialog("receipt")}><Eye size={18} /> Open receipt</button>
          <button className="button button--quiet" onClick={() => setDialog("reflection")}><ChatCircleText size={18} /> Add reflection</button>
        </section>
      </main>

      <div className="desktop-inspector"><EvidenceInspector /></div>
      <button className="inspector-toggle" onClick={() => setDrawer("inspector")}><SealCheck size={18} /> Evidence</button>

      {drawer && <div className="drawer-backdrop" onMouseDown={() => setDrawer(null)} />}
      {drawer === "inspector" && <EvidenceInspector isDrawer onClose={() => setDrawer(null)} />}
      {drawer === "nav" && (
        <aside className="mobile-nav" aria-label="Mobile navigation">
          <div className="mobile-nav__heading"><BrandMark /><strong>GreyTheory AI</strong><button className="icon-button" onClick={() => setDrawer(null)} aria-label="Close navigation"><X size={20} /></button></div>
          {navGroups.flatMap((group) => group.items).map(([item, Icon]) => (
            <button key={item} className={`nav-item ${item === activeNav ? "nav-item--active" : ""}`} onClick={() => chooseNav(item)}><Icon size={19} />{item}</button>
          ))}
          <p className="mobile-nav__status"><StatusDot tone="verified" /> LOCAL_FIXTURE · no live targets</p>
        </aside>
      )}

      {dialog === "authority" && (
        <Dialog title="Authority package" eyebrow="LOCAL_FIXTURE" onClose={() => setDialog(null)} actions={<button className="button button--primary" onClick={() => setDialog(null)}>Understood</button>}>
          <div className="authority-detail">
            <CheckCircle size={28} weight="fill" />
            <div><strong>Scope and rules are confirmed for this fixture.</strong><p>This package grants only local synthetic testing. It cannot authorise a live system, real data, disclosure, or submission.</p></div>
          </div>
          <dl className="dialog-grid"><div><dt>Package</dt><dd>authority_v1.0.0.json</dd></div><div><dt>Posture ceiling</dt><dd>LOCAL_FIXTURE</dd></div><div><dt>Human review</dt><dd>Required</dd></div><div><dt>External network</dt><dd>Unavailable</dd></div></dl>
        </Dialog>
      )}

      {dialog === "receipt" && (
        <Dialog title="Check receipt" eyebrow="Recorded · 14:10:02" onClose={() => setDialog(null)} actions={<button className="button button--primary" onClick={() => setDialog(null)}>Close receipt</button>}>
          <div className="receipt-detail"><LockKey size={28} /><div><strong>Artifact binding verified</strong><p>This local receipt binds the synthetic request and response to experiment_0001. It proves record integrity, not a real-world vulnerability.</p></div></div>
          <dl className="dialog-grid"><div><dt>Receipt</dt><dd>receipt_0001.json</dd></div><div><dt>Validator</dt><dd>local-fixture-check-v1</dd></div><div><dt>SHA-256</dt><dd>3b7f…9c2a</dd></div><div><dt>Export state</dt><dd>Local only</dd></div></dl>
        </Dialog>
      )}

      {dialog === "evidence" && (
        <Dialog title="Minimum evidence review" eyebrow="Claim remains unproven" onClose={() => setDialog(null)} actions={<button className="button button--primary" onClick={() => setDialog(null)}>Keep claim unproven</button>}>
          <p className="dialog-intro">The observation is useful, but the claim cannot advance until the controlled case includes:</p>
          <ul className="check-list">{missingEvidence.map((item) => <li key={item}><span><Check size={15} /></span>{item}</li>)}</ul>
          <div className="boundary-note"><ShieldCheck size={20} /><p>No new action is launched from this review. A future experiment still requires a fresh deterministic gate decision.</p></div>
        </Dialog>
      )}

      {dialog === "reflection" && (
        <Dialog title="Add reflection" eyebrow="Private learning note" onClose={() => setDialog(null)} actions={<><button className="button button--quiet" onClick={() => setDialog(null)}>Cancel</button><button className="button button--primary" onClick={saveReflection} disabled={!reflection.trim()}>Save reflection</button></>}>
          <label className="field"><span>What did this controlled experiment teach you?</span><textarea value={reflection} onChange={(event) => setReflection(event.target.value)} placeholder="Record what changed in your understanding, what remains uncertain, and what you would test next…" rows={6} /></label>
          <p className="field-help">This prototype keeps the note only in the current browser session.</p>
        </Dialog>
      )}
    </div>
  );
}
