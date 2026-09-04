# Agent Activity Log

A record of what each agent session did, **why it deviated from the roadmap where it did**, and what the next agent should not undo.

Read this before changing anything that looks arbitrary. Several guards in this codebase are deliberately stricter than they need to be, and the reasoning is here rather than in the code.

## 2026-09-04 - Codex - Ubuntu worker-image candidate

### What was built

- Canonical-signed base and archive-index verification for 18 exact packages.
- Two-build read-only SquashFS construction sourced from committed runtime code.
- Clean-HEAD image admission for bounded mounts/devices, non-root zero-capability
  execution, exact egress, immutable paths, and full receipt/replay evidence.
- Linked Windows-worktree normalization for Linux-side Git identity, clean-tree,
  source-digest, and archive checks.
- Four complete lock-bound package install groups that preserve `dpkg`
  pre-dependency enforcement.
- An owned, minimal temporary `/dev` tmpfs for package configuration while the
  ext4 build root remains `nodev`; host devices are never bound into staging.
- A canonical root-manifest diff at reproducibility refusal and removal of
  `ldconfig`'s optional filesystem-specific auxiliary cache during hardening.
- A clean two-build-identical release image and a corrected repository-rooted
  module invocation for the outer image-runtime acceptance composer.

### What the next agent should not undo

Do not bind or recursively mount the host `/dev` into a temporary root. The
WSL2 image-runtime candidate is accepted, but do not promote that to hardened
image, local-VM/reboot, posture, programme, or live-target acceptance. Keep
`hardened_worker_image_accepted=false`, retain the clean-source and two-build
requirements, and leave broker transport, key, programme, VPS, and human
posture gates independent.

### Verification

21 focused and all 708 repository tests pass; all 18 packages match
Canonical-signed indexes. The operator-approved Ubuntu restart restored process
creation, device nodes, and supervised user services. A clean release image and
WSL2 image-runtime acceptance record pass while hardened-image and reboot/VM
acceptance remain false.
See `07_LOGS/Build-Logs/2026-09-04-greytheory-ubuntu-worker-image-candidate.md`.

## 2026-09-04 - Codex - Ubuntu namespace-lifetime exact-egress candidate

### What was built

- A hash-locked, no-system-install nftables bootstrap under the governed E:
  tool cache, reconstructed in an owned temporary root on every run.
- Default-drop input/forward/output chains with one exact synthetic
  address/port, three counted bypass denials, and refused route/firewall
  mutation after the worker becomes unprivileged.
- A successful full encrypted Ubuntu worker record plus corrected desktop and
  390-pixel capability truth; the mobile footer no longer obscures panels.

### What the next agent should not undo

Do not mark the durable egress or hardened-image roadmap item complete. The
accepted policy lasts for the owned namespace only, and the retained record
explicitly says `hardened_worker_image_accepted=false`. Do not install the
acceptance packages globally, remove their hash checks, allow the decoy address,
or infer programme/VPS/posture authority.

### Verification

698 repository tests, 23 UI tests, 4 Sites tests, production build,
PowerShell/bash syntax, one accepted Ubuntu host record, and inspected
desktop/mobile captures pass. See
`07_LOGS/Build-Logs/2026-09-04-greytheory-ubuntu-exact-egress-candidate.md`.

## 2026-09-04 - Codex - Windows DPAPI root-KEK candidate

### What was built

- A strict operator-side CurrentUser DPAPI root-KEK provider candidate with
  audited provision/lease operations, exclusive first publication, bounded
  records, and a short-lived zeroing lease.
- Real same-profile restart/protected-copy recovery, tamper refusal, capture
  decryption, plaintext-tree scanning, and audit-chain host proof.
- Corrected executable/UI capability truth for the implemented graphical
  workbench, plus clean desktop and 390-pixel rendered evidence.

### What the next agent should not undo

Do not mark the key-provider gate complete. The observed application-data ACL
is not accepted, recovery is bound to the same Windows profile, and the
operator has not approved this provider or backup policy. Do not move the root
KEK or recipient private key into the Ubuntu worker, wire the provider to a
posture switch, or describe `PARTIAL` Mission Control as a signed standalone
release.

### Verification

