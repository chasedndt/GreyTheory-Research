# AI-Native Learning Workbench

> **Status:** SELECTED INTERACTIVE PREVIEW; responsive learner journey verified locally; installed acceptance open
>
> **Current posture:** `LOCAL_FIXTURE`; no live targets; AI advisory only
>
> **Primary user:** a new security researcher learning web, API, bug-bounty,
> evidence, and agentic-system security through controlled local practice

This document defines the learner-facing product foundation for GreyTheory. It
does not widen authority. On 2026-09-01 the operator selected Guided Mission
Control as the shell and the first interactive implementation was verified
locally. The earlier thirteen-panel Research Ledger remains a useful case view,
while the new shell provides the complete guided local learner journey.

## Product objective

GreyTheory should help a learner answer five questions at every moment:

1. What is the most valuable safe thing to learn or practise next?
2. Why is it recommended for me now?
3. What authority and environment govern the work?
4. What evidence would support or refute the theory?
5. What changed in my demonstrated capability after review?

The dashboard is therefore not a generic analytics surface. It is the visible
orchestrator for a bounded learning-to-proof loop.

```mermaid
flowchart LR
    TODAY["Today: one next safe mission"] --> LEARN["Learn: concept and boundaries"]
    LEARN --> PRACTISE["Practise: synthetic local fixture"]
    PRACTISE --> PROVE["Prove: evidence and receipt"]
    PROVE --> REFLECT["Reflect: limits and lesson"]
    REFLECT --> ASSESS["Assess: explicit human judgement"]
    ASSESS --> TRANSFER["Transfer: distinct local context"]
    TRANSFER --> TODAY

    AUTH["Authority envelope\nLOCAL_FIXTURE · no live targets"] --> TODAY
    AUTH --> PRACTISE
    AUTH --> PROVE
    COACH["AI coach\nexplain · question · critique"] -. advisory .-> LEARN
    COACH -. advisory .-> REFLECT
    COACH -. "cannot execute or award mastery" .-> ASSESS
```

## Information architecture

The primary navigation should follow the operator's mental model rather than
the storage model.

| Area | Operator question | Required surfaces |
|---|---|---|
| Today | What should I do next? | next safe mission, why now, time, prerequisites, due reviews |
| Learn | What do I need to understand? | curriculum, focused note, skill graph, vocabulary, controls |
| Practise | Can I apply it safely? | local labs, challenges, controls, reset, fixture provenance |
| Research | What may be true? | hypotheses, experiment plans, case canvas, ledger |
| Prove | What does the evidence support? | receipts, claim roles, validation, assessment, reviews |
| Library | What can I reuse? | cards, notes, playbooks, templates, artifacts |
| Readiness | What is safe and available? | posture, authority, storage, integrations, capability truth |

The chronological Research Ledger remains a first-class case view under
Research. It is not the home screen.

## Recommendation contract

A recommendation is inspectable decision support, not a model hunch. Every
recommended topic or mission must show:

- the card and exact mastery dimension;
- prerequisite state and any missing prerequisite;
- due-review or operator-goal reason;
- estimated time and local fixture;
- required evidence and assessment type;
- why this item outranks the next alternative; and
- provenance for every input used by the scheduler.

Recommendations may use the existing deterministic planner and transparent
adaptive review policy. A model may explain the recommendation in plain
language, but it may not secretly reorder the queue, invent mastery, award a
level, or convert an ordinal score into probability.

## Agent-security learning track

Agentic-system security is a first-class specialization built on web/API and
evidence foundations, not a detached list of prompt tricks.

| Stage | Topics | Minimum learning outcome |
|---|---|---|
| Foundations | instructions versus data, trust labels, identity, scope, least privilege | explain the boundary and identify the authority source |
| Input and context | direct and indirect prompt injection, context isolation, memory poisoning | recognise untrusted influence and propose controls |
| Tools and agency | tool authorization, MCP tool abuse, excessive agency, side-effect budgets | design a least-authority tool policy and a negative control |
| Data protection | secret leakage, cross-user context, exfiltration paths | trace data flow and prove isolation with synthetic identities |
| Evidence | transcript provenance, deterministic checks, variance, reproducibility | distinguish anomalous output from checked evidence |
| Transfer | a distinct local agent fixture and threat model | apply the method without hidden assistance |

The UI should always separate observation, candidate explanation, checked
evidence, and human judgement. None of those labels is a probability.

## Visualisation system

Visualisations must answer a learner question and expose their source. The
first implementation set is:

1. **Learner loop** — current stage, evidence requirement, and next transition.
2. **Skill trajectory** — prerequisites and six mastery dimensions without a
   misleading single percentage.
