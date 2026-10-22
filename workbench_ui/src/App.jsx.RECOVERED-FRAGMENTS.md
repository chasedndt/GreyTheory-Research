# Recovered fragments: App.jsx

Original path: `E:\Projects\GreyTheory\2026-09-01-workbench-read-model-binding\worktree\workbench_ui\src\App.jsx`. The whole file was never captured in a transcript, so these are the
recorded edits in time order: each shows the text that was replaced and the text that replaced it.
Append-style logs can usually be reassembled from the 'new text' blocks.

## 1.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const closeModal = useCallback(() => setModal(null), []);
````

New text:

````
  const closeModal = useCallback(() => setModal(null), []);
  // One opener for both entry points - Mission Control's skill trajectory and
  // the curriculum page - so a lesson opens the same way wherever it is reached.
  //
  // The curriculum route referenced this name while nothing declared it, which
  // threw during render and left the entire app unmounted on a blank page. Same
  // class as the activePack note above: legal JavaScript, so the bundler builds
  // it happily, and the node tests read this module as text without ever
  // evaluating it. Only loading the page finds this.
  const openLesson = useCallback((lesson) => {
    setActiveLesson(lesson);
    setModal("lesson");
  }, []);
````

## 2.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
openLesson={(lesson) => { setActiveLesson(lesson); setModal("lesson"); }} />
````

New text:

````
openLesson={openLesson} />
````

## 3.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import { readCollapsed, writeCollapsed } from "./onboarding.js";
````

New text:

````
import { initialCollapsed, writeCollapsed } from "./onboarding.js";
````

## 4.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const [guideCollapsed, setGuideCollapsed] = useState(() => readCollapsed());
````

New text:

````
  // A phone starts with the guide collapsed unless someone has already chosen:
  // expanded, it covers most of a narrow screen.
  const [guideCollapsed, setGuideCollapsed] = useState(() => {
    let narrow = false;
    try {
      narrow = Boolean(window.matchMedia?.("(max-width: 760px)").matches);
    } catch { /* no media queries: treat as wide */ }
    return initialCollapsed({ narrow });
  });
````

## 5.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
shortlist={shortlist} onShortlist={onShortlist} />
````

New text:

````
shortlist={shortlist} onShortlist={onShortlist} onOpenLesson={openLesson} />
````

## 6. 2026-09-14T22:39:50.129Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  curriculumFromSnapshot,
````

New text:

````
  campaignFromSnapshot,
  curriculumFromSnapshot,
````

## 7. 2026-09-14T22:39:52.000Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const curriculum = useMemo(() => curriculumFromSnapshot(snapshot), [snapshot]);
````

New text:

````
  const curriculum = useMemo(() => curriculumFromSnapshot(snapshot), [snapshot]);
  const campaign = useMemo(() => campaignFromSnapshot(snapshot), [snapshot]);
````

## 8. 2026-09-14T22:39:53.355Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
curriculum={curriculum} rotationState={rotationState}
````

New text:

````
curriculum={curriculum} campaign={campaign} rotationState={rotationState}
````

## 9. 2026-09-14T22:39:55.408Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
function MissionControl({ navigate, startMission, journey, persistenceMode, activePack, selectPack, openCoach, evidencedCards, openLesson, curriculum, rotationState }) {
````

New text:

````
function MissionControl({ navigate, startMission, journey, persistenceMode, activePack, selectPack, openCoach, evidencedCards, openLesson, curriculum, campaign, rotationState }) {
````

## 10. 2026-09-14T22:39:56.858Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <StudyPlan curriculum={curriculum} />
````

New text:

````
        <CampaignPanel campaign={campaign} />
        <StudyPlan curriculum={curriculum} />
````

## 11. 2026-09-14T22:41:42.100Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  coachHistoryFromSnapshot,
  commandMode,
  createWorkbenchCommand,
  fetchWorkbenchSnapshot,
  campaignFromSnapshot,
  curriculumFromSnapshot,
````

New text:

````
  campaignFromSnapshot,
  coachHistoryFromSnapshot,
  commandMode,
  createWorkbenchCommand,
  fetchWorkbenchSnapshot,
  curriculumFromSnapshot,
````

## 12. 2026-09-14T22:42:21.170Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import PlatformConnections from "./PlatformConnections.jsx";
````

New text:

````
import PlatformConnections from "./PlatformConnections.jsx";
import CampaignPanel from "./CampaignPanel.jsx";
````

## 13. 2026-09-14T23:12:10.517Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const journey = learningState.journey;
  // Only receipts for the card under assessment may be cited. A learner cannot
  // assess a card on the strength of practice they did somewhere else.
  const assessmentEvidence = useMemo(() => {
    const card = journey?.cardId || activePack?.primaryCard || "";
    return learningState.receipts
      .filter((receipt) => receipt.attributes?.card_id === card)
      .map((receipt) => receipt.id)
      .filter(Boolean);
  }, [learningState, journey, activePack]);
  const activePack = journey ? casePackForCard(journey.cardId) : casePackById(selectedPackId);
````

New text:

````
  const journey = learningState.journey;
  // Declared before assessmentEvidence, which reads it in both its body and its
  // dependency array. React evaluates that array during render, so leaving the
  // const below it threw "Cannot access 'activePack' before initialization" and
  // the whole App failed to mount. A bundler cannot catch this and the node
  // tests never evaluate this module, so only loading the page finds it.
  const activePack = journey ? casePackForCard(journey.cardId) : casePackById(selectedPackId);
  // Only receipts for the card under assessment may be cited. A learner cannot
  // assess a card on the strength of practice they did somewhere else.
  const assessmentEvidence = useMemo(() => {
    const card = journey?.cardId || activePack?.primaryCard || "";
    return learningState.receipts
      .filter((receipt) => receipt.attributes?.card_id === card)
      .map((receipt) => receipt.id)
      .filter(Boolean);
  }, [learningState, journey, activePack]);
````

## 14. 2026-09-15T00:14:16.339Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  learningStateFromSnapshot,
  sendWorkbenchCommand,
````

New text:

````
  learningStateFromSnapshot,
  reviewFromSnapshot,
  sendWorkbenchCommand,
````

## 15. 2026-09-15T00:14:17.933Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import CampaignPanel from "./CampaignPanel.jsx";
````

New text:

````
import CampaignPanel from "./CampaignPanel.jsx";
import ReviewPanel from "./ReviewPanel.jsx";
````

## 16. 2026-09-15T00:14:19.815Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const campaign = useMemo(() => campaignFromSnapshot(snapshot), [snapshot]);
````

New text:

````
  const campaign = useMemo(() => campaignFromSnapshot(snapshot), [snapshot]);
  const review = useMemo(() => reviewFromSnapshot(snapshot), [snapshot]);
````

## 17. 2026-09-15T00:14:21.284Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
curriculum={curriculum} campaign={campaign} rotationState={rotationState}
````

New text:

````
curriculum={curriculum} campaign={campaign} review={review} rotationState={rotationState}
````

## 18. 2026-09-15T00:14:22.641Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
openLesson, curriculum, campaign, rotationState }) {
````

New text:

````
openLesson, curriculum, campaign, review, rotationState }) {
````

## 19. 2026-09-15T00:14:24.052Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <CampaignPanel campaign={campaign} />
````

New text:

````
        <CampaignPanel campaign={campaign} />
        <ReviewPanel review={review} />
````

## 20. 2026-09-15T00:30:08.292Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  return <footer className="global-footer"><div><ShieldCheck /><span><strong>LOCAL_FIXTURE</strong><small>All activities are isolated and safe.</small></span></div><div><Target /><span><strong>No live targets</strong><small>Research-only environment.</small></span></div><div><UserCircle /><span><strong>Human approval required</strong><small>You control what happens next.</small></span></div><div><FileText /><span><strong>Apache-2.0</strong><small>Open source research preview.</small></span></div></footer>;
````

New text:

````
  // Compact by design: these four are governance statements, so the labels
  // stay at every width. Only the explanatory sentences collapse, and they
  // remain in the DOM for assistive technology with the wording repeated in
  // `title` so a pointer can still reach it.
  return <footer className="global-footer"><div title="All activities are isolated and safe."><ShieldCheck /><span><strong>LOCAL_FIXTURE</strong><small>All activities are isolated and safe.</small></span></div><div title="Research-only environment."><Target /><span><strong>No live targets</strong><small>Research-only environment.</small></span></div><div title="You control what happens next."><UserCircle /><span><strong>Human approval required</strong><small>You control what happens next.</small></span></div><div title="Open source research preview."><FileText /><span><strong>Apache-2.0</strong><small>Open source research preview.</small></span></div></footer>;
````

## 21. 2026-09-15T01:08:25.206Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import CampaignPanel from "./CampaignPanel.jsx";
import ReviewPanel from "./ReviewPanel.jsx";
````

New text:

````
import BountyWorkspace from "./BountyWorkspace.jsx";
````

## 22. 2026-09-15T01:08:26.569Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <CampaignPanel campaign={campaign} />
        <ReviewPanel review={review} />
````

New text:

````
        <BountyWorkspace campaign={campaign} review={review} />
````

## 23. 2026-09-15T01:17:04.408Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <BountyWorkspace campaign={campaign} review={review} />
        <StudyPlan curriculum={curriculum} />
````

New text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} />
````