694 repository tests, 22 UI tests, 4 Sites tests, and the production build pass.
The accepted host record is
`E:\Projects\GreyTheory\acceptance\windows-dpapi-root-kek-20260904-095757-20740\acceptance.json`.
See `07_LOGS/Build-Logs/2026-09-04-greytheory-windows-dpapi-root-kek-candidate.md`.

## 2026-09-04 - Codex - Ubuntu full-service no-route acceptance

### What was built

- An enforced LF line-ending contract for Linux entrypoints used through WSL.
- Durable JSON/error output and local-only invariant validation in the bounded
  Windows-to-Ubuntu wrapper.
- A successful Ubuntu 24.04.4 full worker-service acceptance record covering
  non-root identity, zero capabilities, no-new-privileges, exact synthetic
  request, encrypted capture, receipt verification, replay, and cleanup.

### What the next agent should not undo

Do not infer durable egress, a hardened image, OS-bound KEK, programme
permission, VPS suitability, or posture approval from the no-route fixture.
Do not remove the LF attribute; Bash failed before namespace setup when the
entrypoint was checked out as CRLF.

### Verification

Accepted record:
`E:\Projects\GreyTheory\acceptance\ubuntu-worker-service-20260904-092741-23640\acceptance.json`.
See `07_LOGS/Build-Logs/2026-09-04-greytheory-ubuntu-full-service-acceptance.md`.

## 2026-09-04 - Codex - Windows current-user install lifecycle

### What was built

- A non-admin installer with separate application/runtime and private-data
  roots, a capability-truth manifest, and a Start Menu-shaped shortcut.
- A launcher that opens the dashboard only after local-only health succeeds.
- Lifecycle acceptance for a real persisted learning command across restart,
  same-wheel upgrade, and replaceable-runtime recovery.

### What the next agent should not undo

Do not put browser/process convenience inside `greytheory_local`; its import
guard intentionally keeps the trusted local package free of browser, subprocess,
and target-client adapters. Do not describe current-user isolated-path
acceptance as a genuinely separate-user or signed-installer result.

### Verification

686 repository tests pass. The accepted lifecycle record is
`E:\Projects\GreyTheory\acceptance\windows-user-install-20260904-092039-9220\acceptance.json`.
See `07_LOGS/Build-Logs/2026-09-04-greytheory-windows-user-install-lifecycle.md`.

## 2026-09-02 - Codex - Guided mission and programme readiness

### What was built

- An exact 30-minute mission budget with selectable Learn, Practise, Prove,
  Reflect, and Assess stages.
- Two scored scenarios per current topic plus a learner-explanation threshold;
  the Safe Lab unlocks only for practice and never awards mastery.
- An offline programme-to-synthetic-case explainer for the saved HackerOne,
  Bugcrowd, and direct-policy bundles.

### What the next agent should not undo

Do not convert saved programme text, scenario answers, or lab completion into
authority, target access, proof, or mastery. YNAB ambiguity and live posture
must remain blocked until their independent gates pass.

See `07_LOGS/Build-Logs/2026-09-02-greytheory-guided-mission-and-programme-readiness.md`.

## 2026-09-02 - Codex - Navigation scrollbar and keyboard follow-up

### What was built

- Matched the visible navigation scrollbar to the Guided Mission Control navy,
  muted-blue, and amber system without hiding the scroll affordance.
- Added a stable gutter, overscroll containment, regression coverage, and
  current desktop and mobile visual QA.
- Reconfirmed the drawer focus loop and recorded the runtime focusable order.

### What the next agent should not undo

Do not restore bright native drawer chrome, hide the only vertical scroll cue,
or claim whole-app first-entry keyboard acceptance from a DOM-order inventory.
The current browser harness still cannot issue the initial Tab from BODY.

See `07_LOGS/Build-Logs/2026-09-02-greytheory-navigation-scrollbar-and-keyboard.md`.

## 2026-09-02 — Codex — Keyboard boundaries and packaged Windows workbench

### What was built

- Corrected compact/mobile navigation semantics and focus containment without
  changing the selected Guided Mission Control visual direction.
- Added reproducible wheel assembly with bundled UI and learning resources.
- Added empty-prefix Windows launcher/UI/health/snapshot acceptance with exact
  process cleanup and a non-echoed ephemeral environment token.

### What the next agent should not undo

