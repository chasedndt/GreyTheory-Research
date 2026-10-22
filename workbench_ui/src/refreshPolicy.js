/**
 * When a looked-up programme should be read again, and how often at most.
 *
 * This is the policy behind an auto-refreshing board, kept apart from the
 * component because it is a decision with consequences outside the browser:
 * every refresh is a real request from the operator's own address to a bug
 * bounty platform. Sustained automated traffic is exactly the behaviour that
 * gets a researcher's access restricted, and several platforms' terms prohibit
 * automated collection outright. So the restraint lives here, in one tested
 * place, rather than being a property of whichever component last touched it.
 *
 * Four rules this module exists to hold:
 *
 * **A floor that cannot be lowered.** `MINIMUM_INTERVAL_MS` is a clamp, not a
 * default. A caller asking for thirty seconds gets the floor, silently and
 * always, because the protection is worthless if a caller can opt out of it.
 *
 * **One at a time, spaced.** Refreshing returns a single programme, never a
 * batch. A burst of six simultaneous requests looks like collection; one
 * request every few seconds looks like a person.
 *
 * **Only what you already chose.** A programme is eligible for automatic
 * refresh solely because you looked it up yourself. Turning a toggle on must
 * never be the thing that causes a request for something you never asked for.
 *
 * **Nothing is claimed about freshness that was not observed.** A programme
 * never looked up has no age, and `describeAge` says so rather than implying
 * one.
 */

//: Once a day, and no more. New public programmes appear on the major
//: platforms a few times a week, not a few times an hour: a launch involves
//: scope review and a published policy, so it is not a high-frequency event.
//: Checking more often spends requests on a page that changes roughly monthly,
//: and sustained automated traffic is what gets a researcher's access
//: restricted. Lower values are clamped up, never honoured.
export const MINIMUM_INTERVAL_MS = 24 * 60 * 60 * 1000;

//: The same figure: there is no case for a shorter automatic cadence, so the
//: default and the floor are deliberately identical.
export const DEFAULT_INTERVAL_MS = MINIMUM_INTERVAL_MS;

//: A person may re-check one programme every four hours. Frequent enough to
//: catch a scope change the same day it lands, far below anything that reads
//: as collection, and it is per programme rather than global - checking GitLab
//: does not lock out Shopify.
export const MANUAL_COOLDOWN_MS = 4 * 60 * 60 * 1000;

//: Gap between consecutive requests in a manual refresh of several programmes.
export const SPACING_MS = 3000;

export function clampInterval(requestedMs) {
  const value = Number(requestedMs);
  if (!Number.isFinite(value)) return DEFAULT_INTERVAL_MS;
  return Math.max(MINIMUM_INTERVAL_MS, value);
}

function retrievedAtMs(lookup) {
  if (!lookup?.retrievedAt) return null;
  const parsed = Date.parse(lookup.retrievedAt);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Milliseconds since a programme was last read, or null if it never was. */
export function ageOf(row, now = Date.now()) {
  const at = retrievedAtMs(row?.lookup);
  if (at === null) return null;
  // A clock skew that puts retrieval in the future reads as "just now" rather
  // than as a negative age.
  return Math.max(0, now - at);
}

export function describeAge(ms) {
  if (ms === null || ms === undefined) return "never looked up";
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return "just now";
  if (minutes === 1) return "1 minute ago";
  if (minutes < 60) return `${minutes} minutes ago`;
  const hours = Math.floor(minutes / 60);
  if (hours === 1) return "1 hour ago";
  if (hours < 24) return `${hours} hours ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "1 day ago" : `${days} days ago`;
}

/**
 * The one programme due for an automatic refresh, or null.
 *
 * Returns a single row on purpose. The caller refreshes it, waits for the next
 * tick, and asks again - so a backlog drains one request at a time instead of
 * arriving as a burst.
 */
export function nextDue(rows = [], now = Date.now(), intervalMs = DEFAULT_INTERVAL_MS) {
  const interval = clampInterval(intervalMs);
  const eligible = rows
    // Never-looked-up programmes are deliberately excluded: enabling automatic
    // refresh must not be what causes a first request for something you did
    // not choose.
    .filter((row) => row?.verified && row?.lookup)
    .map((row) => ({ row, age: ageOf(row, now) }))
    .filter((item) => item.age !== null && item.age >= interval);

  if (!eligible.length) return null;
  // Oldest first, so nothing starves behind a programme refreshed recently.
  eligible.sort((a, b) => b.age - a.age);
  return eligible[0].row;
}

/** How many already-read programmes are currently overdue. */
export function dueCount(rows = [], now = Date.now(), intervalMs = DEFAULT_INTERVAL_MS) {
  const interval = clampInterval(intervalMs);
  return rows.filter((row) => {
    if (!row?.verified || !row?.lookup) return false;
    const age = ageOf(row, now);
    return age !== null && age >= interval;
  }).length;
}

/**
 * Whether one programme may be re-checked by hand right now.
 *
 * Separate from the automatic cadence on purpose. A person pressing a button
 * has a reason - a scope change they heard about, a handle they think moved -
 * and should not wait a full day for it. Four hours respects that without
 * letting a button become a poller.
 */
export function canRefresh(row, now = Date.now()) {
  if (!row?.verified || !row?.lookup) {
    // Never read: this is a first look, not a re-check, and nothing is being
    // re-requested.
    return { allowed: true, waitMs: 0, reason: "" };
  }
  const age = ageOf(row, now);
  if (age === null) return { allowed: true, waitMs: 0, reason: "" };
  if (age >= MANUAL_COOLDOWN_MS) return { allowed: true, waitMs: 0, reason: "" };

  const waitMs = MANUAL_COOLDOWN_MS - age;
  return {
    allowed: false,
    waitMs,
    reason: `Checked ${describeAge(age)}. Re-check available in ${describeAge(waitMs).replace(" ago", "")}.`,
  };
}

/**
 * How a programme's last read should be shown as a status.
 *
 * Deliberately a statement about the *page*, not about the programme. A 200
 * means its page is published and reachable; it does not mean the programme is
 * accepting submissions, and a light claiming that would be a fabrication
 * someone might act on. Whether a programme currently pays and for what lives
 * on its own page.
 */
export function pageStatus(row, now = Date.now()) {
  if (!row?.verified || !row?.lookup) {
    return { tone: "unknown", label: "Not checked", detail: "This page has not been read yet." };
  }
  const status = Number(row.lookup.status) || 0;
  const age = ageOf(row, now);

  if (status !== 200) {
    return {
      tone: "down",
      label: `Responded ${status}`,
      detail: "The page did not return normally. The handle may have changed or the programme may have moved.",
    };
  }
  if (age !== null && age >= MINIMUM_INTERVAL_MS) {
    return {
      tone: "stale",
      label: `Reachable, ${describeAge(age)}`,
      detail: "Its page responded when last read, but that was a while ago.",
    };
  }
  return {
    tone: "live",
    label: `Reachable, ${describeAge(age)}`,
    detail: "Its page is published and responded normally when last read. That is not a statement about whether it is accepting submissions.",
  };
}

/**
 * What a manual "refresh everything you have read" would actually do.
 *
 * Returned so the control can state the cost before it is pressed: a button
 * that quietly sends six requests is the thing this design is trying to avoid.
 */
export function refreshPlan(rows = []) {
  const targets = rows.filter((row) => row?.verified && row?.lookup);
  return {
    targets,
    requests: targets.length,
    spacingMs: SPACING_MS,
    estimatedMs: targets.length > 0 ? (targets.length - 1) * SPACING_MS : 0,
  };
}