## 24. 2026-09-15T01:17:52.465Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
function StudyPlan({ curriculum }) {
  const [programmeId, setProgrammeId] = useState(null);
  if (!curriculum?.available || !curriculum.programmes.length) return null;

  const active =
    curriculum.programmes.find((entry) => entry.programmeId === programmeId)
    || curriculum.programmes[0];

  return (
    <section className="surface study-plan" aria-labelledby="study-plan-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Selected from real programme scope</span>
          <h2 id="study-plan-title">What this programme will ask of you</h2>
        </div>
        {curriculum.programmes.length > 1 && (
          <div className="study-plan__switch" role="group" aria-label="Programme">
            {curriculum.programmes.map((entry) => (
              <button key={entry.programmeId} type="button"
                className={entry.programmeId === active.programmeId ? "is-selected" : ""}
                aria-pressed={entry.programmeId === active.programmeId}
                onClick={() => setProgrammeId(entry.programmeId)}>{entry.programmeId}</button>
            ))}
          </div>
        )}
      </div>
      <ol className="study-plan__topics">
        {active.topics.map((topic) => (
          <li key={topic.cardId}>
            <span className="study-plan__rank">{topic.rank}</span>
            <div>
              <strong>{topic.cardId}</strong>
              <p>{topic.reason}</p>
              {topic.matchedAssets.length > 0
                ? <small>Because the scope lists {topic.matchedAssets.join(", ")}</small>
                : topic.matchedContext.length > 0
                  ? <small>From the programme's own description: {topic.matchedContext.join(", ")}</small>
                  : null}
            </div>
          </li>
        ))}
      </ol>
      {active.notes.length > 0 && (
        <div className="study-plan__notes">
          <span className="eyebrow">This programme prohibits</span>
          <ul>{active.notes.map((note) => <li key={note}>{note}</li>)}</ul>
        </div>
      )}
      <footer className="study-plan__boundary">
        <ShieldCheck />
        <p>Selected by reading compiled programme authority. This is a teaching aid, not a test plan: it says what to understand, never what to attack, and grants no permission to touch any asset.</p>
      </footer>
    </section>
  );
}