Do not make an off-screen drawer focusable, strip accessible names from
icon-only navigation, log an active session token, or call isolated-prefix
acceptance a clean-user installer result. Keep `LOCAL_FIXTURE` and all five
live-programme gates intact.

See `07_LOGS/Build-Logs/2026-09-02-greytheory-keyboard-and-windows-package.md`.

## 2026-09-02 — Codex — Interactive learning paths and intelligence contracts

### What was built

- Added inspectable 24-node skill trajectories and topic-owned four-stage
  roadmaps without converting exploration into mastery.
- Restored the selected shell's complete thirteen-panel navigation.
- Added a network-free, identifier-only contract for five public vulnerability
  intelligence sources and kept bug-bounty account connectors dark.

### What the next agent should not undo

Keep browser previews credential-free, provider plans non-executing, target
inputs rejected, and imported intelligence distinct from finding evidence.

See `07_LOGS/Build-Logs/2026-09-02-greytheory-interactive-learning-paths.md`.

## 2026-09-02 — Codex — Case Pack and persisted learner foundation

### What was built

- Added three versioned Case Packs, immutable synthetic receipts, same-origin
  learner command persistence, and a working three-run Demo Suite.
- Added a dark live-programme compatibility contract and documented its five
  all-or-nothing transition gates.
- Added bounded same-origin static UI serving without adding a target client.

### What the next agent should not undo

Keep cross-origin previews read-only. Never accept programme authority from the
browser, award mastery from a fixture, treat synthetic evidence as a live
finding, or use a VPS to skip local Windows and Ubuntu acceptance.

See `07_LOGS/Build-Logs/2026-09-02-greytheory-case-pack-foundation.md`.

## 2026-09-01 — Codex — AI-native learner dashboard direction

### What was established

- The current Research Ledger is retained as a case view, not the final home.
- Real desktop and 390-pixel captures show horizontal clipping, so the earlier
  responsive acceptance claim is no longer current.
- Three modern directions and an editable Figma board now ground the next choice.
- The learner-first architecture, agent-security track, bounded AI coach,
  visualisations, responsive gate, and Windows-to-Ubuntu transition are documented.

### What the next agent should not undo

Do not implement from prose or silently merge all three concepts. Wait for the
operator to select 1, 2, or 3. Keep AI advisory, mastery human-assessed,
`LOCAL_FIXTURE` visible, and the Windows-local pilot separate from the later
Ubuntu worker and VPS posture gates.

See `07_LOGS/Build-Logs/2026-09-01-greytheory-ai-native-dashboard-direction.md`.

## 2026-08-26 - Codex - Ubuntu service harness hardening

### What was built

- Replaced fragile inline Bash with a checked-in no-route namespace script and
  exact Windows-side timeout/owned-client cleanup.
- Isolated WSL's hosts mount and covered the resolver's absolute dotted name.
- Started the Linux worker from a clean fork server and forked DNS only inside
  the scrubbed authority-free worker.
- Verified 92 focused passive-security tests and a 665-test repository baseline.

### Boundary retained

No complete Ubuntu JSON record exists. Shared WSL/Hermes startup became
unreliable again; unrelated processes and the shared distro/service were not
stopped, and `PASSIVE_HTTP` remains unavailable.

A later retry with no WSL clients present failed inside WSL at
`CreateVm/0x800705b4` before namespace startup. The wrapper returned nonzero,
left no owned client, and now retains its native handle so PowerShell preserves
the real exit code.

See `07_LOGS/Build-Logs/2026-08-26-greytheory-ubuntu-service-harness-hardening.md`.

## 2026-08-26 - Codex - Owned-process passive worker assembly

### What was built

- Added one capped spawned worker process that may resolve once and perform one
  broker-rechecked exact TLS request before exiting.
- Kept broker authority and private keys in the parent; scrubbed the child
  environment and enforced non-root/zero-capability/no-new-privileges identity.
- Added a full no-route Ubuntu service harness, 91 focused passing tests, and a
  664-test passing repository baseline.

### Boundary retained

The first host run timed out without evidence and WSL then became unavailable.
The refined harness is not host-accepted; no unrelated Hermes process was
stopped, and `PASSIVE_HTTP` remains unavailable.

See `07_LOGS/Build-Logs/2026-08-26-greytheory-owned-process-worker-assembly.md`.

