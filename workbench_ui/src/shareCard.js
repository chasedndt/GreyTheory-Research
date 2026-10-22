// Locally generated share card.
//
// Everything here runs in the browser and writes nothing anywhere until the
// learner explicitly exports. There is no upload path, and there is no server
// call — this file cannot reach the network even if asked to.
//
// The content rules matter more than the styling, so they are enforced rather
// than documented. A card is refused if it would carry:
//
//   * a programme name, target, host, or URL — sharing that implies research
//     activity against a named party, which is exactly what the scope policy
//     forbids in public claims;
//   * any word implying a real finding, vulnerability, or breach;
//   * any word implying certification or mastery, which the learner has not
//     been awarded and which this product never awards automatically.
//
// The card carries participation. "I practised tool authorization, 5 day
// streak" is honest and still worth posting. "GreyTheory Certified" is neither.

import { titleFor, titleProgress } from "./titles.js";

export const CARD_WIDTH = 1200;
export const CARD_HEIGHT = 630;

export const ACCENTS = {
  amber: { key: "amber", label: "Amber", ink: "#ffb600", glow: "rgba(255,182,0,.16)" },
  blue: { key: "blue", label: "Blue", ink: "#5aa9ff", glow: "rgba(90,169,255,.16)" },
  green: { key: "green", label: "Green", ink: "#43c98b", glow: "rgba(67,201,139,.16)" },
  violet: { key: "violet", label: "Violet", ink: "#b18cff", glow: "rgba(177,140,255,.16)" },
};

// Words that would turn a participation card into a claim.
const FORBIDDEN_PATTERNS = [
  /\bcertified?\b/i,
  /\bcertification\b/i,
  /\bmastery\b/i,
  /\bexpert\b/i,
  /\bvulnerabilit(y|ies)\b/i,
  /\bexploit(ed|s)?\b/i,
  /\bbreach(ed|es)?\b/i,
  /\bhacked\b/i,
  /\bpwned\b/i,
  /\bbount(y|ies)\b/i,
  /\bfinding\b/i,
  /\bdisclosure\b/i,
  /\bCVE-\d{4}-\d+/i,
  // Anything that looks like a target.
  /https?:\/\//i,
  /\b[a-z0-9-]+\.(com|net|org|io|dev|app|co|ai)\b/i,
  /\b\d{1,3}(\.\d{1,3}){3}\b/,
];

export class ShareCardRefused extends Error {}

/** Reject anything a learner might type that would make the card a claim. */
export function checkShareText(value, field) {
  const text = String(value ?? "");
  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(text)) {
      throw new ShareCardRefused(
        `The ${field} cannot mention targets, findings, or certification. ` +
          "A share card records what you practised, not what you found.",
      );
    }
  }
  return text;
}

// Text measurement. An SVG has no layout engine to ask, so a box drawn around
// text has to be computed from the font's own metrics. Guessing a per-character
// width is what made the streak pill too narrow for its own text.

/** IBM Plex Mono advance width, 600/1000 em for every glyph. */
const MONO_ADVANCE = 0.6;
/** Manrope ExtraBold. Deliberately over-estimated; see SLACK below. */
const RANK_ADVANCE = 0.66;

const FLOURISH_SIZE = 18;
const FLOURISH_PADDING = 16;
const RANK_SIZE = 82;
/** Left margin 88 to the progress ring's left edge at 906, less breathing room. */
const RANK_MAX_WIDTH = 790;

// A downloaded card is viewed wherever the learner opens it, and neither
// Manrope nor IBM Plex Mono will be installed there. The fallback metrics are
// close but not identical, so both measurements carry margin rather than
// fitting the named font exactly. Being a few pixels loose costs nothing;
// being a few pixels tight puts text through its own border.
const FLOURISH_SLACK = 10;

function monoWidth(text, size) {
  return Math.ceil(String(text).length * size * MONO_ADVANCE) + FLOURISH_SLACK;
}

