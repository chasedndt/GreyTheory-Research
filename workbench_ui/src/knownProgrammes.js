/**
 * A starting list of real, long-standing public bug bounty programmes.
 *
 * Read what this is carefully, because the distinction is the whole point.
 *
 * These are **suggestions to look up**, not verified records. Each entry names
 * a programme that has run publicly for years, on the platform and handle
 * recorded here. But nothing in this file has been fetched, checked, or
 * confirmed by the application - it is prior knowledge written down, and prior
 * knowledge goes stale. A programme can close, move platform, or change its
 * handle without this file knowing.
 *
 * So every row stays marked unverified until *you* look it up. The lookup is
 * what turns a suggestion into evidence: it retrieves the real page, records
 * its size and SHA-256, and proves the handle resolves. If a handle here is
 * wrong, the lookup fails and says so, which is the correct outcome rather
 * than an embarrassment to hide.
 *
 * This is deliberately not a live feed. No approved source enumerates
 * programmes, and scraping a platform's index page is both fragile and a terms
 * question. A short honest list you can verify beats a long invented one.
 *
 * `why` is my own assessment of what makes each a reasonable place to learn -
 * opinion, offered as opinion, not a claim about the programme's terms. The
 * programme's own scope is the only thing that governs what may be tested, and
 * that comes from a compiled contract, never from here.
 *
 * `rewards` deliberately carries no figures. Whether a programme pays at all
 * is stable and worth knowing up front; what it pays is a moving number that
 * changes without notice, and stating one from memory would be inventing a
 * fact you might act on. Amounts belong to the programme's own page, and until
 * something parses that page the honest answer is that we have not read them.
 */

//: Where each platform publishes a programme, so a row can link straight to it.
//: These mirror the origins the fetcher is pinned to, and are the only place
//: reward figures actually live - they change without notice, so the link is
//: the honest answer where a number would be an invented one.
export const PLATFORM_ORIGIN = {
  hackerone: "https://hackerone.com",
  bugcrowd: "https://bugcrowd.com",
  intigriti: "https://www.intigriti.com",
  yeswehack: "https://yeswehack.com",
};

export function programmeUrl(platform, handle) {
  const origin = PLATFORM_ORIGIN[platform];
  if (!origin || !handle) return "";
  return `${origin}/${handle}`;
}

//: Whether a programme pays, not what it pays.
export const REWARD_POSTURE = {
  paid: {
    label: "Pays bounties",
    detail: "Monetary rewards. Amounts are set by the programme and change; this list does not record them.",
  },
  recognition: {
    label: "Recognition only",
    detail: "A disclosure programme with no monetary reward. Valid findings earn credit, not payment.",
  },
  unknown: {
    label: "Reward posture unknown",
    detail: "Not recorded in this list. The programme's own page is the only authority on it.",
  },
};

export const KNOWN_PROGRAMMES = [
  {
    id: "hackerone:gitlab",
    platform: "hackerone",
    handle: "gitlab",
    name: "GitLab",
    rewards: "paid",
    target: "DevOps platform, with its source code publicly available",
    why:
      "Source is readable, so logic and query construction can be studied "
      + "directly rather than guessed at. Its scope also permits testing an "
      + "instance you run yourself, which is the safest place to learn.",
  },
  {
    id: "hackerone:security",
    platform: "hackerone",
    handle: "security",
    name: "HackerOne",
    rewards: "paid",
    target: "The bug bounty platform itself",
    why:
      "A platform whose business is vulnerability handling tends to write "
      + "unusually clear scope and disclosure terms, which makes it a good "
      + "programme to read even before you test anything.",
  },
  {
    id: "hackerone:github",
    platform: "hackerone",
    handle: "github",
    name: "GitHub",
    rewards: "paid",
    target: "Source hosting, CI, and a large authenticated web surface",
    why:
      "Dense with object-ownership and permission boundaries - the shape "
      + "behind most access-control findings - across an application most "
      + "people already understand well.",
  },
  {
    id: "hackerone:shopify",
    platform: "hackerone",
    handle: "shopify",
    name: "Shopify",
    rewards: "paid",
    target: "Commerce platform with multi-tenant stores and an app ecosystem",
    why:
      "Commerce flows are where business-logic flaws live: discounts, refunds "
      + "and order state carry rules a scanner has no model of.",
  },
  {
    id: "hackerone:mozilla",
    platform: "hackerone",
    handle: "mozilla",
    name: "Mozilla",
    rewards: "paid",
    target: "Browser, web services and developer infrastructure",
    why:
      "A long-running programme from an organisation that publishes its "
      + "security reasoning openly, so the findings and fixes are unusually "
      + "instructive to read.",
  },
  {
    id: "hackerone:automattic",
    platform: "hackerone",
    handle: "automattic",
    name: "Automattic",
    rewards: "paid",
    target: "WordPress.com and related publishing services",
    why:
      "A very large user-content surface, which is where input handling and "
      + "the browser-context injection classes actually matter in practice.",
  },
];

const BY_ID = new Map(KNOWN_PROGRAMMES.map((entry) => [entry.id, entry]));

export function knownProgramme(id) {
  return BY_ID.get(id) || null;
}

/**
 * Join the suggestions to what has actually been retrieved.
 *
 * A row is only ever "verified" because a lookup exists for it, never because
 * this file says so. Anything looked up that is *not* in the list is included
 * too, so a programme you found yourself is not second-class on the board.
 */
export function boardRows(lookups = []) {
  const byIdentifier = new Map(lookups.map((item) => [item.identifier, item]));

  const suggested = KNOWN_PROGRAMMES.map((entry) => {
    const lookup = byIdentifier.get(entry.id) || null;
    return { ...entry, lookup, verified: Boolean(lookup), suggested: true };
  });

  const discovered = lookups
    .filter((item) => !BY_ID.has(item.identifier))
    .map((item) => ({
      id: item.identifier,
      platform: item.platform,
      handle: item.handle,
      name: item.handle,
      // Nothing is known about a programme you found yourself beyond what was
      // retrieved, and guessing would be worse than saying so.
      rewards: "unknown",
      target: "",
      why: "",
      lookup: item,
      verified: true,
      suggested: false,
    }));

  // Verified first: what you have actually retrieved outranks what this file
  // merely suggests.
  return [...discovered, ...suggested].sort((a, b) => {
    if (a.verified !== b.verified) return a.verified ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
}