## 2026-08-26 - Codex - Transparent adaptive learning tracks

### What was built

- Added inspectable evidence-history review scheduling with persisted policy
  references and rationales.
- Added bounded standard, assisted, and transfer journeys through the shared
  learning domain, CLI, private stores, application service, and snapshot.
- Added structural caps for assisted mastery and distinct-context proof for
  transfer, with 50 focused and 651 full repository tests passing.

### Boundary retained

Journeys do not award mastery or execute fixtures. Broader curricula and the
graphical Learn/workbench surface remain unbuilt; `LOCAL_FIXTURE` is unchanged.

See `07_LOGS/Build-Logs/2026-08-26-greytheory-adaptive-learning-tracks.md`.

## 2026-08-25 - Codex - Offline Ubuntu primitive host acceptance

### What was built

- Added an offline Ubuntu 24.04 WSL2 acceptance wrapper and Python harness.
- Used an ephemeral user/network namespace with only loopback and no default
  route, assigning a synthetic public address locally so the unchanged
  production request contract could be exercised without target contact.
- Proved production numeric TLS, no re-resolution, explicit CA and hostname
  checks, mismatch refusal, split-header capture, zero body, and cleanup.
- Proved the resolver parent's real spawn/deadline/termination path with a
  deliberately blocking replacement child.

### What the next agent should not undo

Do not run the synthetic address canary outside the no-route namespace. Do not
call the replacement-child cancellation check successful system-DNS proof, and
do not call WSL2 primitive proof an assembled worker, unprivileged image, VPS
acceptance, or posture approval. `PASSIVE_HTTP` remains unavailable.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-ubuntu-primitive-host-acceptance.md`.

---

## 2026-08-25 - Codex - Unlaunched passive worker primitives

### What was built

- Added a cancellable absolute-name system resolver in one owned spawn child,
  with capped non-pickle JSON IPC and exact terminate/kill cleanup.
- Added direct numeric IPv4/IPv6 TLS transport with explicit CA trust,
  hostname/SNI verification, TLS 1.2+, HTTP/1.1 ALPN, disabled TLS key logging,
  shared-deadline timeouts, bounded header reads, peer verification, and close
  on every path.
- Added syscall-injected conformance for process, pipe, socket, TLS, timeout,
  overflow, body, peer, ALPN, CA, IPv6, and cleanup behavior.

### What the next agent should not undo

Do not add a default CA, KEK, target, ticket source, proxy-aware URL client, or
launcher to these primitives. Do not claim injected syscall tests prove Ubuntu
behavior. Assemble only inside the isolated worker after host and egress plans
are explicit; keep `PASSIVE_HTTP` unavailable until canary and posture gates.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-passive-worker-primitives.md`.

---

## 2026-08-25 - Codex - Network-free passive adapter contract

### What was built

- Added an injected resolver/direct-transport orchestration contract with no
  network or process imports.
- Bound each transport result to the full ticket/request/address/TLS/deadline
  contract, parsed one strict bounded response-header block, encrypted it, and
  sealed completion or every denial through the passive broker.
- Added denial proof for private/mixed DNS, wrong host/address/SNI/request,
  proxy use, followed redirects, body bytes, open connections, malformed or
  oversized headers, kill switch, and resolution/transport deadlines.

### What the next agent should not undo

Do not mistake injected conformance evidence for OS behavior. The production
resolver and direct TLS transport must not re-resolve, consult proxy settings,
follow redirects, receive a body, or own policy. Keep them confined to the
future Ubuntu worker and keep `PASSIVE_HTTP` dark through host acceptance.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-passive-adapter-contract.md`.

---

## 2026-08-25 - Codex - Passive capture encryption and key lifecycle

### What was built

- Added X25519/HKDF/ChaCha20-Poly1305 capture envelopes authenticated against
  their ticket digest, recipient, plaintext digest, size, and timestamp.
- Added operator-side recipient provision/rotation/revocation with private keys
  AES-256-GCM wrapped under a purpose-derived key from an external root KEK,
  plus a separately authenticated manifest and old-evidence recovery.
- Tightened completed receipts to accept only the typed envelope and derive
  their byte count and digests from it.

### What the next agent should not undo

Do not give a worker a private recipient key or persist/default the root KEK.
Do not treat ciphertext as lower than `RAW_RESTRICTED`. Keep the broker dark
until OS secret-provider, DNS/HTTP, transport, worker, canary, and explicit
posture gates are independently accepted.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-passive-capture-encryption.md`.