/** The largest size at or below `size` that keeps `text` inside `maxWidth`. */
function fittedSize(text, size, maxWidth) {
  const width = String(text).length * size * RANK_ADVANCE;
  if (width <= maxWidth) return size;
  return Math.max(40, Math.floor(size * (maxWidth / width)));
}

function escapeXml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/** A handle is the learner's own label, not an identity claim. */
export function normaliseHandle(value) {
  const trimmed = String(value ?? "").trim().slice(0, 24);
  return checkShareText(trimmed, "handle");
}

export function normaliseAvatar(value) {
  // One or two characters: an emoji or initials. Nothing longer renders well.
  return [...String(value ?? "").trim()].slice(0, 2).join("");
}

/**
 * Build the share card as an SVG string.
 *
 * `participation` comes from the local achievement tracker, so every figure on
 * the card is something the learner actually did on this machine.
 */
export function buildShareCard({
  handle = "",
  avatar = "",
  accent = "amber",
  topic = "",
  participation = {},
} = {}) {
  const safeHandle = normaliseHandle(handle) || "Researcher";
  const safeTopic = checkShareText(String(topic ?? "").slice(0, 48), "topic");
  const glyph = normaliseAvatar(avatar) || safeHandle.slice(0, 1).toUpperCase();
  const theme = ACCENTS[accent] || ACCENTS.amber;

  const title = titleFor(participation);
  const progress = titleProgress(participation);
  const cards = Number(participation.cardsPractised ?? 0);
  const streak = Number(participation.streak ?? 0);
  const days = Number(participation.daysActive ?? 0);

  // Ring geometry for the progress toward the next title.
  const radius = 74;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference * progress;

  const stats = [
    ["Scenarios", `${cards}/12`],
    ["Day streak", String(streak)],
    ["Days active", String(days)],
  ];
  const statMarkup = stats
    .map(([label, value], index) => {
      const x = index * 250;
      return `
      <g transform="translate(${x},0)">
        <text x="0" y="0" font-family="IBM Plex Mono, monospace" font-size="18" fill="#7d90a4" letter-spacing="1.5">${escapeXml(label.toUpperCase())}</text>
        <text x="0" y="52" font-family="Manrope, Segoe UI, sans-serif" font-size="52" font-weight="800" fill="#e8eef5">${escapeXml(value)}</text>
      </g>`;
    })
    .join("");

  const flourishText = title.flourish
    ? `${title.flourish.toUpperCase()} · ${title.flourishCriterion}`
    : "";
  const flourish = flourishText
    ? `
    <g transform="translate(0,196)">
      <rect x="0" y="-27" width="${monoWidth(flourishText, FLOURISH_SIZE) + FLOURISH_PADDING * 2}" height="38" rx="19" fill="none" stroke="${theme.ink}" stroke-opacity="0.5"/>
      <text x="${FLOURISH_PADDING}" y="0" font-family="IBM Plex Mono, monospace" font-size="${FLOURISH_SIZE}" fill="${theme.ink}">${escapeXml(flourishText)}</text>
    </g>`
    : "";

  // The rank is the largest thing on the card, so it is also the one string
  // that can run into the progress ring. Shrink it to fit rather than let it
  // collide or be silently clipped.
  const rankSize = fittedSize(title.name, RANK_SIZE, RANK_MAX_WIDTH);

  const nextLine = title.next
    ? `${title.next.remaining} more to reach ${title.next.name}`
    : "Every scenario in the local deck practised";

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${CARD_WIDTH}" height="${CARD_HEIGHT}" viewBox="0 0 ${CARD_WIDTH} ${CARD_HEIGHT}" role="img" aria-label="GreyTheory practice card for ${escapeXml(safeHandle)}, ${escapeXml(title.name)}, ${escapeXml(title.criterion)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#08131d"/>
      <stop offset="0.55" stop-color="#0b1c2b"/>
      <stop offset="1" stop-color="#0e2436"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.82" cy="0.28" r="0.62">
      <stop offset="0" stop-color="${theme.glow}"/>
      <stop offset="1" stop-color="rgba(0,0,0,0)"/>
    </radialGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="${theme.ink}"/>
      <stop offset="1" stop-color="rgba(0,0,0,0)"/>
    </linearGradient>
  </defs>

  <rect width="${CARD_WIDTH}" height="${CARD_HEIGHT}" fill="url(#bg)"/>
  <rect width="${CARD_WIDTH}" height="${CARD_HEIGHT}" fill="url(#glow)"/>
  <rect x="0" y="0" width="${CARD_WIDTH}" height="5" fill="url(#rule)"/>
  <rect x="40" y="40" width="${CARD_WIDTH - 80}" height="${CARD_HEIGHT - 80}" rx="18" fill="none" stroke="#1d3346"/>

  <g transform="translate(88,104)">
    <circle cx="30" cy="22" r="30" fill="none" stroke="${theme.ink}" stroke-width="2.5"/>
    <text x="30" y="34" text-anchor="middle" font-family="Manrope, Segoe UI, sans-serif" font-size="26" font-weight="700" fill="${theme.ink}">${escapeXml(glyph)}</text>
    <text x="80" y="14" font-family="IBM Plex Mono, monospace" font-size="17" fill="#6f8398" letter-spacing="2.5">GREYTHEORY</text>
    <text x="80" y="46" font-family="Manrope, Segoe UI, sans-serif" font-size="30" font-weight="700" fill="#e8eef5">${escapeXml(safeHandle)}</text>
  </g>

  <g transform="translate(88,244)">
    <text x="0" y="0" font-family="IBM Plex Mono, monospace" font-size="18" fill="#6f8398" letter-spacing="2">PRACTICE RANK</text>
    <text x="0" y="76" font-family="Manrope, Segoe UI, sans-serif" font-size="${rankSize}" font-weight="800" fill="${theme.ink}">${escapeXml(title.name)}</text>
    <text x="0" y="118" font-family="IBM Plex Mono, monospace" font-size="19" fill="#9fb0c2">${escapeXml(title.criterion)}</text>
    <text x="0" y="150" font-family="Manrope, Segoe UI, sans-serif" font-size="20" fill="#7d90a4">${escapeXml(title.blurb)}</text>${flourish}
  </g>

  <g transform="translate(88,470)">${statMarkup}</g>

  <g transform="translate(980,236)">
    <circle cx="0" cy="0" r="${radius}" fill="none" stroke="#1d3346" stroke-width="14"/>
    <circle cx="0" cy="0" r="${radius}" fill="none" stroke="${theme.ink}" stroke-width="14" stroke-linecap="round"
      stroke-dasharray="${dash.toFixed(1)} ${(circumference - dash).toFixed(1)}" transform="rotate(-90)"/>
    <text x="0" y="-4" text-anchor="middle" font-family="Manrope, Segoe UI, sans-serif" font-size="44" font-weight="800" fill="#e8eef5">${cards}</text>
    <text x="0" y="26" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="16" fill="#7d90a4">OF 12</text>
  </g>
  <text x="980" y="342" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="16" fill="#6f8398">${escapeXml(nextLine)}</text>

  <g transform="translate(88,${CARD_HEIGHT - 74})">
    <text x="0" y="0" font-family="Manrope, Segoe UI, sans-serif" font-size="21" fill="#9fb0c2">${escapeXml(safeTopic ? `Practised ${safeTopic}` : "Learning security by practising it")}</text>
    <text x="0" y="30" font-family="IBM Plex Mono, monospace" font-size="16" fill="#5d7086">Apache-2.0 · a practice record, not a certification</text>
  </g>
</svg>`;
}

/** Trigger a download of the card. Nothing is uploaded. */
export function downloadShareCard(svg, filename = "greytheory-practice-card.svg") {
  const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
