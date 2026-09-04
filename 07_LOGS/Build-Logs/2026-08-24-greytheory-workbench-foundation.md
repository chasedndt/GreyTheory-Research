# GreyTheory workbench foundation - 2026-08-24

## Repository truth

- Base: `bd1e12f3b38e8405637fab1ec1eaee9662afc8f2`.
- Isolated worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- Source security-hardening worktree remained clean and untouched.
- The dirty canonical ChaseOS vault was inspected only through bounded reads and
  Agent Bus readiness; no canonical vault file was changed.

## Repo-truth delta

Before this pass the dashboard still reported that no Signal Plane lane,
learning graph, or Scope Watch implementation existed. The repository already
contained three static offline lanes, the learning core, governed offline model
gateway, and offline Scope Watch. `PROJECT_STATE.md` and the top README register
also still described Milestone 7 as current.

The static dashboard itself was real and responsive, but it remained a
read-only export with no navigation, session interaction, learning journey,
evidence drill-down, or application command boundary.

## Change

- Added `greytheory.capabilities`, the executable status register shared by the
  dashboard and future workbench.
- Corrected dashboard capability truth while preserving the rule that missing
  runtime data is `UNKNOWN`, never a reassuring zero.
- Added focused register and dashboard tests.
- Added deterministic guided/review planning, prerequisite routing, explicit review intervals, and an ordered Learn/Practise/Prove/Reflect/Assess state machine.
- Added integrity-checked private journey persistence, optimistic revisions, abandonment, and CLI plan/start/status/advance/abandon operation. Completing a journey requires an already persisted matching human assessment and awards no mastery itself.
- Accepted ADR-0010: the workbench is a separate local application boundary and
  cannot execute collectors or workers directly.
- Defined Windows-first local launch, private data roots, primary journeys,
  learning orchestration, typed command/read contracts, UX truth rules, and the
  future isolated Ubuntu 24.04 passive-worker boundary.
- Reconciled README, canonical project definition/state, roadmap, ADR index,
  docs map, changelog, and governed repository logs.

## Safety boundary

- Posture remains `LOCAL_FIXTURE`.
- No target, programme, provider, model API, socket, browser automation against
  an external site, credential, payment, deployment, or publishing system was
  contacted.
- Lane 3, external Scope Watch collection, a network broker, Ubuntu worker, and
  `PASSIVE_HTTP` remain explicitly unavailable.
- The three generated UI concepts are preview-only and are not repository
  product assets or evidence that an interactive workbench exists.

## Verification

- Focused capability/dashboard suite: `36 passed in 2.86s`.
- Initial capability/dashboard full suite: `534 passed`; guided-learning full suite: `546 passed in 22.58s`.
- `python -m compileall -q greytheory`: exit 0.
- `git diff --check`: exit 0 (Git emitted line-ending notices only).
- CLI dashboard JSON verification showed:
  - Lanes 1, 2, and 4: `live`;
  - Lane 3: `unavailable`;
  - learning catalogue/mastery: `live`;
  - guided learning: `partial`;
  - offline Scope Watch: `live`;
  - governed Scope Watch collector: `unavailable`;
  - graphical workbench: `planned`;
  - passive HTTP worker: `unavailable`.
- Changed-Markdown local-link check: PASS across 18 changed files.
- Public package import proof: PASS; 22 capability entries plus guided planner and journey store exported.
- Repository-wide Markdown link check also identified three pre-existing links
  from 2026-08-09 logs to an absent sibling `chaseintech-personal-site`
  checkout. They were not introduced or changed by this branch.
- Private CLI learning proof reached active `assess` at revision 4 after a real
  synthetic fixture receipt, evidence reference, and written reflection. It
  retained `awards_mastery: false`, had zero mastery assessments, and refused
  completion without a persisted human assessment (exit 1).

## Remaining

- Operator selection of workbench concept 1, 2, or 3.
- Interactive workbench and local application service.
- Adaptive scheduling, assisted/transfer-specific journeys, and the graphical Learn surface.
- General local fixture process broker.
- All Milestone 9 posture, broker, worker, and sustained-operation gates.