3. **Case canvas** — Authority -> Theory -> Safe experiment -> Receipt ->
   Reflection, with visible return paths when evidence changes the theory.
4. **Evidence-quality profile** — authority anchoring, relevance,
   reproducibility, minimal impact, and documentation, each linked to the
   supporting record.
5. **Review schedule** — due and upcoming human-assessment work.
6. **Activity heatmap** — time spent on active learning, including sessions that
   produced no finding.

Charts must render `UNKNOWN` as unknown, not zero. They must support keyboard
inspection, provide a text/table equivalent, and remain legible without colour.

## AI coach boundary

The coach can explain concepts, ask Socratic questions, suggest a falsifiable
theory or negative control, critique plans/evidence/reflections/drafts, and
translate deterministic scheduler reasons into beginner-friendly language.

The coach cannot contact a target, run a tool, approve an action, change
posture, submit, decide that scope exists, mark evidence as checked, award
mastery, complete an assessment, hide criteria, or read data above its provider
ceiling.

## Visual direction gate

The 2026-09-01 audit produced three grounded directions in the editable
[GreyTheory AI-Native Research Workbench Figma file](https://www.figma.com/design/1Agfk1l6iKvmNf8agWCqpB):

1. **Guided Mission Control** — recommended foundation; best daily orientation.
2. **Research Notebook + Skill Graph** — strongest focused-learning workspace.
3. **Adaptive Pathways + Case Canvas** — strongest visual systems model and the
   most expensive to implement and validate.

The selected composition is Direction 1 as the shell, Direction 2's focused
learning note and skill map as the Learn detail, and Direction 3's case canvas,
evidence-quality, and competency views as the Research/Prove detail.

## Responsive and accessibility acceptance

The redesigned shell is not accepted until all of the following pass:

- no horizontal document overflow at 390, 768, 1024, and 1440 pixels;
- headings, actions, filters, graphs, and evidence records remain fully visible;
- primary touch targets are at least 44 by 44 pixels;
- one-column mobile order preserves next action -> reason -> learner loop -> supporting detail;
- desktop side rails become labelled drawers or bottom sheets on small screens;
- all navigation, dialogs, graphs, and assessment forms work from the keyboard;
- focus is visible and returns to the invoking control;
- graph meaning has a text/table equivalent; and
- screenshots are compared at matching viewport and state before acceptance.

## Delivery sequence

| Stage | Outcome | Current truth |
|---|---|---|
| D0 Audit | current desktop/mobile evidence and failure list | COMPLETE 2026-09-01 |
| D1 Direction | three grounded visual options and editable Figma board | COMPLETE 2026-09-01 |
| D2 Selection | operator chooses the shell and permitted borrowings | COMPLETE 2026-09-01 |
| D3 Foundations | tokens, typography, shell, responsive grid, navigation | COMPLETE IN PREVIEW 2026-09-01 |
| D4 Today/Learn | recommendation, exact 30-minute learner loop, scenario checks, focused lesson, skill graph | SAME-ORIGIN PERSISTENCE IMPLEMENTED 2026-09-02 |
| D5 Practise/Research/Prove | fixture command, immutable receipt, case canvas, ledger, evidence | SAME-ORIGIN PERSISTENCE IMPLEMENTED 2026-09-02 |
| D5a Case Packs/Demos | two ready local packs, one queued pack, guided/full/transfer demo suite | IMPLEMENTED; PACK 02 PROMOTED 2026-09-04 |
| D6 AI coach | advisory-only presentation complete; governed model conversation | PARTIAL |
| D7 Acceptance | visual/reload/route-focus pass; mobile drawer and modal keyboard boundaries pass; bundled wheel plus current-user shortcut/restart/upgrade/runtime recovery pass; whole-app first-entry traversal, genuinely separate-account run, signing, and uninstall remain | PARTIAL |

The D4 learner surface now makes all 24 visible trajectory lessons selectable.
Completed, current, previewed, and future states remain semantically separate;
selecting a later node reveals the path but cannot award progress. The three
current agent-security topics each own distinct instructional content,
checkpoints, lenses, official resources, and a four-lesson progression from
beginner orientation to independent transfer.

The Agent Tool Authorization mission budgets Learn 8, Practise 10, Prove 5,
Reflect 4, and Assess 3 minutes. API Object Ownership budgets Learn 12,
Practise 18, Prove 8, Reflect 6, and Assess 6 minutes. Each current topic adds
two scored scenarios to the learner's own explanation checklist. Both
scenarios and three explanations are required to open the lab, but neither the
unlock nor mission completion grants mastery.

## Public intelligence and programme connectors

The workbench now exposes a read-only Intelligence journey for OSV, CISA KEV,
FIRST EPSS, NVD, and GitHub Advisories. `greytheory_intelligence` validates CVE
or versioned-package request plans, rejects target-shaped inputs, and contains
no network client. This is integration architecture, not a live connection.

HackerOne and Bugcrowd remain account connectors. Their official APIs require
account credentials and permissions, so the preview shows their requirements
without accepting tokens or making requests. A future local worker must keep
credentials outside the browser, import only authorised account data, preserve
source/retrieval evidence, and remain separate from target testing.

The Programmes view uses the already saved source bundles to teach a four-step
transition: read the dated source, resolve scope through human review, derive a
synthetic local case, and only later consider a posture decision. The fourth
step remains unavailable, YNAB ambiguity remains blocked, and the view performs
no refresh, account access, programme contact, or target request.

## Implemented reference case

`CASE-AGENT-AUTH-001` teaches the Agent Tool Authorization Boundary through
paired local controls:

- a direct, currently consented request to write an approved local note is
  allowed by the deterministic fixture policy;
- the same available tool cannot be invoked by instructions embedded in an
  untrusted document;
- both decisions declare `externalAction: false` and the negative control is
  denied before the tool adapter;
- the learner must inspect the evidence, write a limitations-aware reflection,
  and complete an independent readiness question; and
- completion remains practice evidence rather than automatic mastery.

`CASE-API-OWNERSHIP-001` now teaches object-level authorization through three
synthetic local controls:

- Account A reads its own object as the positive control;
- the same actor reaches Account B's synthetic object only when the ownership
  check is deliberately removed for the teaching failure;
- restoring server-side ownership policy denies the identical cross-owner
  request;
- the receipt preserves actor, owner, object, action, policy mode, result, and
  limitations while every result declares `externalAction: false`; and
- identifier predictability, a synthetic teaching failure, live impact,
  programme scope, and disclosure authority remain separate claims.

## Industry-practice grounding

The implementation borrows durable learning patterns without copying another
product's visual design:

- [PortSwigger Web Security Academy](https://portswigger.net/web-security/getting-started)
  grounds the read, practise, and progress-tracking loop; its
  [essential-skills guidance](https://portswigger.net/web-security/essential-skills)
  also reinforces that one lab is one variation and skill requires transfer.
- [Hack The Box Academy paths](https://academy.hackthebox.com/catalogue/paths)
  support ordered paths that join theory, practical work, methodology, and
  reporting rather than presenting an undifferentiated topic library.
- The [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/download/52117/)
  informs the agent-security track, including prompt injection, excessive
  agency, tool misuse, identity/privilege, and memory/context risks.
- [HackerOne scope and rewards guidance](https://docs.hackerone.com/en/articles/14432111-unified-scope-rewards-setup)
  supports making scope groups, exclusions, warnings, and changes visible
  before authorised testing begins.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and its
  [focus-order guidance](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html)
  define the keyboard, focus, and target-size acceptance basis.

These references shape the learning and safety contracts; they do not imply
endorsement, equivalence, or competitive feature parity.

## Launch and transition

The passive lab research pilot launches first on the operator's **Windows
workstation**: packaged workbench, local application service, offline core,
private user-data root, and controlled local fixtures. Ubuntu is the later
isolated worker host, not the first desktop UI.

The first worker step is a local Ubuntu 24.04 VM for acceptance. A VPS becomes
reasonable only after the same worker image, durable egress controls, OS-bound
key handling, broker/receipt path, sustained clean operation, and explicit
human posture approval have passed. The workbench remains on Windows while the
worker receives one short-lived ticket and returns one receipt and encrypted
capture.

The exact compatibility fields, all-or-nothing five-gate decision, and the
signal for considering transition are defined in
[`live-programme-transition.md`](live-programme-transition.md).

```mermaid
flowchart LR
    WIN["Windows operator workstation\nWorkbench + local service + offline core"]
    FIX["Controlled local fixtures\nLOCAL_FIXTURE"]
    VM["Ubuntu 24.04 local VM\nacceptance only"]
    VPS["Ubuntu VPS\nscheduled passive availability"]
    LIVE["PASSIVE_HTTP\none ticket · one target · one receipt"]

    WIN --> FIX
    FIX -->|"learner pilot accepted"| VM
    VM -->|"host, egress, key and receipt gates pass"| VPS
    VPS -->|"explicit posture approval"| LIVE
    LIVE -. "receipt + encrypted capture" .-> WIN

    style FIX fill:#065f46,stroke:#10b981,color:#fff
    style VM fill:#1e3a8a,stroke:#60a5fa,color:#fff
    style VPS fill:#78350f,stroke:#f59e0b,color:#fff
    style LIVE fill:#7f1d1d,stroke:#ef4444,color:#fff
```
