# Documentation Map

Where to start, and which document wins when two disagree.

## Authority order

1. [`../PROJECT_DEFINITION.md`](../PROJECT_DEFINITION.md) — canonical identity, boundaries, and capability truth.
2. [`scope-policy.md`](scope-policy.md) — current operating authority; it wins on what may happen now.
3. Subject canon: [`../DOMAIN_MODEL.md`](../DOMAIN_MODEL.md), [`../AUTONOMY_MODEL.md`](../AUTONOMY_MODEL.md), [`../DATA_POLICY.md`](../DATA_POLICY.md), [`../THREAT_MODEL.md`](../THREAT_MODEL.md), and [`../INTEGRATION_BOUNDARIES.md`](../INTEGRATION_BOUNDARIES.md).
4. [`roadmap.md`](roadmap.md) — implementation order and exit conditions.
5. [`definition.md`](definition.md) — detailed trust-kernel definition and historical decision register.
6. Other current documentation.
7. [`full-brief.md`](full-brief.md) and [`architecture.md`](architecture.md) — historical snapshots where marked.

## Start here

| Need | Read |
|---|---|
| Current project identity and capability truth | [`PROJECT_DEFINITION.md`](../PROJECT_DEFINITION.md) |
| Current implementation stage | [`PROJECT_STATE.md`](../PROJECT_STATE.md) |
| Build order | [`roadmap.md`](roadmap.md) |
| Research objects | [`DOMAIN_MODEL.md`](../DOMAIN_MODEL.md) |
| Vulnerability cards, local labs, and mastery graph | [`DOMAIN_MODEL.md`](../DOMAIN_MODEL.md#milestone-5-exit-condition) · [`vuln-coverage-matrix.md`](vuln-coverage-matrix.md) |
| Transparent hypothesis ranking and private research queues | [`DOMAIN_MODEL.md`](../DOMAIN_MODEL.md#milestone-6-exit-condition) · [`ADR-0007`](decisions/ADR-0007-transparent-ranking-without-authority.md) |
| Human/AI/execution boundaries | [`AUTONOMY_MODEL.md`](../AUTONOMY_MODEL.md) |
| Threats before networking | [`THREAT_MODEL.md`](../THREAT_MODEL.md) |
| Data handling | [`DATA_POLICY.md`](../DATA_POLICY.md) |
| Standalone/ChaseOS/worker boundaries | [`INTEGRATION_BOUNDARIES.md`](../INTEGRATION_BOUNDARIES.md) |
| What is allowed right now | [`scope-policy.md`](scope-policy.md) |
| Architecture decisions | [`decisions/`](decisions/README.md) |
| Workbench application, learning, storage, and worker boundary | [`workbench-architecture.md`](workbench-architecture.md) |
| AI-native learner dashboard, agent-security track, visualisations, and delivery stages | [`ai-native-learning-workbench.md`](ai-native-learning-workbench.md) |
| Exact live-programme compatibility fields and transition gate | [`live-programme-transition.md`](live-programme-transition.md) |
| Passive pilot broker and worker gates | [`ADR-0011`](decisions/ADR-0011-dark-passive-broker-foundation.md) · [`ADR-0013`](decisions/ADR-0013-passive-capture-encryption-and-key-lifecycle.md) · [`ADR-0014`](decisions/ADR-0014-network-free-passive-adapter-contract.md) · [`ADR-0015`](decisions/ADR-0015-unlaunched-passive-worker-primitives.md) · [`ADR-0016`](decisions/ADR-0016-offline-ubuntu-primitive-host-acceptance.md) · [`ADR-0018`](decisions/ADR-0018-keep-broker-authority-outside-passive-worker.md) · [`ADR-0019`](decisions/ADR-0019-windows-dpapi-root-kek-candidate.md) · [`ADR-0020`](decisions/ADR-0020-accept-namespace-lifetime-exact-egress-candidate.md) · [`THREAT_MODEL.md`](../THREAT_MODEL.md#preconditions-for-any-network-posture) |
| Real public programme-source evidence | [`HackerOne/GitLab`](../fixtures/programmes/public/hackerone-gitlab-2026-08-09/) · [`Bugcrowd/YNAB`](../fixtures/programmes/public/bugcrowd-ynab-2026-08-09/) · [`Direct policy/MCP Python SDK`](../fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/) |

## Trust kernel and current implementation

- [`definition.md`](definition.md) — three planes, invariants, capability register, and earlier decisions.
- [`system-overview.md`](system-overview.md) — implemented offline path and why it is shaped this way.
- [`diagrams.md`](diagrams.md) — trust-kernel flows and boundaries.
- [`module-breakdown.md`](module-breakdown.md) — current module ownership.
- [`data-flow.md`](data-flow.md) — authorisation to defensible artifact.
- [`validation-policy.md`](validation-policy.md) — validation gates and demotion.
- [`evidence-policy.md`](evidence-policy.md) — evidence location, integrity, and export.
- [`workbench-architecture.md`](workbench-architecture.md) - application boundary, required journeys, deployment shape, and acceptance evidence.
- [`ai-native-learning-workbench.md`](ai-native-learning-workbench.md) - learner-first information architecture, bounded AI coach, agent-security curriculum, visual direction gate, responsive acceptance, and Windows-to-Ubuntu transition.
- [`live-programme-transition.md`](live-programme-transition.md) - dark compatibility adapter, five mandatory activation gates, and the exact signal for considering a passive pilot.
- [`ADR-0011`](decisions/ADR-0011-dark-passive-broker-foundation.md) - dark passive ticket, DNS, replay, kill-switch, and receipt boundary before any network adapter.
- [`ADR-0013`](decisions/ADR-0013-passive-capture-encryption-and-key-lifecycle.md) - ticket-bound capture encryption and operator-side wrapped recipient-key lifecycle without enabling a worker.
- [`ADR-0014`](decisions/ADR-0014-network-free-passive-adapter-contract.md) - exact-address passive adapter orchestration proved with injected conformance doubles and no network implementation.
- [`ADR-0015`](decisions/ADR-0015-unlaunched-passive-worker-primitives.md) - cancellable system-DNS and numeric direct-TLS primitives implemented without a launcher.
- [`ADR-0016`](decisions/ADR-0016-offline-ubuntu-primitive-host-acceptance.md) - Ubuntu 24.04 WSL2 primitive proof inside a loopback-only, no-route namespace without enabling a worker.
- [`ADR-0018`](decisions/ADR-0018-keep-broker-authority-outside-passive-worker.md) - two-phase owned-process assembly that keeps broker authority out of the worker; its full no-route Ubuntu host harness now passes.
- [`ADR-0019`](decisions/ADR-0019-windows-dpapi-root-kek-candidate.md) - proposed Windows CurrentUser DPAPI root-KEK provider; same-profile candidate proof passes while ACL, independent recovery, and operator approval remain open.
- [`ADR-0020`](decisions/ADR-0020-accept-namespace-lifetime-exact-egress-candidate.md) - default-drop exact-address/port Ubuntu namespace proof with counted bypass denials; hardened-image binding remains open.

## Planning and research policy

- [`open-questions.md`](open-questions.md) — unresolved choices with resolution conditions.
- [`vuln-coverage-matrix.md`](vuln-coverage-matrix.md) — designed signal surface; current detection coverage is three static offline collectors and learning coverage is twelve synthetic local fixtures.
- [`safe-local-demo-proof-plan.md`](safe-local-demo-proof-plan.md) — local demonstrations with no target contact.
- [`disclosure-authority-checklist.md`](disclosure-authority-checklist.md) — gate before any external action.
- [`product-boundary-map.md`](product-boundary-map.md) — allowed now versus blocked.

## Historical material

- [`full-brief.md`](full-brief.md) — complete 2026-08-07 handover snapshot; retained for history and implementation detail, superseded for identity/roadmap by the 2026-08-09 foundation.
- [`architecture.md`](architecture.md) — superseded lane-design reference.

## Writing rules

- Use LIVE, VERIFIED, PARTIAL, DESIGNED, PLANNED, UNAVAILABLE, HISTORICAL, BLOCKED, or DEFERRED honestly. `UNAVAILABLE` means the action or component has no shipped path; it is stronger and clearer than a merely unconfigured runtime.
- Product direction may be described as direction; it may not be described as working capability.
- Separate observation, deterministic proof, and inference.
- Name the mistake a rule prevents.