---

## 2026-08-25 - Codex - Governed local claim lifecycle

### What was built

- Added exact two-account-fixture claim assembly from existing private raw
  evidence and persisted operator attestations, rerunning five deterministic
  validators and creating all seven role bindings without another action.
- Added atomic finding/report-matrix persistence, fresh-pass-gated internal
  progression to `report_ready`, a hard stop before submission, and private
  export of the digest-bound finding/receipt chain.

### What the next agent should not undo

Do not generalise this handler by accepting UI-authored claims, receipts,
authority, target, lifecycle destination, or arbitrary artifact shapes. Keep
claim assembly exact-fixture-only until another validator-backed adapter has
its own evidence contract. Never let the internal lifecycle handler cross
`report_ready`.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-local-claim-lifecycle.md`.

---

## 2026-08-25 - Codex - Persisted human-bound report validation

### What was built

- Added a fresh human-acknowledged application handler that reruns Gates B-F
  from the persisted finding/draft and verified private evidence.
- Bound all three attestations to the configured local operator and known case
  evidence, then stored complete attestation and gate-result history under the
  report case's optimistic revision.

### What the next agent should not undo

Do not accept attester identity, authority, lifecycle state, or arbitrary
evidence references from the UI. A passing validation is Gate G eligibility
evidence only: it must not bind claim roles, promote a finding, export, submit,
contact a target, or change posture.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-persisted-report-validation.md`.

---

## 2026-08-25 - Codex - Persistent private report authoring

### What was built

- Added complete finding/claim-role/check-receipt round trips and an atomic,
  integrity-checked private report-case store.
- Added server-derived informational case creation and revision-safe full-draft
  saves, plus default runtime/read-model/export integration.

### What the next agent should not undo

Do not accept authority, programme, asset, finding state, or claim-matrix data
from the UI. Do not let prose completeness promote a claim or finding. Keep
authoring, validation, report-ready transition, export, and submission as
separate governed states.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-private-report-authoring.md`.

---

## 2026-08-25 - Codex - Bounded local-fixture action intent

### What was built

- Added a non-executing action-intent handler for an active persisted
  `LOCAL_FIXTURE` experiment.
- Derived authority-bearing context and stop conditions from server-held state,
  restricted the action to the planned in-scope fixture target, and retained
  store budget checks.

### What the next agent should not undo

Do not let the UI supply authority fingerprints, session/identity/stop-condition
bindings, arbitrary actions, or non-fixture action types. An accepted request is
intent only; it must never imply Gate approval, a receipt, or execution.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-local-action-intent.md`.

---

## 2026-08-25 - Codex - Private redacted report export

### What was built

- Added a human-acknowledged private report-export command over server-held
  report-ready state.
- Rechecked report quality, authority, and complete redacted evidence before
  atomically writing a digest-bound package outside Git.
- Recorded that no submission occurred in both manifest and audit.

### What the next agent should not undo

Do not accept report prose, draft state, an evidence subset, or a filesystem
path from the UI. Do not export an incomplete or unredacted evidence set, reuse
an export ID, or treat a private export as programme submission or disclosure.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-private-report-export.md`.

---

## 2026-08-25 - Codex - Human mastery assessment handler

### What was built

- Added the explicit workbench handler that records an evidence-bound human
  mastery assessment in the private store.
- Required freshness and acknowledgement, bound commands to the configured
  local operator, and derived human assessor identity inside the service.
- Kept accepted results non-executing and reused existing mastery-domain rules.

### What the next agent should not undo

Do not accept an assessor identity or assessor kind from the UI, infer mastery
from fixture/model/journey output, loosen evidence or rationale requirements, or
turn a recorded assessment into execution authority. The graphical form must
submit the existing command contract to the local application service.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-human-mastery-handler.md`.

---

## 2026-08-25 - Codex - Authenticated local workbench transport

### What was built

- Added `greytheory_local` private-store assembly and a Windows-first launcher.
- Added numeric-loopback-only JSON snapshots/commands with exact Host,
  in-memory token, exact-origin writes, no CORS, strict size/framing, and
  duplicate-key/header refusal.