function LearnerLoop({ current = 1, onSelect }) {
````

New text:

````
// StudyPlan now lives in ./StudyPlan.jsx so BountyWorkspace can render it for
// the single selected bounty. Given one programme its switcher does not draw,
// which is how the workspace came to own selection for all three panels.

function LearnerLoop({ current = 1, onSelect }) {
````

## 25. 2026-09-15T10:16:22.082Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
function MissionControl({ navigate, startMission, journey, persistenceMode, activePack, selectPack, openCoach, evidencedCards, openLesson, curriculum, campaign, review, rotationState }) {
````

New text:

````
function MissionControl({ navigate, startMission, journey, persistenceMode, activePack, selectPack, openCoach, evidencedCards, openLesson, curriculum, campaign, review, rotationState, onRecordReview }) {
````

## 26. 2026-09-15T10:16:23.817Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} />
````

New text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} persistenceMode={persistenceMode} onRecordReview={onRecordReview} />
````

## 27. 2026-09-15T10:16:55.981Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  async function captureProof() {
````

New text:

````
  async function recordProgrammeReview({ programmeId, reviewer }) {
    if (persistenceMode !== "interactive") {
      setNotice("Connect the local application to record a review. A review that is not persisted is not a review.");
      return;
    }
    try {
      const { result } = await dispatch(createWorkbenchCommand({
        kind: "review_programme",
        fields: { programme_id: programmeId, reviewer },
        // Reviewing states that a person read a clean compile. It is a claim
        // about having read something, not permission to act on it, so it asks
        // for no authority and leaves the programme's own ceiling untouched.
        requestedAuthority: "NONE",
        humanAcknowledged: true,
      }));
      // The server says what changed and what stayed capped; prefer its words.
      setNotice(result?.message || `${programmeId} is recorded as reviewed by ${reviewer}.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "The review could not be recorded.");
    }
  }

  async function captureProof() {
````

## 28. 2026-09-15T10:16:57.844Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
rotationState={rotationState} openLesson={(lesson) => { setActiveLesson(lesson); setModal("lesson"); }} />,
````

New text:

````
rotationState={rotationState} onRecordReview={recordProgrammeReview} openLesson={(lesson) => { setActiveLesson(lesson); setModal("lesson"); }} />,
````

## 29. 2026-09-15T11:02:07.452Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import BountyWorkspace from "./BountyWorkspace.jsx";
````

New text:

````
import BountyWorkspace from "./BountyWorkspace.jsx";
import { announceHintPreference, readHintPreference, writeHintPreference } from "./helpPreference.js";
````

## 30. 2026-09-15T11:02:09.544Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const [lessonHints, setLessonHints] = useState(true);
````

New text:

````
  // Reads the same browser-local preference the hints themselves read. This
  // toggle previously changed nothing but its own caption, so the promise that
  // hints were "hidden for independent practice" was not true.
  const [lessonHints, setLessonHints] = useState(() => readHintPreference());
````

## 31. 2026-09-15T11:02:11.066Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
onChange={(event) => setLessonHints(event.target.checked)} />
````

New text:

````
onChange={(event) => { const next = event.target.checked; setLessonHints(next); writeHintPreference(next); announceHintPreference(next); }} />
````

## 32. 2026-09-15T15:33:54.054Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const review = useMemo(() => reviewFromSnapshot(snapshot), [snapshot]);
````

New text:

````
  const review = useMemo(() => reviewFromSnapshot(snapshot), [snapshot]);
  const shortlist = useMemo(() => shortlistFromSnapshot(snapshot), [snapshot]);
````

## 33. 2026-09-15T15:33:59.986Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  async function recordProgrammeReview({ programmeId, reviewer }) {
````

New text:

````
  // Curating the shortlist. Each pins its write to the revision the panel was
  // showing, so a change made elsewhere is refused rather than overwritten.
  async function curateShortlist(kind, fields, expectedRevision, fallback) {
    if (persistenceMode !== "interactive") {
      setNotice("Connect the local application to change your shortlist.");
      return;
    }
    try {
      const { result } = await dispatch(createWorkbenchCommand({
        kind,
        fields,
        expectedRevision,
      }));
      setNotice(result?.message || fallback);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : fallback);
    }
  }

  async function shortlistProgramme(programmeId) {
    // A new entry has no revision to pin; the store refuses a duplicate itself.
    await curateShortlist(
      "shortlist_programme",
      { programme_id: programmeId },
      null,
      `${programmeId} could not be shortlisted.`,
    );
  }

  async function archiveProgramme({ programmeId, revision }) {
    await curateShortlist(
      "archive_programme",
      { programme_id: programmeId },
      revision,
      `${programmeId} could not be set aside.`,
    );
  }

  async function restoreProgramme({ programmeId, revision }) {
    await curateShortlist(
      "restore_programme",
      { programme_id: programmeId },
      revision,
      `${programmeId} could not be restored.`,
    );
  }

  async function recordProgrammeReview({ programmeId, reviewer }) {
````

## 34. 2026-09-15T15:34:02.397Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
function MissionControl({ navigate, startMission, journey, persistenceMode, activePack, selectPack, openCoach, evidencedCards, openLesson, curriculum, campaign, review, rotationState, onRecordReview }) {
````

New text:

````
function MissionControl({ navigate, startMission, journey, persistenceMode, activePack, selectPack, openCoach, evidencedCards, openLesson, curriculum, campaign, review, rotationState, onRecordReview, shortlist, onArchiveProgramme, onRestoreProgramme }) {
````

## 35. 2026-09-15T15:34:05.122Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} persistenceMode={persistenceMode} onRecordReview={onRecordReview} />
````

New text:

````
        {/* The working set first, then the one bounty you are focused on. */}
        <ShortlistPanel shortlist={shortlist} persistenceMode={persistenceMode} onArchive={onArchiveProgramme} onRestore={onRestoreProgramme} />
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} persistenceMode={persistenceMode} onRecordReview={onRecordReview} />
````

## 36. 2026-09-15T15:34:07.001Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
rotationState={rotationState} onRecordReview={recordProgrammeReview} openLesson=
````

New text:

````
rotationState={rotationState} onRecordReview={recordProgrammeReview} shortlist={shortlist} onArchiveProgramme={archiveProgramme} onRestoreProgramme={restoreProgramme} openLesson=
````

## 37. 2026-09-15T15:34:49.914Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  sendWorkbenchCommand,
  validateLocalConnection,
} from "./workbenchApi";
````

New text:

````
  sendWorkbenchCommand,
  shortlistFromSnapshot,
  validateLocalConnection,
} from "./workbenchApi";
````

## 38. 2026-09-15T15:34:51.502Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import BountyWorkspace from "./BountyWorkspace.jsx";
````

New text:

````
import BountyWorkspace from "./BountyWorkspace.jsx";
import ShortlistPanel from "./ShortlistPanel.jsx";
````

## 39. 2026-09-15T15:35:24.219Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
rotationState, onRecordReview, shortlist, onArchiveProgramme, onRestoreProgramme }) {
````

New text:

````
rotationState, onRecordReview, shortlist, onShortlist, onArchiveProgramme, onRestoreProgramme }) {
````

## 40. 2026-09-15T15:35:26.338Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} persistenceMode={persistenceMode} onRecordReview={onRecordReview} />
````

New text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} persistenceMode={persistenceMode} onRecordReview={onRecordReview} shortlist={shortlist} onShortlist={onShortlist} />
````

## 41. 2026-09-15T15:35:28.149Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
shortlist={shortlist} onArchiveProgramme={archiveProgramme} onRestoreProgramme={restoreProgramme} openLesson=
````

New text:

````
shortlist={shortlist} onShortlist={shortlistProgramme} onArchiveProgramme={archiveProgramme} onRestoreProgramme={restoreProgramme} openLesson=
````

## 42. 2026-09-15T16:29:44.693Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  reviewFromSnapshot,
  sendWorkbenchCommand,
````

New text:

````
  researchFromSnapshot,
  reviewFromSnapshot,
  sendWorkbenchCommand,
````

## 43. 2026-09-15T16:29:46.306Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import ShortlistPanel from "./ShortlistPanel.jsx";
````

New text:

````
import ShortlistPanel from "./ShortlistPanel.jsx";
import ResearchWorkspacePanel from "./ResearchWorkspacePanel.jsx";
````

## 44. 2026-09-15T16:29:48.131Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const shortlist = useMemo(() => shortlistFromSnapshot(snapshot), [snapshot]);
````

New text:

````
  const shortlist = useMemo(() => shortlistFromSnapshot(snapshot), [snapshot]);
  const research = useMemo(() => researchFromSnapshot(snapshot), [snapshot]);
````

## 45. 2026-09-15T16:29:49.780Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
shortlist, onShortlist, onArchiveProgramme, onRestoreProgramme }) {
````

New text:

````
shortlist, onShortlist, onArchiveProgramme, onRestoreProgramme, research }) {
````

## 46. 2026-09-15T16:29:52.664Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} persistenceMode={persistenceMode} onRecordReview={onRecordReview} shortlist={shortlist} onShortlist={onShortlist} />
````

New text:

````
        <BountyWorkspace campaign={campaign} review={review} curriculum={curriculum} persistenceMode={persistenceMode} onRecordReview={onRecordReview} shortlist={shortlist} onShortlist={onShortlist} />
        {/* Where investigation happens once a contract has been reviewed. */}
        <ResearchWorkspacePanel research={research} />
````

## 47. 2026-09-15T16:29:54.273Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
onArchiveProgramme={archiveProgramme} onRestoreProgramme={restoreProgramme} openLesson=
````

New text:

````
onArchiveProgramme={archiveProgramme} onRestoreProgramme={restoreProgramme} research={research} openLesson=
````

## 48. 2026-09-15T17:58:29.183Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <div className="sidebar-profile"><div>GT</div><span><strong>Grey Researcher</strong><small>Learner · local</small></span><CaretDown /></div>
````

New text:

````
        <button type="button" className="sidebar-profile" onClick={() => setModal("progress")} aria-label="Open your local progress record"><span className="sidebar-profile__avatar">GT</span><span className="sidebar-profile__identity"><strong>Grey Researcher</strong><small>Learner · local</small></span><CaretDown /></button>
````

## 49. 2026-09-15T17:58:31.655Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <div className="sidebar-mobile"><Brand /><button ref={mobileNavCloseRef} className="icon-button" onClick={() => setMobileNav(false)} aria-label="Close navigation"><X /></button></div>
````

New text:

````
        <div className="sidebar-mobile"><Brand /><button ref={mobileNavCloseRef} className="icon-button" onClick={() => setMobileNav(false)} aria-label="Close navigation"><X /></button></div>
        <button type="button" className="rail-toggle" onClick={toggleRail} aria-expanded={!railCollapsed} aria-controls="primary-sidebar" aria-label={railCollapsed ? "Expand the navigation rail" : "Collapse the navigation rail"}><CaretDown /><span>Collapse</span></button>
````

## 50. 2026-09-15T17:58:34.701Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    <div className="app-shell">
      <a className="skip-link" href="#workspace-main">Skip to workspace</a>
````

New text:

````
    <div className="app-shell" data-rail={railCollapsed ? "collapsed" : "expanded"}>
      <a className="skip-link" href="#workspace-main">Skip to workspace</a>
````

## 51. 2026-09-15T17:58:36.725Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const persistRotation = useCallback((next) => {
````

New text:

````
  // Rail width is presentation, like the hint preference: it changes what you
  // are shown, never what is recorded or permitted, so it belongs in browser
  // storage rather than the research record.
  const [railCollapsed, setRailCollapsed] = useState(() => {
    try {
      return window.localStorage?.getItem("greytheory.rail") === "collapsed";
    } catch { return false; }
  });
  const toggleRail = useCallback(() => {
    setRailCollapsed((previous) => {
      const next = !previous;
      try {
        window.localStorage?.setItem("greytheory.rail", next ? "collapsed" : "expanded");
      } catch { /* storage optional */ }
      return next;
    });
  }, []);

  const persistRotation = useCallback((next) => {
````

## 52. 2026-09-15T18:06:31.908Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const research = useMemo(() => researchFromSnapshot(snapshot), [snapshot]);
````

New text:

````
  const research = useMemo(() => researchFromSnapshot(snapshot), [snapshot]);
  const registeredProgrammes = useMemo(() => programmesFromSnapshot(snapshot), [snapshot]);
````

## 53. 2026-09-15T18:06:33.433Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  researchFromSnapshot,
  reviewFromSnapshot,
````

New text:

````
  programmesFromSnapshot,
  researchFromSnapshot,
  reviewFromSnapshot,
````

## 54. 2026-09-15T18:07:24.114Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
function ProgrammesView() {
  const [selectedId, setSelectedId] = useState(PROGRAMME_READINESS[0].id);
  const [stage, setStage] = useState("source");
  const selected = PROGRAMME_READINESS.find((programme) => programme.id === selectedId) || PROGRAMME_READINESS[0];
````

New text:

````
function ProgrammesView({ programmes }) {
  // Every programme here is compiled from sources saved on this machine. The
  // panel previously rendered a hardcoded array while the server published this
  // exact list and nothing read it.
  const entries = programmes?.available ? programmes.programmes : [];
  const [selectedId, setSelectedId] = useState(null);
  const selected = entries.find((item) => item.id === selectedId) || entries[0] || null;
  const next = programmeNextStep(selected);

  if (!entries.length) {
    return (
      <div className="content-page programmes-page">
        <header className="page-heading"><div><span className="eyebrow">Research · Authority first</span><h1>Programme scope library</h1><p>Programmes compiled from sources saved on this machine.</p></div></header>
        <section className="surface"><p className="programme-empty">No programme is registered yet. A programme arrives by compiling a saved source bundle — nothing is fetched, and registering one grants no authority to test anything.</p></section>
      </div>
    );
  }

  return (
    <div className="content-page programmes-page">
      <header className="page-heading"><div><span className="eyebrow">Research · Authority first</span><h1>Programme scope library</h1><p>Compiled from sources saved on this machine. Registering a programme grants no authority to test it.</p></div><Pill tone="amber">{programmes.counts.registered} registered · {programmes.counts.needingAttention} need you</Pill></header>
      <div className="programme-layout">
        <main className="surface programme-list">
          <div className="section-heading"><div><span className="eyebrow">Your registry</span><h2>Registered programmes</h2></div></div>
          {entries.map((programme) => (
            <button key={programme.id} className={selected?.id === programme.id ? "is-selected" : ""} onClick={() => setSelectedId(programme.id)}>
              <Target />
              <div><small>version {programme.version}</small><strong>{programme.id}</strong><span>{programme.humanReviewed ? "reviewed by a person" : "no human review recorded"}</span></div>
              <Pill tone={programme.contractStatus === "blocked" ? "amber" : programme.humanReviewed ? "green" : "neutral"}>{programme.contractStatus}</Pill>
            </button>
          ))}
        </main>
        <aside className="surface programme-inspector">
          <span className="eyebrow">What to do next</span>
          <h2>{next.step}</h2>
          <p>{next.because}</p>
          <dl>
            <div><dt>Contract state</dt><dd>{selected.contractStatus}</dd></div>
            <div><dt>Human review</dt><dd>{selected.humanReviewed ? "recorded" : "none recorded"}</dd></div>
            <div><dt>Authority ceiling</dt><dd>{selected.maxAuthority || "not recorded"}</dd></div>
            <div><dt>Contract version</dt><dd>{selected.version}</dd></div>
          </dl>
          <div className="evidence-limit"><ShieldCheck /><p>This panel reads compiled contracts. It cannot contact, scan, or test any programme asset, and the authority ceiling above is the programme's own — not something this screen can raise.</p></div>
        </aside>
      </div>
    </div>
  );
}
````

## 55. 2026-09-15T18:07:25.494Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    programmes: <ProgrammesView />,
````

New text:

````
    programmes: <ProgrammesView programmes={registeredProgrammes} />,
````

## 56. 2026-09-15T18:07:34.077Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import ResearchWorkspacePanel from "./ResearchWorkspacePanel.jsx";
````

New text:

````
import ResearchWorkspacePanel from "./ResearchWorkspacePanel.jsx";
import { programmeNextStep } from "./programmeReadiness.js";
````

## 57. 2026-09-15T18:08:44.686Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const stages = [
    ["source", "Read source", selected.sourceState],
    ["review", "Review scope", selected.reviewState],
    ["case", "Derive local case", selected.caseState],
    ["live", "Raise posture", "Unavailable"],
  ];
  return (
    <div className="content-page programmes-page">
      <header className="page-heading"><div><span className="eyebrow">Research · Authority first</span><h1>Programme scope library</h1><p>Review versioned scope and policy sources before creating a hypothesis. Imported text cannot activate testing.</p></div><Pill tone="amber">3 offline bundles</Pill></header>
      <section className="surface programme-readiness" aria-labelledby="programme-readiness-title"><div><span className="eyebrow">Learning-to-research transition</span><h2 id="programme-readiness-title">From public policy to a safe local case</h2><p>Select each stage to see what can happen now. Nothing here grants target authority.</p></div><div className="programme-stages" role="group" aria-label="Programme readiness stages">{stages.map(([id, label, state], index) => <button type="button" key={id} className={stage === id ? "is-selected" : ""} onClick={() => setStage(id)} aria-pressed={stage === id}><span>{index + 1}</span><strong>{label}</strong><small>{state}</small></button>)}</div><div className="programme-stage-note" role="status"><ShieldCheck /><div><strong>{stage === "source" ? "Saved source, not live truth" : stage === "review" ? "A human resolves scope" : stage === "case" ? "Learning stays synthetic" : "Live access remains dark"}</strong><p>{stage === "source" ? "Inspect the versioned snapshot and record its date; refresh is a separate governed action." : stage === "review" ? "Confirm assets, exclusions, rates, data handling, and disclosure terms without guessing through conflicts." : stage === "case" ? selected.nextAction : "Ubuntu full-service and exact-egress namespace proofs plus the same-profile DPAPI candidate pass. Separate-account Windows acceptance, reproducible hardened-image binding, approved key recovery and ACLs, programme review, and explicit posture approval are still required."}</p></div></div></section>
      <div className="programme-layout"><main className="surface programme-list"><div className="section-heading"><div><span className="eyebrow">Available sources</span><h2>Programme bundles</h2></div></div>{PROGRAMME_READINESS.map((programme) => <button key={programme.id} className={selected.id === programme.id ? "is-selected" : ""} onClick={() => { setSelectedId(programme.id); setStage("source"); }}><Target /><div><small>{programme.platform}</small><strong>{programme.name}</strong><span>{programme.source}</span></div><Pill tone={programme.blocked ? "amber" : "green"}>{programme.reviewState}</Pill></button>)}</main><aside className="surface programme-inspector"><span className="eyebrow">Selected programme</span><h2>{selected.name}</h2><p>{selected.nextAction}</p><dl><div><dt>Platform</dt><dd>{selected.platform}</dd></div><div><dt>Source state</dt><dd>{selected.sourceState}</dd></div><div><dt>Review state</dt><dd>{selected.reviewState}</dd></div><div><dt>Local case</dt><dd>{selected.caseState}</dd></div><div><dt>Network access</dt><dd>Unavailable</dd></div></dl><div className="evidence-limit"><ShieldCheck /><p>This panel teaches programme analysis and can shape a synthetic case. It cannot contact, scan, or test any programme asset.</p></div></aside></div>
    </div>
  );
}

function HypothesesView({ navigate, activePack }) {
````

New text:

````
function HypothesesView({ navigate, activePack }) {
````

## 58. 2026-09-15T18:09:39.015Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import { CASE_PACKS, DEMO_RUNS, LIVE_PROGRAMME_GATES, PROGRAMME_READINESS, casePackById, casePackForCard, missionSegmentsForPack } from "./casePacks";
````

New text:

````
import { CASE_PACKS, DEMO_RUNS, LIVE_PROGRAMME_GATES, casePackById, casePackForCard, missionSegmentsForPack } from "./casePacks";
````

## 59. 2026-09-15T22:02:05.812Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import ResearchWorkspacePanel from "./ResearchWorkspacePanel.jsx";
````

New text:

````
import ResearchWorkspacePanel from "./ResearchWorkspacePanel.jsx";
import DirectoryPanel from "./DirectoryPanel.jsx";
````

## 60. 2026-09-15T22:02:07.284Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  programmesFromSnapshot,
  researchFromSnapshot,
````

New text:

````
  directoryFromSnapshot,
  programmesFromSnapshot,
  researchFromSnapshot,
````

## 61. 2026-09-15T22:02:09.919Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const registeredProgrammes = useMemo(() => programmesFromSnapshot(snapshot), [snapshot]);
````

New text:

````
  const registeredProgrammes = useMemo(() => programmesFromSnapshot(snapshot), [snapshot]);
  const directory = useMemo(() => directoryFromSnapshot(snapshot), [snapshot]);
````

## 62. 2026-09-15T22:02:12.990Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  async function shortlistProgramme(programmeId) {
````

New text:

````
  // The only action in this application that sends a request from this machine.
  // It is acknowledged explicitly for that reason, and it happens only when the
  // operator presses the button that says so.
  async function lookUpProgramme({ platform, handle }) {
    if (persistenceMode !== "interactive") {
      setNotice("Connect the local application before sending a request.");
      return;
    }
    try {
      const { result } = await dispatch(createWorkbenchCommand({
        kind: "look_up_programme",
        fields: { platform, handle },
        humanAcknowledged: true,
      }));
      setNotice(result?.message || `${platform}:${handle} was read.`);
    } catch (error) {
      setNotice(
        error instanceof Error ? error.message : `${platform}:${handle} could not be read.`,
      );
    }
  }

  async function shortlistProgramme(programmeId) {
````

## 63. 2026-09-15T22:02:14.588Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
onArchiveProgramme, onRestoreProgramme, research }) {
````

New text:

````
onArchiveProgramme, onRestoreProgramme, research, directory, onLookUp }) {
````

## 64. 2026-09-15T22:02:17.352Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <ShortlistPanel shortlist={shortlist} persistenceMode={persistenceMode} onArchive={onArchiveProgramme} onRestore={onRestoreProgramme} />
````

New text:

````
        <ShortlistPanel shortlist={shortlist} persistenceMode={persistenceMode} onArchive={onArchiveProgramme} onRestore={onRestoreProgramme} />
        {/* Which programmes, then how to add one; the workspace below answers
            "this programme". */}
        <DirectoryPanel directory={directory} persistenceMode={persistenceMode} onLookUp={onLookUp} />
````

## 65. 2026-09-15T22:02:18.895Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
onRestoreProgramme={restoreProgramme} research={research} openLesson=
````

New text:

````
onRestoreProgramme={restoreProgramme} research={research} directory={directory} onLookUp={lookUpProgramme} openLesson=
````

## 66. 2026-09-15T22:12:13.179Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <LearnerLoop current={0} onSelect={(step) => navigate(step === "learn" ? "learn" : step === "practise" ? "labs" : step === "prove" ? "evidence" : "reviews")} />
        {/* The working set first, then the one bounty you are focused on. */}
````

New text:

````
        <LearnerLoop current={0} onSelect={(step) => navigate(step === "learn" ? "learn" : step === "practise" ? "labs" : step === "prove" ? "evidence" : "reviews")} />
        {/* The bounties you actually have, on the page you open first. This is
            your registry, not a feed: nothing here was fetched, and nothing
            appears that you did not compile from saved sources. */}
        <ProgrammeRoster programmes={programmes} navigate={navigate} />
        {/* The working set first, then the one bounty you are focused on. */}
````

## 67. 2026-09-15T22:12:45.789Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import DirectoryPanel from "./DirectoryPanel.jsx";
````

New text:

````
import DirectoryPanel from "./DirectoryPanel.jsx";
import ProgrammeRoster from "./ProgrammeRoster.jsx";
````

## 68. 2026-09-15T22:12:47.146Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
research, directory, onLookUp }) {
````

New text:

````
research, directory, onLookUp, programmes }) {
````

## 69. 2026-09-15T22:12:48.892Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
research={research} directory={directory} onLookUp={lookUpProgramme} openLesson=
````

New text:

````
research={research} directory={directory} onLookUp={lookUpProgramme} programmes={registeredProgrammes} openLesson=
````

## 70. 2026-09-15T22:28:15.006Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import ProgrammeRoster from "./ProgrammeRoster.jsx";
````

New text:

````
import ProgrammeRoster from "./ProgrammeRoster.jsx";
import BountyBoard from "./BountyBoard.jsx";
````

## 71. 2026-09-15T22:28:17.714Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <ProgrammeRoster programmes={programmes} navigate={navigate} />
````

New text:

````
        {/* Real programmes you could work on, then the ones you already have.
            Suggestions first, because this is the question you arrive with. */}
        <BountyBoard directory={directory} persistenceMode={persistenceMode} onLookUp={onLookUp} registered={programmes} />
        <ProgrammeRoster programmes={programmes} navigate={navigate} />
````

## 72. 2026-09-15T22:33:28.968Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  // The only action in this application that sends a request from this machine.
````

New text:

````
  // Automatic refresh is off until asked for, and the preference is browser
  // local: it changes what this tab does, never what is recorded.
  const [autoRefresh, setAutoRefresh] = useState(() => {
    try {
      return window.localStorage?.getItem("greytheory.autoRefresh") === "on";
    } catch { return false; }
  });
  const toggleAutoRefresh = useCallback((next) => {
    setAutoRefresh(Boolean(next));
    try {
      window.localStorage?.setItem("greytheory.autoRefresh", next ? "on" : "off");
    } catch { /* storage optional */ }
  }, []);

  // The only action in this application that sends a request from this machine.
````

## 73. 2026-09-15T22:33:32.979Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  async function shortlistProgramme(programmeId) {
````

New text:

````
  // Sequential with a gap, never Promise.all. Six simultaneous requests to a
  // bug bounty platform is the traffic pattern that gets a researcher's access
  // restricted; one every few seconds is a person reading pages.
  async function refreshAllProgrammes(plan) {
    if (persistenceMode !== "interactive" || !plan?.targets?.length) return;
    setNotice(`Refreshing ${plan.requests} programme${plan.requests === 1 ? "" : "s"}, one at a time.`);
    for (const [index, row] of plan.targets.entries()) {
      if (index > 0) {
        await new Promise((resolve) => setTimeout(resolve, plan.spacingMs));
      }
      await lookUpProgramme({ platform: row.platform, handle: row.handle });
    }
  }

  async function shortlistProgramme(programmeId) {
````

## 74. 2026-09-15T22:33:36.976Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  const views = {
````

New text:

````
  // One overdue programme per tick, and only while the tab is actually being
  // looked at: a window left open overnight must not sit there issuing
  // requests nobody is reading. The clamp inside nextDue means a short tick
  // cannot produce a short interval.
  useEffect(() => {
    if (!autoRefresh || persistenceMode !== "interactive") return undefined;
    const timer = setInterval(() => {
      if (document.hidden) return;
      const due = nextDue(boardRows(directory?.lookups || []), Date.now(), DEFAULT_INTERVAL_MS);
      if (due) lookUpProgramme({ platform: due.platform, handle: due.handle });
    }, 60000);
    return () => clearInterval(timer);
  }, [autoRefresh, persistenceMode, directory]);

  const views = {
````

## 75. 2026-09-15T22:33:38.860Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import BountyBoard from "./BountyBoard.jsx";
````

New text:

````
import BountyBoard from "./BountyBoard.jsx";
import { boardRows } from "./knownProgrammes.js";
import { DEFAULT_INTERVAL_MS, nextDue } from "./refreshPolicy.js";
````

## 76. 2026-09-15T22:33:40.979Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
        <BountyBoard directory={directory} persistenceMode={persistenceMode} onLookUp={onLookUp} registered={programmes} />
````

New text:

````
        <BountyBoard directory={directory} persistenceMode={persistenceMode} onLookUp={onLookUp} registered={programmes} onRefreshAll={onRefreshAll} autoRefresh={autoRefresh} onToggleAutoRefresh={onToggleAutoRefresh} />
````

## 77. 2026-09-15T22:33:42.513Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
research, directory, onLookUp, programmes }) {
````

New text:

````
research, directory, onLookUp, programmes, onRefreshAll, autoRefresh, onToggleAutoRefresh }) {
````

## 78. 2026-09-15T22:33:44.481Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
onLookUp={lookUpProgramme} programmes={registeredProgrammes} openLesson=
````

New text:

````
onLookUp={lookUpProgramme} programmes={registeredProgrammes} onRefreshAll={refreshAllProgrammes} autoRefresh={autoRefresh} onToggleAutoRefresh={toggleAutoRefresh} openLesson=
````

## 79. 2026-09-15T22:34:18.347Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  useEffect(() => {
    if (!autoRefresh || persistenceMode !== "interactive") return undefined;
    const timer = setInterval(() => {
      if (document.hidden) return;
      const due = nextDue(boardRows(directory?.lookups || []), Date.now(), DEFAULT_INTERVAL_MS);
      if (due) lookUpProgramme({ platform: due.platform, handle: due.handle });
    }, 60000);
    return () => clearInterval(timer);
  }, [autoRefresh, persistenceMode, directory]);
````

New text:

````
  // Read through a ref rather than closing over `directory`: that value changes
  // on every snapshot, and depending on it would tear down and recreate the
  // interval after each completed lookup, restarting the tick every time.
  const lookupsRef = useRef([]);
  lookupsRef.current = directory?.lookups || [];

  useEffect(() => {
    if (!autoRefresh || persistenceMode !== "interactive") return undefined;
    const timer = setInterval(() => {
      // A window left open overnight must not sit there issuing requests
      // nobody is reading.
      if (document.hidden) return;
      const due = nextDue(boardRows(lookupsRef.current), Date.now(), DEFAULT_INTERVAL_MS);
      if (due) lookUpProgramme({ platform: due.platform, handle: due.handle });
    }, 60000);
    return () => clearInterval(timer);
  }, [autoRefresh, persistenceMode]);
````

## 80. 2026-09-16T06:12:27.847Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import BountyBoard from "./BountyBoard.jsx";
import { boardRows } from "./knownProgrammes.js";
````

New text:

````
import BountyBoard from "./BountyBoard.jsx";
import CurriculumView from "./CurriculumView.jsx";
import { readProgress, writeProgress } from "./curriculumPath.js";
import { boardRows } from "./knownProgrammes.js";
````

## 81. 2026-09-16T06:12:31.791Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  // Automatic refresh is off until asked for, and the preference is browser
  // local: it changes what this tab does, never what is recorded.
````

New text:

````
  // Which lessons have been worked through in this browser. A practice record,
  // never a claim about skill: mastery stays six separately assessed
  // dimensions recorded by a person, and nothing here touches it.
  const [completedLessons, setCompletedLessons] = useState(() => readProgress());
  const markLessonComplete = useCallback((lessonId) => {
    if (!lessonId) return;
    setCompletedLessons((current) => {
      if (current.includes(lessonId)) return current;
      return writeProgress([...current, lessonId]);
    });
  }, []);

  // Automatic refresh is off until asked for, and the preference is browser
  // local: it changes what this tab does, never what is recorded.
````

## 82. 2026-09-16T06:12:33.322Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    learn: <LearnView openLab={openLab} journey={journey} activePack={activePack} />,
````

New text:

````
    learn: <CurriculumView completed={completedLessons} onOpenLesson={openLesson} />,
````

## 83. 2026-09-16T06:12:35.296Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
onSolved={(lesson) => persistRotation(clearTopic(rotation, selectedPackId, {}))} /></Modal>}
````

New text:

````
onSolved={(lesson) => { markLessonComplete(lesson?.id); persistRotation(clearTopic(rotation, selectedPackId, {})); }} /></Modal>}
````

## 84. 2026-09-16T10:47:38.217Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import CurriculumView from "./CurriculumView.jsx";
````

New text:

````
import CurriculumView from "./CurriculumView.jsx";
import OnboardingOverlay from "./OnboardingOverlay.jsx";
import { readCollapsed, writeCollapsed } from "./onboarding.js";
````

## 85. 2026-09-16T10:47:41.609Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  // Which lessons have been worked through in this browser. A practice record,
````

New text:

````
  // Only whether the guide is collapsed is remembered. Its progress is never
  // stored: it is recomputed from what actually happened, so it cannot drift
  // out of step with reality or be clicked past.
  const [guideCollapsed, setGuideCollapsed] = useState(() => readCollapsed());
  const toggleGuideCollapsed = useCallback((next) => {
    setGuideCollapsed(Boolean(next));
    writeCollapsed(Boolean(next));
  }, []);

  // Which lessons have been worked through in this browser. A practice record,
````

## 86. 2026-09-16T10:47:45.534Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
      <main ref={workspaceRef} id="workspace-main" className="workspace" tabIndex="-1" aria-label={currentNav.label}>{view}</main>
      <FooterBoundary />
````

New text:

````
      <main ref={workspaceRef} id="workspace-main" className="workspace" tabIndex="-1" aria-label={currentNav.label}>{view}</main>
      {/* Above every panel on every view: the steps span the whole product, so
          anchoring the guide to one page would lose your place the moment you
          went to do what a step told you to. */}
      <OnboardingOverlay
        connected={persistenceMode === "interactive"}
        programmes={registeredProgrammes}
        completedLessons={completedLessons}
        shortlist={shortlist}
        directory={directory}
        collapsed={guideCollapsed}
        onToggleCollapsed={toggleGuideCollapsed}
        onConnect={() => setModal("connection")}
        navigate={navigate}
      />
      <FooterBoundary />
````

## 87. 2026-09-16T10:48:14.326Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
function LearnView({ openLab, journey, activePack }) {
  const [topic, setTopic] = useState(() => activePack.topicId);
  const [lessonIndex, setLessonIndex] = useState(0);
  const [checked, setChecked] = useState([false, false, false, false]);
  const [answers, setAnswers] = useState({});
  const [missionSegment, setMissionSegment] = useState("learn");
  const selected = topicById(topic);
  const missionSegments = missionSegmentsForPack(activePack);
  const activeSegment = missionSegments.find((segment) => segment.id === missionSegment) || missionSegments[0];
  const correctAnswers = selected.practiceChecks.filter((item, index) => answers[index] === item.answer).length;
  const conceptChecks = checked.filter(Boolean).length;
  const labReady = conceptChecks >= 3 && correctAnswers === selected.practiceChecks.length;
  useEffect(() => {
    setTopic(activePack.topicId);
    setLessonIndex(0);
    setChecked([false, false, false, false]);
    setAnswers({});
    setMissionSegment("learn");
  }, [activePack.id, activePack.topicId]);
  const selectTopic = (id) => {
    if (id === topic) return;
    setTopic(id);
    setLessonIndex(0);
    setChecked([false, false, false, false]);
    setAnswers({});
  };
  const toggle = (index) => setChecked((items) => items.map((value, itemIndex) => itemIndex === index ? !value : value));
  return (
    <div className="content-page learn-page">
      <header className="page-heading"><div><span className="eyebrow">Learn · Case Pack {activePack.number}</span><h1>{activePack.title}</h1><p>{activePack.learnCopy}</p>{journey && <div className="tag-row"><Pill tone="violet">Assigned step: {journey.title}</Pill><Pill>{journey.dimension}</Pill></div>}</div><div className="time-chip"><BookOpen />{activePack.duration} guided mission</div></header>
      <section className="surface mission-plan" aria-labelledby="mission-plan-title">
        <div className="mission-plan__heading"><div><span className="eyebrow">Your route today</span><h2 id="mission-plan-title">One complete research-learning loop</h2></div><Pill tone="green">{activePack.estimatedMinutes} minutes total</Pill></div>
        <div className="mission-segments" role="group" aria-label="Mission stages">{missionSegments.map((segment, index) => <button type="button" key={segment.id} className={segment.id === missionSegment ? "is-selected" : ""} onClick={() => setMissionSegment(segment.id)} aria-pressed={segment.id === missionSegment}><span>{String(index + 1).padStart(2, "0")}</span><strong>{segment.label}</strong><small>{segment.minutes} min</small></button>)}</div>
        <div className="mission-segment-detail" aria-live="polite"><div><span className="eyebrow">Outcome</span><strong>{activeSegment.outcome}</strong></div><div><span className="eyebrow">Produce</span><p>{activeSegment.deliverable}</p></div><div><span className="eyebrow">Safety boundary</span><p>{activeSegment.boundary}</p></div></div>
      </section>
      <div className="topic-grid">
        {LEARNING_TOPICS.map(({ id, title, copy, duration, level }) => { const Icon = TOPIC_ICONS[id] || BookOpen; return <button key={id} className={`topic-card ${topic === id ? "is-selected" : ""}`} onClick={() => selectTopic(id)} onMouseEnter={() => selectTopic(id)} onFocus={() => selectTopic(id)} aria-pressed={topic === id}><div><Icon /><Pill tone={topic === id ? "amber" : "neutral"}>{topic === id ? "Current topic" : level}</Pill></div><strong>{title}</strong><p>{copy}</p><span>{duration} · {level}</span></button>; })}
      </div>
      <div className="learning-layout">
        <main>
          <section className="surface lesson-card">
            <div className="section-heading"><div><span className="eyebrow">Focused note</span><h2>{selected.title}</h2></div><Pill tone="green">Ethical + technical</Pill></div>
            <p className="lesson-lede">{selected.lede}</p>
            <div className="principle-grid">
              {selected.principles.map(([title, copy], index) => { const Icon = PRINCIPLE_ICONS[index]; return <article key={title}><Icon /><strong>{title}</strong><p>{copy}</p></article>; })}
            </div>
            <div className="lens-compare">
              <article><span className="eyebrow">Traditional lens</span><h3>{selected.traditional[0]}</h3><p>{selected.traditional[1]}</p><Pill>{selected.traditional[2]}</Pill></article>
              <article><span className="eyebrow">AI lens</span><h3>{selected.ai[0]}</h3><p>{selected.ai[1]}</p><Pill tone="blue">{selected.ai[2]}</Pill></article>
            </div>
          </section>
          <section className="surface topic-roadmap">
            <div className="section-heading"><div><span className="eyebrow">Lesson roadmap</span><h2>From first look to independent transfer</h2></div><Pill tone="blue">{lessonIndex + 1} of {selected.lessons.length}</Pill></div>
            <ol>{selected.lessons.map(([number, title, level, objective], index) => <li key={title} className={index < lessonIndex ? "is-visited" : index === lessonIndex ? "is-current" : ""}><button onClick={() => setLessonIndex(index)} aria-current={index === lessonIndex ? "step" : undefined}><span>{index < lessonIndex ? <Check /> : number}</span><div><small>{level}</small><strong>{title}</strong><p>{objective}</p></div></button></li>)}</ol>
            <div className="lesson-media"><div><span className="eyebrow">Official learning material</span><p>Open trusted sources alongside the local lesson. External pages remain reading material and never gain authority over this workbench.</p></div>{selected.resources.map(([source, title, href]) => <a key={href} href={href} target="_blank" rel="noreferrer"><BookOpen /><span><small>{source}</small><strong>{title}</strong></span><ArrowRight /></a>)}</div>
          </section>
        </main>
        <aside className="surface lesson-checklist">
          <span className="eyebrow">Practice check</span><h2>Reason before the lab</h2><p>Answer both scenarios, then confirm what you can explain in your own words.</p>
          <div className="practice-checks">{selected.practiceChecks.map((item, checkIndex) => <fieldset key={item.question}><legend>{checkIndex + 1}. {item.question}</legend>{item.options.map((option, optionIndex) => <label key={option}><input type="radio" name={`${selected.id}-check-${checkIndex}`} checked={answers[checkIndex] === optionIndex} onChange={() => setAnswers((current) => ({ ...current, [checkIndex]: optionIndex }))} /><span>{option}</span></label>)}{answers[checkIndex] !== undefined && <div className={`practice-feedback ${answers[checkIndex] === item.answer ? "is-correct" : "is-wrong"}`} role="status"><strong>{answers[checkIndex] === item.answer ? "Good reasoning" : "Try that boundary again"}</strong><p>{answers[checkIndex] === item.answer ? item.explanation : "Re-read the focused note and choose the answer that preserves explicit authority and the smallest safe scope."}</p></div>}</fieldset>)}</div>
          <div className="self-check-heading"><span className="eyebrow">Explain it yourself</span><Pill tone={conceptChecks >= 3 ? "green" : "neutral"}>{conceptChecks}/4</Pill></div>
          {selected.checkpoints.map((label, index) => <label key={label}><input type="checkbox" checked={checked[index]} onChange={() => toggle(index)} /><span><i><Check /></i>{label}</span></label>)}
          <Progress value={Math.round(((conceptChecks + correctAnswers) / 6) * 100)} label="Practice readiness" />
          <button className="button button--primary button--full" onClick={openLab} disabled={!labReady}>Open the safe lab <ArrowRight /></button>
          <small>Answer both practice checks correctly and confirm at least three explanations. This unlocks practice only; it does not award mastery.</small>
        </aside>
      </div>
    </div>
  );
}
````

New text:

````
// LearnView was removed here. It rendered a parallel, much thinner data set -
// a lede, four principle cards, a roadmap of titles with nothing behind them -
// and then asked two scenario questions and four "confirm you can explain this"
// boxes. Questions before material is interrogation, not teaching, and its
// wrong-answer feedback was one generic sentence for every question on every
// topic. The 28 written lessons it should have been using now drive
// CurriculumView, which reads before it tests and gives a specific hint per
// wrong answer.
````

## 88. 2026-09-16T10:50:29.879Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
          <button className="metric-card" onClick={() => navigate("evidence")}><Receipt /><span>Evidence receipts</span><strong>7</strong><small>3 verified this week</small></button>
          <button className="metric-card" onClick={() => navigate("reviews")}><GraduationCap /><span>Reviews</span><strong>2</strong><small>Awaiting your response</small></button>
          <div className="metric-card"><ShieldCheck /><span>Authority violations</span><strong>0</strong><small>All sessions within policy</small></div>
          <div className="metric-card"><TrendUp /><span>Learning rhythm</span><strong>5 days</strong><small>Best streak: 5 days</small></div>
````

New text:

````
          {/* Every figure here is counted from something on this machine. These
              were four hardcoded literals - "7 receipts", "2 reviews", "0
              authority violations", "5 day streak" - on a dashboard whose whole
              argument is that claims must be sourced. Nothing is shown now that
              cannot answer where it came from, and "authority violations" is
              gone entirely because nothing counts them. */}
          <button className="metric-card" onClick={() => navigate("evidence")}><Receipt /><span>Evidence receipts</span><strong>{evidencedCards.size}</strong><small>cards with a server-issued fixture receipt</small></button>
          <button className="metric-card" onClick={() => navigate("programmes")}><GraduationCap /><span>Programmes needing you</span><strong>{programmes?.counts?.needingAttention ?? 0}</strong><small>of {programmes?.counts?.registered ?? 0} compiled locally</small></button>
          <button className="metric-card" onClick={() => navigate("mission")}><Target /><span>On your shortlist</span><strong>{shortlist?.counts?.active ?? 0}</strong><small>{shortlist?.counts?.archived ?? 0} set aside</small></button>
          <button className="metric-card" onClick={() => navigate("mission")}><MagnifyingGlass /><span>Pages checked</span><strong>{directory?.counts?.read ?? 0}</strong><small>public programme pages retrieved</small></button>
````

## 89. 2026-09-16T10:50:33.250Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
const TOPIC_ICONS = {
  "prompt-boundaries": ShieldCheck,
  "tool-authorization": LockKey,
  "object-authorization": Target,
  "session-role-transitions": UserCircle,
  "mcp-abuse": Warning,
};

const CASE_PACK_ICONS = {
````

New text:

````
const CASE_PACK_ICONS = {
````

## 90. 2026-09-16T10:50:33.386Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
const PRINCIPLE_ICONS = [Scales, UserCircle, ShieldCheck, Receipt];

function simulationPresentation(result) {
````

New text:

````
function simulationPresentation(result) {
````

## 91. 2026-09-16T10:51:11.706Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
    learn: <CurriculumView completed={completedLessons} onOpenLesson={openLesson} />,
````

New text:

````
    learn: <CurriculumView completed={completedLessons} onOpenLesson={openLesson} onOpenLab={openLab} />,
````

## 92. 2026-09-16T10:51:39.686Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import { LEARNING_TOPICS, SKILL_TRACKS, topicById } from "./learningPaths";
````

New text:

````
import { SKILL_TRACKS, topicById } from "./learningPaths";
````

## 93. 2026-09-16T10:53:30.404Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
import { announceHintPreference, readHintPreference, writeHintPreference } from "./helpPreference.js";
````

New text:

````
import { announceHintPreference, readHintPreference, writeHintPreference } from "./helpPreference.js";
// Cross-cutting by nature, so it lives in one file rather than being sprinkled
// through component stylesheets. Everything in it is gated behind
// prefers-reduced-motion: no-preference.
import "./motion.css";
````
