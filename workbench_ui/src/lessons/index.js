// Lesson registry. One file per lesson so entries never collide on edit.
//
// Lessons are curriculum content. They describe what a learner should
// understand — they never record what a learner has done, and they never
// carry progress, scores, or mastery. Those come from persisted evidence.

import { accessControl } from "./access-control.js";
import { agentEvidence } from "./agent-evidence.js";
import { aiTrustBoundaries } from "./ai-trust-boundaries.js";
import { apiAuthorization } from "./api-authorization.js";
import { businessLogic } from "./business-logic.js";
import { contextIsolation } from "./context-isolation.js";
import { csrf } from "./csrf.js";
import { domXss } from "./dom-xss.js";
import { evidenceBasics } from "./evidence-basics.js";
import { evidenceQuality } from "./evidence-quality.js";
import { httpAndSessions } from "./http-and-sessions.js";
import { idorBola } from "./idor-bola.js";
import { independentAgentCase } from "./independent-agent-case.js";
import { independentCase } from "./independent-case.js";
import { independentReport } from "./independent-report.js";
import { inputHandling } from "./input-handling.js";
import { mcpAbusePatterns } from "./mcp-abuse-patterns.js";
import { memoryPoisoning } from "./memory-poisoning.js";
import { probabilityLanguage } from "./probability-language.js";
import { promptInjection } from "./prompt-injection.js";
import { reflectedXss } from "./reflected-xss.js";
import { safeExperiments } from "./safe-experiments.js";
import { scopeAndAuthority } from "./scope-and-authority.js";
import { securityEthics } from "./security-ethics.js";
import { ssrf } from "./ssrf.js";
import { threatModelling } from "./threat-modelling.js";
import { toolAuthorization } from "./tool-authorization.js";
import { trustBoundaries } from "./trust-boundaries.js";

// Registry order follows the sequence a learner walks each track, so
// `lessonsForTrack` returns them in teaching order rather than import order.
export const LESSONS = [
  // Foundations
  securityEthics,
  scopeAndAuthority,
  evidenceBasics,
  trustBoundaries,
  threatModelling,
  safeExperiments,
  probabilityLanguage,
  independentCase,
  // Web & API Security
  httpAndSessions,
  accessControl,
  // After access control, not before it. Forgery does follow from how the
  // browser attaches the credential sessions introduced - but it is a
  // Foundation-level idea, and putting it ahead of a Beginner lesson asks
  // someone to reason about forged cross-site requests before they have been
  // taught who is allowed to do what.
  csrf,
  idorBola,
  inputHandling,
  // The concrete browser-context case of the injection shape above, then the
  // variant whose value never reaches the server at all.
  reflectedXss,
  domXss,
  // Follows input handling: a value reaching something that makes network
  // requests, rather than something that parses a query.
  ssrf,
  apiAuthorization,
  businessLogic,
  evidenceQuality,
  independentReport,
  // Agent Security
  aiTrustBoundaries,
  promptInjection,
  toolAuthorization,
  contextIsolation,
  mcpAbusePatterns,
  memoryPoisoning,
  agentEvidence,
  independentAgentCase,
];

const BY_ID = new Map(LESSONS.map((lesson) => [lesson.id, lesson]));
const BY_CARD = new Map(
  LESSONS.filter((lesson) => lesson.cardId).map((lesson) => [lesson.cardId, lesson]),
);

export function lessonById(id) {
  return BY_ID.get(id) || null;
}

/** Look up the lesson that teaches a catalogue card, if one is written yet. */
export function lessonForCard(cardId) {
  return BY_CARD.get(cardId) || null;
}

/** Lessons written for a track, in registry order. */
export function lessonsForTrack(trackId) {
  return LESSONS.filter((lesson) => lesson.trackId === trackId);
}