- Kept the listener separate from the transport-neutral application service
  and added no target-network client or file-serving surface.

### What the next agent should not undo

Do not accept `localhost`, a configurable hostname, LAN/any-address binding,
ambient CORS, token-in-URL authentication, unbounded bodies, duplicate critical
headers, or UI-supplied executable state. Remote/VPS transport requires a new
decision; ADR-0012 authorizes only numeric local loopback.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-authenticated-local-transport.md`.

---

## 2026-08-25 - Codex - Governed research-planning handlers

### What was built

- Added create-only hypothesis, human scope-review, and atomic experiment-plan
  handlers to the transport-neutral workbench service.
- Added optimistic revisions to hypotheses and experiments, including a typed
  conflict for a race detected at the store write boundary.
- Derived authority, session, and workspace bindings from persisted state
  instead of accepting them from the UI.

### What the next agent should not undo

Do not let `PLAN_EXPERIMENT` silently scope a hypothesis, trust an authority
fingerprint supplied by the UI, or add the experiment and advance the
hypothesis in separate writes. An accepted application result still means a
private domain mutation only; `executed` remains false.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-research-planning-handlers.md`.

---

## 2026-08-25 - Codex - Dark passive broker foundation

### What was built

- Added the separate offline `greytheory_broker` package and `passive-head-v1`.
- Bound tickets to the latest exact verified Gate audit allow and made programme
  rate a fingerprinted authority field.
- Added canonical target/public-address policy, default-engaged kill switch,
  atomic cross-ticket rate/replay storage, and signed encrypted-capture receipt
  metadata.

### Why it remains dark

There is no resolver, HTTP adapter, encryption implementation, key provisioning,
worker image, broker transport, or external acceptance. Tests use synthetic
Gate posture only and contact no host. `PASSIVE_HTTP` remains unavailable.

### What the next agent should not undo

Do not add an HTTP client before capture encryption/key handling and adapter
conformance exist. Do not move address or redirect checks into callback code,
exclude rate from the authority fingerprint, accept a detached Gate decision,
or let an absent/corrupt kill switch fail open.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-passive-broker-foundation.md`.

---

## 2026-08-25 - Codex - Workbench application contract

### What was built

- Added the separate `greytheory_app` layer and versioned workbench contracts.
- Assembled fail-closed snapshots from the real programme, research, learning,
  hypothesis, evidence, report, approval, audit, and capability sources.
- Added bounded idempotent learning handlers with optimistic revisions. Other
  typed commands refuse without changing domain or execution state.

### What remains deliberately absent

There is no HTTP/IPC transport, graphical shell, process or network broker, or
posture above `LOCAL_FIXTURE`. Do not interpret an accepted learning-domain
command as tool execution, and do not expose refused command shapes until their
dedicated application handlers and tests exist.

### Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-workbench-application-contract.md`.

---

## 2026-08-24 - Codex - Workbench foundation and executable capability truth

### What was built

- Added a typed capability register shared by the dashboard and future workbench.
- Corrected stale dashboard claims about offline signal, learning, model, and Scope Watch capability.
- Accepted ADR-0010 and documented the Windows-first workbench, local application-service contract, private storage, guided-learning journey, and future isolated Ubuntu worker boundary.
- Implemented deterministic learning recommendations, ordered evidence-bound journey stages, integrity-checked private persistence, optimistic revisions, and CLI operation without automatic mastery.

### Why before the interactive workbench

The operator requested a real research operating system, not a decorative
dashboard. All three visual concepts need the same truthful capability source,
command boundary, storage model, and learning-to-evidence journey. Implementing
those direction-independent contracts first prevents the selected UI from
becoming a second authority path or hard-coding stale status copy.

### What the next agent should not undo

Do not put the UI framework, local server, or network worker inside
`greytheory/`. Do not let a screen call collectors or tools directly. Do not use
`LIVE` as a runtime-health claim, and do not collapse `UNKNOWN` into zero. The
visual direction is still operator-owned; build the selected concept against
ADR-0010 rather than inventing a fourth.

### Verification

See `07_LOGS/Build-Logs/2026-08-24-greytheory-workbench-foundation.md`.

---

