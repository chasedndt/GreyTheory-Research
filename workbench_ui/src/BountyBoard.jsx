// Real bug bounty programmes, on the page you open first.
//
// Three rules hold this component together.
//
// **A suggestion must never look like a fact.** Every row is marked unchecked
// until a real fetch has read its page, and only then does it show retrieved
// evidence.
//
// **The status light describes the page, not the programme.** A 200 means its
// page is published and responded; it does not mean the programme is accepting
// submissions. A light claiming that would be a fabrication someone might act
// on, so the wording stays "reachable".
//
// **Reward figures are linked, never stated.** Amounts change without notice,
// so the only honest answer is a direct route to the programme's own page,
// where the current numbers actually live.
//
// The card opens on click and closes on click. It deliberately does not open on
// hover: a card that appears the moment a pointer crosses it makes the list
// impossible to scan. Hover lights the row; pressing it opens the detail.
//
// Self-contained: no imports from App.jsx, which would be circular.

import { useId, useState } from "react";
import { CaretDown } from "@phosphor-icons/react/dist/csr/CaretDown";
// ArrowRight rather than ArrowSquareOut: this Phosphor build ships a csr shim
// for ArrowSquareOut but no matching defs module, so it cannot resolve. Only
// icons shipping both halves are usable here.
import { ArrowRight } from "@phosphor-icons/react/dist/csr/ArrowRight";
import { REWARD_POSTURE, boardRows, programmeUrl } from "./knownProgrammes.js";
import {
  DEFAULT_INTERVAL_MS,
  MANUAL_COOLDOWN_MS,
  canRefresh,
  describeAge,
  dueCount,
  pageStatus,
  refreshPlan,
} from "./refreshPolicy.js";
import "./BountyBoard.css";

const PLATFORM_NAME = {
  hackerone: "HackerOne",
  bugcrowd: "Bugcrowd",
  intigriti: "Intigriti",
  yeswehack: "YesWeHack",
};

const CONTRACT_TONE = {
  blocked: "is-blocked",
  pending_review: "is-attention",
  verified: "is-ready",
};

function bytes(count) {
  if (!count) return "0 bytes";
  if (count < 1024) return `${count} bytes`;
  return `${(count / 1024).toFixed(1)} kB`;
}

function Row({ row, registryEntry, connected, onLookUp, now, baseId }) {
  const [open, setOpen] = useState(false);
  const panelId = `${baseId}-${row.platform}-${row.handle}`;
  const platform = PLATFORM_NAME[row.platform] || row.platform;
  const reward = REWARD_POSTURE[row.rewards] || REWARD_POSTURE.unknown;
  const status = pageStatus(row, now);
  const recheck = canRefresh(row, now);
  const url = row.lookup?.url || programmeUrl(row.platform, row.handle);

  return (
    <li className={[row.verified ? "is-verified" : "is-unchecked", open ? "is-open" : ""].join(" ").trim()}>
      <button
        type="button"
        className="bounty-board__row"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="bounty-board__who">
          <strong>{row.name}</strong>
          <small>{platform} &middot; <code>{row.handle}</code></small>
        </span>

        <span className="bounty-board__status" title={status.detail}>
          <i className={`bounty-board__light is-${status.tone}`} aria-hidden="true" />
          <span>{status.label}</span>
        </span>

        <span className="bounty-board__reward">
          <em>{reward.label}</em>
          <small>amounts on the programme page</small>
        </span>

        <span className="bounty-board__chevron" aria-hidden="true"><CaretDown /></span>
      </button>

      <div className="bounty-board__card" id={panelId} hidden={!open}>
        {row.target && <p className="bounty-board__target">{row.target}</p>}
        {row.why
          ? <p className="bounty-board__why">{row.why}</p>
          : <p className="bounty-board__why bounty-board__found">You looked this one up yourself, so nothing beyond what was retrieved is known about it.</p>}

        <dl className="bounty-board__facts">
          <div>
            <dt>Page status</dt>
            <dd>{status.label}</dd>
          </div>
          <div>
            <dt>Reward</dt>
            <dd>{reward.label}</dd>
          </div>
          <div>
            <dt>Retrieved</dt>
            <dd>
              {row.verified
                ? <>{bytes(row.lookup.bodyBytes)} &middot; {row.lookup.contentType}</>
                : <span className="is-unknown">not yet</span>}
            </dd>
          </div>
          <div>
            <dt>In your registry</dt>
            <dd>
              {registryEntry
                ? `${registryEntry.contractStatus} · v${registryEntry.version}`
                : <span className="is-unknown">not compiled</span>}
            </dd>
          </div>
        </dl>

        <p className="bounty-board__status-note">{status.detail}</p>

        <div className="bounty-board__actions">
          {/* The link is the honest answer to "how much does it pay". Amounts
              move, and the programme's own page is the only current source. */}
          <a className="button button--primary" href={url} target="_blank" rel="noreferrer">
            Open on {platform} <ArrowRight />
          </a>
          <button
            type="button"
            className="button button--secondary"
            disabled={!connected || !onLookUp || !recheck.allowed}
            onClick={() => onLookUp({ platform: row.platform, handle: row.handle })}
          >
            {row.verified ? "Check again" : "Check this page"}
          </button>
          <small>
            {recheck.allowed
              ? "An anonymous HTTPS GET of this page. No credentials, redirects refused, and it does not touch the programme's own systems."
              : recheck.reason}
          </small>
        </div>
      </div>
    </li>
  );
}

