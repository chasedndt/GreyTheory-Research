# Open Questions

Tracked unknowns. Each has an owner and a resolution condition. Nothing here may be assumed resolved in code or copy.

## Resolved (2026-08-06)

| # | Question | Resolution |
|---|---|---|
| R1 | Is GreyTheory a detection pipeline or a control plane? | Control plane. Lanes are plugins. See `definition.md` D1. |
| R2 | Are `finding` and `finding_candidate` different objects? | No — one entity, one lifecycle. `definition.md` §4. |
| R3 | Build substrate | Local-first Python package with tests, no network in the core. |
| R4 | External testing posture for this phase | Local-only until the Authority Plane can gate it. |
| R5 | README vs scope-policy contradiction on automatic probing | `scope-policy.md` wins; README corrected. |
| R6 (was O2) | Does ChaseOS already own approval / audit / graph layers? | **Yes, all three.** GreyTheory reads ChaseOS approvals where present and builds no graph. Full table in `chaseos-reconciliation.md`. |
| R7 (was O3) | Where does raw evidence live? | Outside every git working tree, enforced by a hard guard. Standalone default is the platform user-data directory; `CHASEOS_VAULT_ROOT` is an optional integration. See `evidence-policy.md`. |
| R9 (was O1) | What is Grapevine AI? | **Cut.** It came from a planning document that stated it had never seen the implementation, and none was found. The useful capability is restated as Scope Watch in `roadmap.md` Phase 5. |
| R10 | Is GreyTheory a governance product or a research engine? | **A research engine.** It governs the operator's own research. Governance offerings for other people's agents are derivative and separate. `definition.md` §1. |
| R8 | Is GreyTheory standalone or ChaseOS-dependent? | **Standalone, first-class.** Apache-2.0, zero runtime dependencies, fully functional with no ChaseOS present. ChaseOS integration is an adapter, never a requirement. |

## Open — blocking

| # | Question | Why it blocks | Resolution condition |
|---|---|---|---|
| O9 | Should ChaseOS's run audit be made tamper-evident? | Not blocking GreyTheory, but `runtime/operator_surface/audit.py` writes editable per-run JSON. For a system that must prove authority after the fact, that is the weak link. | Operator decision on whether to port GreyTheory's hash chain into ChaseOS. ~40 lines, no schema change. |
| O10 | Dashboard panels and tabs | Operator will define these. The read model should be shaped to serve them rather than retrofitted. | Operator specification of panels; then a query layer over audit, contracts, evidence manifests and findings. |

## Open — non-blocking

| # | Question | Notes |
|---|---|---|
| O4 | Which programme becomes the first compiled `ScopeContract`? | Needed for Plane 1 validation against real-world rule text, not for testing. A public programme page can be compiled without any interaction with the target. |
| O5 | Severity framework — CVSS, programme-native, or both recorded? | Leaning: record both, never let either drive submission decisions. |
| O6 | Curriculum substrate — files, or the same schema store as everything else? | Defer until Plane 1 exists. |
| O7 | Does GreyTheory graduate to a standalone business lane, or stay a ChaseOS incubation lane? | Graduation criteria already exist in `roadmap.md` Phase 4. |
| O8 | Studio/dashboard surface — terminal-only, local web, or ChaseOS Studio integration? | Defer. Terminal output is sufficient for the first proof slice. |