## 2026-08-24 — Codex · Offline boundary made structural

### What was built

- Removed the `allow_network_fetcher=True` Scope Watch escape hatch.
- Restricted the core to the exact rooted `LocalSourceFetcher`; arbitrary fetchers and subclasses fail closed before their code runs.
- Made historical local demonstrations deterministic at their recorded fixture time so the full clean-checkout suite remains reproducible without changing real stale-contract rules.

### Why

A Boolean supplied by the same caller that supplies executable fetcher code is not an approval receipt. The earlier check trusted an adapter's self-reported `network` attribute and let the caller bypass it. The trust kernel now consumes captured local evidence only. Network collection remains a separate, unbuilt, operator-gated system.

### What the next agent should not undo

Do not reintroduce a generic fetcher or `allow_network` option inside `ScopeWatch`. A future collector needs its own verified authority, URL/DNS/redirect policy, budgets, receipts and kill switch, then writes a local captured-source artifact for the core.

### Verification

See `07_LOGS/Build-Logs/2026-08-24-portfolio-security-hardening.md`.

---

## 2026-08-09 — Claude · Model gateway and Scope Watch (Milestones 7 and 8)

### What was built

- `greytheory/models/` — provider policy, nine role contracts, the gateway, and an eight-case evaluation harness.
- `greytheory/scopewatch.py` — source re-reading, change detection, review invalidation.
- 49 new tests. Suite: 476 → 525.

Full reasoning in [ADR-0009](decisions/ADR-0009-model-gateway-and-fetcher-boundaries.md).

### Why the milestone order stopped mattering

The previous entry recommended swapping 7 and 8 because Scope Watch is the safer first network component. Both are now built, so the ordering question dissolved — but only because **neither turned out to need the network.**

That was the real finding. Both components' valuable logic sits entirely on the offline side of a protocol boundary. The model gateway takes a `ModelProvider`; Scope Watch takes a `SourceFetcher`. The core ships only offline implementations, and everything worth testing — classification, citations, provenance, budgets, change detection, invalidation — is provable without a network, a key or a bill.

### What the next agent should not undo

**Do not put a real provider or an HTTP fetcher inside `greytheory/`.** CI enforces it, but the reason matters more than the check: the trust kernel's value is that its guarantees hold without trusting anything it cannot see.

**Do not move classification from assembly to send.** Checking at send time creates a window in which an unclassified string can be appended to an already-approved prompt.

**Do not downgrade an unresolvable citation to a warning.** A model citing context that was never supplied invented a source. It is the cheapest fabrication detector available.

**Do not log prompt content.** The audit records a digest. A log that re-exposes the sensitive fragment it was recording defeats the classification it just enforced.

**Do not make `UNREACHABLE` collapse into `UNCHANGED`.** A source nobody could read has not been shown to be the same. Equally, do not make it invalidate review — "could not read it" is not "it changed", and conflating those makes every network blip look like scope drift.

**Do not remove the negative fixtures from the eval suite.** They look like failing tests and are not: they assert the detectors fire on known-bad replies. Without them the suite cannot tell a working harness from a well-behaved model.

### Still open

Unchanged from the previous entry except where noted:

| Gap | Note |
|---|---|
| `ApprovalProvider` protocol | ADR-0003 exists, the code does not. Still the clearest next trust-kernel work. |
| Signed audit checkpoints | Needs an operator key, therefore a dependency outside the core. |
| Evidence tombstones | Write-once raw evidence versus the duty to delete third-party data. |
| Taint labels on stored evidence | **Partially addressed.** `TrustLabel` now exists for model context; evidence artifacts still do not carry it. |
| Plugin conformance suite | No adapter tested against denial, rate and scope fixtures. |
| Network fetcher for Scope Watch | Deferred to the posture decision, by design. |

### Verification

```
525 tests, up from 476
8/8 evaluation cases clean against the stub provider
no network import in greytheory/ (CI-enforced)
```

---

## 2026-08-09 — Claude · Claim roles and submission-time scope recheck

### What was built

- `greytheory/claims.py` — seven claim roles, `RoleBinding`, the claim-evidence matrix.
- `greytheory/validators.py` — four reusable validators settling the checked roles from artifacts already held.
- `greytheory/findings.py` — `report_ready` now requires role coverage; `submitted` now requires a `ScopeRecheck`.
- `greytheory/vertical_slice.py` — binds all seven roles with no additional fixture interaction.
- `tests/test_claim_roles.py` — 29 tests. Suite: 447 → 476.