export default function BountyBoard({
  directory,
  persistenceMode,
  onLookUp,
  registered,
  onRefreshAll,
  autoRefresh,
  onToggleAutoRefresh,
}) {
  const baseId = useId().replace(/:/g, "");
  const rows = boardRows(directory?.lookups || []);
  const connected = persistenceMode === "interactive";
  const now = Date.now();
  const checked = rows.filter((row) => row.verified).length;
  const plan = refreshPlan(rows);
  const overdue = dueCount(rows, now, DEFAULT_INTERVAL_MS);

  const byRegistryId = new Map(
    (registered?.programmes || []).map((item) => [item.id, item]),
  );

  return (
    <section className="surface bounty-board" aria-labelledby="board-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Real public programmes &middot; a starting list, not a feed</span>
          <h2 id="board-title">Bug bounty board</h2>
        </div>
        <span className="eyebrow">{checked} of {rows.length} checked</span>
      </div>

      <p className="bounty-board__what">
        These are real programmes that have run publicly for years. Press a row
        to open it; the light shows whether its page responded when last read.
        Reward amounts are never recorded here &mdash; they change without
        notice, so each card links straight to the programme&rsquo;s own page
        where the current figures live.
      </p>

      {plan.requests > 0 && (
        <div className="bounty-board__refresh">
          <button
            type="button"
            className="button button--secondary"
            disabled={!connected || !onRefreshAll}
            onClick={() => onRefreshAll(plan)}
          >
            Re-check {plan.requests} {plan.requests === 1 ? "page" : "pages"}
          </button>
          <label className="bounty-board__auto">
            <input
              type="checkbox"
              checked={Boolean(autoRefresh)}
              disabled={!connected || !onToggleAutoRefresh}
              onChange={(event) => onToggleAutoRefresh(event.target.checked)}
            />
            <span>
              Check once a day
              <small>
                New public programmes appear a few times a week, so daily is
                ample. One request at a time, paused while this tab is hidden,
                and only pages you have already checked &mdash; turning this on
                never fetches something new.
                {overdue > 0 && ` ${overdue} due now.`}
              </small>
            </span>
          </label>
        </div>
      )}

      <ul className="bounty-board__list">
        {rows.map((row) => (
          <Row
            key={row.id}
            row={row}
            registryEntry={byRegistryId.get(`${row.platform}-${row.handle}-public`)}
            connected={connected}
            onLookUp={onLookUp}
            now={now}
            baseId={baseId}
          />
        ))}
      </ul>

      <footer className="bounty-board__boundary">
        <p>
          A light means that page responded when it was last read &mdash; not
          that the programme is accepting submissions, which only its own page
          can tell you. Reading a page grants no authority to test anything, and
          scope comes solely from a compiled, reviewed contract. A page may be
          re-checked by hand every {Math.round(MANUAL_COOLDOWN_MS / 3600000)} hours.
        </p>
      </footer>
    </section>
  );
}
