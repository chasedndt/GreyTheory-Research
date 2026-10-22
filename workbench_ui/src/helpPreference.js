/**
 * Whether inline "what to look for" hints are shown.
 *
 * Browser-local, for the same reason rotation is: this is presentation, not
 * evidence. Hiding a hint changes what you are shown, never what the system
 * knows, what was observed, or what any gate permits - so it has no business in
 * the private research store.
 *
 * Reads and writes are guarded because storage can be unavailable, full, or
 * cleared, and a missing preference must degrade to showing hints rather than
 * silently withholding them from a learner.
 */

export const HINTS_STORAGE_KEY = "greytheory.hints";
export const HINTS_CHANGED_EVENT = "greytheory:hints-changed";

function store(storage) {
  if (storage) return storage;
  try {
    return globalThis.localStorage || null;
  } catch {
    return null;
  }
}

export function readHintPreference(storage) {
  const target = store(storage);
  if (!target) return true;
  try {
    const raw = target.getItem(HINTS_STORAGE_KEY);
    // Absent means never chosen. A learner who has expressed no preference
    // should be taught, so the default is on.
    if (raw === null || raw === undefined) return true;
    return raw !== "false";
  } catch {
    return true;
  }
}

export function writeHintPreference(enabled, storage) {
  const target = store(storage);
  if (!target) return Boolean(enabled);
  try {
    target.setItem(HINTS_STORAGE_KEY, enabled ? "true" : "false");
  } catch {
    /* storage optional */
  }
  return Boolean(enabled);
}

/** Let open hints react to the Settings toggle without threading props. */
export function announceHintPreference(enabled) {
  try {
    globalThis.dispatchEvent?.(
      new CustomEvent(HINTS_CHANGED_EVENT, { detail: { enabled: Boolean(enabled) } }),
    );
  } catch {
    /* environments without CustomEvent simply do not live-update */
  }
}
