/**
 * The curriculum as an ordered path, not a menu.
 *
 * Two things were already true and never joined up. `SKILL_TRACKS` lists the
 * tracks in the order a learner walks them, and every lesson carries the
 * `trackId` it belongs to, in registry order which *is* teaching order. What
 * was missing is the join - so the Learn page rendered a thin parallel data set
 * and the real lessons were reachable only from elsewhere.
 *
 * The rule this module exists to enforce:
 *
 *     You are never asked about something you were not first taught.
 *
 * That is the property that makes ordered courseware work, and it is what the
 * old Learn page broke: it opened with two scenario questions and four
 * "confirm you can explain this" boxes, behind about a hundred words of
 * summary. Questions before material is interrogation, not teaching.
 *
 * So a lesson is reachable when everything before it in its track has been
 * completed. Not locked as punishment - the next one is always open, and every
 * earlier one stays open - but the *path* is explicit, so a beginner has an
 * obvious first step instead of a grid of equal-looking tiles.
 *
 * Completion here means the learner worked through a lesson's checks in this
 * browser. It is a practice record and nothing more: it awards no mastery,
 * proves no skill, and changes no scope. Mastery is six separately assessed
 * dimensions recorded by a person, and nothing in this file touches it.
 */

import { LESSONS } from "./lessons/index.js";
// Extension included deliberately: these modules are exercised by bare Node in
// the test suite, and Node's ESM loader does not resolve extensionless paths
// the way the bundler does.
import { SKILL_TRACKS } from "./learningPaths.js";

//: Where a learner's completed lessons are remembered. Browser-local, because
//: this is presentation and encouragement, not evidence.
export const PROGRESS_STORAGE_KEY = "greytheory.lessonProgress";

export function readProgress(storage) {
  const target = storage || (() => { try { return globalThis.localStorage; } catch { return null; } })();
  if (!target) return [];
  try {
    const raw = target.getItem(PROGRESS_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    // A corrupted value must not look like progress, and must not throw.
    return Array.isArray(parsed) ? parsed.filter((id) => typeof id === "string") : [];
  } catch {
    return [];
  }
}

export function writeProgress(completedIds, storage) {
  const target = storage || (() => { try { return globalThis.localStorage; } catch { return null; } })();
  const unique = [...new Set(completedIds.filter((id) => typeof id === "string"))];
  if (!target) return unique;
  try {
    target.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(unique));
  } catch {
    /* storage optional */
  }
  return unique;
}

/**
 * Every track, with its lessons in teaching order and their state.
 *
 * `state` is one of:
 *   "done"    - its checks were worked through in this browser
 *   "current" - the first lesson in the track that is not done
 *   "open"    - reachable, because everything before it is done
 *   "later"   - not yet reachable; something earlier comes first
 */
export function curriculumPath(completed = []) {
  const done = new Set(completed);

  return SKILL_TRACKS.map((track) => {
    const lessons = LESSONS.filter((lesson) => lesson.trackId === track.id);
    let currentTaken = false;

    const steps = lessons.map((lesson, index) => {
      const isDone = done.has(lesson.id);
      const priorAllDone = lessons.slice(0, index).every((item) => done.has(item.id));
      let state;
      if (isDone) {
        state = "done";
      } else if (priorAllDone && !currentTaken) {
        state = "current";
        currentTaken = true;
      } else if (priorAllDone) {
        state = "open";
      } else {
        state = "later";
      }
      return {
        id: lesson.id,
        title: lesson.title,
        level: lesson.level,
        duration: lesson.duration,
        oneLine: lesson.oneLine,
        cardId: lesson.cardId,
        checks: lesson.checks.length,
        position: index + 1,
        state,
      };
    });

    const doneCount = steps.filter((step) => step.state === "done").length;
    return {
      id: track.id,
      title: track.title,
      steps,
      total: steps.length,
      done: doneCount,
      // A track is "current" when it is the first with anything left to do, so
      // a learner arriving cold has exactly one obvious place to begin.
      complete: steps.length > 0 && doneCount === steps.length,
    };
  });
}

/** The single lesson a learner should open next, across all tracks. */
export function nextLesson(completed = []) {
  for (const track of curriculumPath(completed)) {
    const step = track.steps.find((item) => item.state === "current");
    if (step) return { track, step };
  }
  return null;
}

/** How far through the whole curriculum a learner is. */
export function overallProgress(completed = []) {
  const tracks = curriculumPath(completed);
  const total = tracks.reduce((sum, track) => sum + track.total, 0);
  const done = tracks.reduce((sum, track) => sum + track.done, 0);
  return { done, total, percent: total === 0 ? 0 : Math.round((done / total) * 100) };
}