Full reasoning in [ADR-0008](decisions/ADR-0008-claim-roles-and-submission-scope-recheck.md).

### Why this instead of Milestone 7

**The roadmap said Milestone 7 was the model gateway. I did not build that.** This is a deliberate deviation and the operator approved it.

The reasoning:

1. **Two open holes were cheaper to close than the next milestone was to open.** The productisation review identified both in §20. Neither was addressed by Milestones 1–6, and both are in the trust kernel — the part everything else assumes is correct.

2. **The `report_ready` guard was the weaker of the two and the more embarrassing.** Milestone 4 had already proved a finding could reach report-ready. It reached it on one checked claim. Building a model gateway on top of a guard that weak would have meant adding AI capability above a foundation that could not distinguish a proven vulnerability from a proven HTTP 200.

3. **The model gateway gates nothing.** It can be built offline at any time and nothing waits on it. The two guards, by contrast, are load-bearing for every finding that will ever pass through the system.

### The other roadmap change I would make, and did not

**Milestone 7 (model gateway) and Milestone 8 (Scope Watch) should swap.**

Scope Watch is the *safer* first network component — it fetches public policy pages, not targets — and it exercises the network worker, the execution broker and change detection under the lowest available operational risk. The review itself argues this in Milestone 8 ("why first: it touches public policy sources rather than targets") and then places it second anyway.

I have not made this change because reordering the roadmap is the operator's call, not an agent's. It is recorded here so the next session does not have to rediscover it.

### What the next agent should not undo

**Do not relax the seven-role guard back to a count.** A count of checked claims can be satisfied by proving almost nothing, and that is what it was before. If the guard is inconvenient, the finding is probably not ready.

**Do not make `impact` a checked role.** Whether a proven behaviour matters is a judgement about the product, its users and the programme's view. A validator adjudicating it would manufacture exactly the false certainty this project exists to prevent.

**Do not make `reproduction` a checked role either** — this is the one that looks wrong and is not. It is checkable in principle, but only by acting on the target twice. Requiring a receipt would push every finding in the system into doubling its interaction, against invariant I4. Gate B in `validation.py` already treats reproducibility as attested-plus-evidence; the two mechanisms must agree.

**Do not downgrade the scope recheck to a warning.** A warning at submission time is read by someone who has already decided to submit.

**Do not let the role validators perform any interaction.** They settle their questions from bytes already stored. That constraint is what keeps the stricter guard compatible with minimum-impact proof. A validator that fetches something has broken the design.

**Do not treat an empty evidence manifest as verified.** `EvidenceIntegrityValidator` returns `invalid_input` on an empty set on purpose. "Nothing to check" is not "everything verified" — the same rule the dashboard follows for absent data.

### Still open from the review

Verified absent from the codebase (grepped, zero hits) as of this session:

| Gap | Note |
|---|---|
| `ApprovalProvider` protocol | **ADR-0003 exists; the code does not.** The clearest next piece of trust-kernel work. |
| Signed audit checkpoints | The hash chain detects alteration from a known start, but a writer with full access can rewrite and recompute the whole chain. Needs an operator key, therefore a dependency outside the core. |
| Evidence tombstones | Write-once raw evidence conflicts with the duty to delete accidentally captured third-party data. Needs hard deletion plus an immutable record that something was deleted and why. |
| Taint labels for target content | Target-controlled text can attempt to influence the model. Not yet formally distinguished from operator content. |
| Plugin conformance suite | No adapter is tested against denial, rate and scope fixtures. |
| Model gateway | Milestone 7 as written. |

### Verification

```
447 tests before this session's changes, all passing
476 tests after
no network import in greytheory/ (CI-enforced)
```

The twelve failures encountered mid-change were all callers satisfying the old weak guard, including the Milestone 4 vertical slice. Each was updated rather than exempted.

---

## Template for future entries

```markdown
## YYYY-MM-DD — <agent> · <one-line summary>

### What was built
### Why this instead of what the roadmap said
### What the next agent should not undo
### Still open
### Verification
```
