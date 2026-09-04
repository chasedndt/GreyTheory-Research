"""Executable capability truth for GreyTheory surfaces.

Documentation explains why a capability has its status.  This module gives the
CLI, dashboard, and future workbench one small, typed register so that surfaces
cannot quietly drift into different answers about what exists.

The register describes shipped code, not runtime health.  A LIVE capability can
still have no configured data source; dashboard metrics must continue to render
that absence as UNKNOWN.  Nothing here grants authority or enables I/O.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityStatus(str, Enum):
    """Product truth states exposed to researchers."""

    LIVE = "live"
    PARTIAL = "partial"
    PLANNED = "planned"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Capability:
    """One capability and the boundary that prevents status inflation."""

    id: str
    label: str
    status: CapabilityStatus
    detail: str
    boundary: str
    evidence_refs: tuple[str, ...] = ()


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "programme_registry",
        "Programme registry",
        CapabilityStatus.LIVE,
        "Versioned local contracts, source bundles, review invalidation, and attention queue.",
        "Saved sources only; compilation never grants authority without human review.",
        ("greytheory.registry", "greytheory.authority.sources"),
    ),
    Capability(
        "scope_compiler",
        "Scope compiler",
        CapabilityStatus.LIVE,
        "Fail-closed programme rules to ScopeContract compilation.",
        "Ambiguity, missing limits, and conflicts block rather than widen scope.",
        ("greytheory.authority.compiler",),
    ),
    Capability(
        "execution_gate",
        "Execution gate",
        CapabilityStatus.LIVE,
        "Deterministic authority, scope, approval, posture, and kill-switch decisions.",
        "A decision is permission for one bound action, not a reusable grant.",
        ("greytheory.authority.gate",),
    ),
    Capability(
        "operator_approvals",
        "Operator approvals",
        CapabilityStatus.LIVE,
        "Bound, expiring, single-use local and ChaseOS approval stores.",
        "The explicit one-provider integration protocol remains open.",
        ("greytheory.authority.approvals", "Docs/decisions/ADR-0003-one-approval-provider.md"),
    ),
    Capability(
        "audit_log",
        "Audit log",
        CapabilityStatus.LIVE,
        "Append-only hash-chained local audit records with integrity verification.",
        "Signed external checkpoints are not implemented.",
        ("greytheory.audit",),
    ),
    Capability(
        "evidence_vault",
        "Evidence vault",
        CapabilityStatus.LIVE,
        "Write-once raw evidence, redacted derivatives, manifests, and integrity checks.",
        "Private data must remain outside Git; only redacted artifacts are exportable.",
        ("greytheory.evidence",),
    ),
    Capability(
        "validation_reporting",
        "Validation and reporting",
        CapabilityStatus.LIVE,
        "Validator receipts, Gates B-F, claim-role matrix, findings, and report drafts.",
        "Submission remains a human Gate G action and is not implemented as automation.",
        ("greytheory.validation", "greytheory.validators", "greytheory.report"),
    ),
    Capability(
        "research_domain",
        "Research workspace",
        CapabilityStatus.LIVE,
        "Structured workspaces, sessions, assets, hypotheses, experiments, receipts, and lessons.",
        "Private runtime state is stored outside the repository.",
        ("greytheory.research",),
    ),
    Capability(
        "hypothesis_ranking",
        "Hypothesis ranking",
        CapabilityStatus.LIVE,
        "Transparent nine-factor ordinal research queue with integrity checks.",
        "Scores are decision support, never probability, proof, severity, or authority.",
        ("greytheory.hypothesis",),
    ),
    Capability(
        "lane_1_dependency",
        "Lane 1 - dependency correlation",
        CapabilityStatus.LIVE,
        "Matches local dependency manifests against imported local OSV records.",
        "Static and offline; a match is not proof that a deployed target is vulnerable.",
        ("greytheory.signal.lanes.dependency_manifest", "greytheory.advisories"),
    ),
    Capability(
        "lane_2_exposure",
        "Lane 2 - local-tree exposure",
        CapabilityStatus.LIVE,
        "Reviews local files for bounded credential, backup, source-map, and VCS indicators.",
        "Static and offline; presence in a tree is not proof of network reachability.",
        ("greytheory.signal.lanes.exposure",),
    ),
    Capability(
        "lane_3_web",
        "Lane 3 - web observation",
        CapabilityStatus.UNAVAILABLE,
        "No web collector is shipped.",
        "Requires a separately governed network broker and a posture above LOCAL_FIXTURE.",
        ("Docs/roadmap.md",),
    ),
    Capability(
        "lane_4_agent_config",
        "Lane 4 - agent configuration",
        CapabilityStatus.LIVE,
        "Reviews local agent and MCP configuration for unsafe authority shapes.",
        "Static and offline; it sends no prompt and invokes no model or tool.",
        ("greytheory.signal.lanes.agent_config",),
    ),
    Capability(
        "learning_core",
        "Learning catalogue and mastery",
        CapabilityStatus.LIVE,
        "Twelve versioned cards, synthetic fixtures, skill graph, and evidence-bound mastery records.",
        "Synthetic fixture completion never awards human mastery automatically.",
        ("greytheory.learning",),
    ),
    Capability(
        "guided_learning",
        "Guided learning orchestration",
        CapabilityStatus.PARTIAL,
        "Deterministic recommendations, prerequisite routing, transparent adaptive review intervals, standard/assisted/transfer tracks, staged journeys, reflection, private persistence, CLI flow, and workbench snapshot/command integration are live.",
        "Assistance cannot evidence mastery above assisted; transfer requires independent test/prove foundations plus distinct-context evidence. One Case Pack is ready; broader ready curricula and a governed model-backed coach remain open.",
        (
            "greytheory.learning.journey",
            "Docs/decisions/ADR-0017-transparent-adaptive-learning-tracks.md",
            "Docs/roadmap.md",
        ),
    ),
    Capability(
        "model_gateway",
        "Model gateway",
        CapabilityStatus.LIVE,
        "Governed roles, classification, citations, budgets, provenance, and adversarial evaluation.",
        "The core ships only a deterministic local provider; no network provider is configured.",
        ("greytheory.models", "Docs/decisions/ADR-0009-model-gateway-and-fetcher-boundaries.md"),
    ),
    Capability(
        "scope_watch_offline",
        "Scope Watch - offline comparison",
        CapabilityStatus.LIVE,
        "Compares captured local programme sources and invalidates review on change or removal.",
        "It accepts only the exact LocalSourceFetcher and performs no network fetch.",
        ("greytheory.scopewatch",),
    ),
    Capability(
        "scope_watch_collector",
        "Scope Watch - governed collector",
        CapabilityStatus.UNAVAILABLE,
        "No external source collector is shipped.",
        "A future out-of-process worker must capture immutable bytes under broker authority.",
        ("Docs/decisions/ADR-0009-model-gateway-and-fetcher-boundaries.md",),
    ),
    Capability(
        "dashboard_read_model",
        "Dashboard read model",
        CapabilityStatus.LIVE,
        "Text, JSON, and self-contained HTML status rendering.",
        "It is a static export, not an interactive application workbench.",
        ("greytheory.dashboard",),
    ),
    Capability(
        "workbench_application_service",
        "Workbench application service",
        CapabilityStatus.PARTIAL,
        "Versioned snapshots assemble programmes, learning, research, hypotheses, evidence, reports, approvals, audit readiness, and capability truth; bounded learning, research planning, fixture action intent, human mastery assessment, revisioned private report authoring, persisted Gates B-F validation, exact-fixture claim assembly, next-state internal lifecycle, and redacted export are live.",
        "The service remains transport-neutral; report authority, asset, finding state, claims, receipts, and claim matrix are server-owned, claim assembly is limited to the exact two-account fixture and stored evidence, lifecycle never crosses report_ready, every handler is non-executing, export never submits, and posture above LOCAL_FIXTURE is structurally rejected.",
        ("greytheory_app", "Docs/workbench-architecture.md"),
    ),
    Capability(
        "local_workbench_transport",
        "Local workbench transport",
        CapabilityStatus.PARTIAL,
        "Private runtime assembly, strict versioned command decoding, authenticated numeric-loopback JSON snapshots/commands, bundled same-origin UI, Windows-first launch, and current-user shortcut/restart/upgrade/runtime-recovery acceptance are live.",
        "Only exact local loopback is admitted; cross-origin writes and target clients remain absent. Whole-application first-entry keyboard traversal, a genuinely separate Windows-account run, signing, and uninstall acceptance remain open.",
        (
            "greytheory_local",
            "Docs/decisions/ADR-0012-authenticated-numeric-loopback-workbench.md",
        ),
    ),
    Capability(
        "graphical_workbench",
        "Graphical workbench",
        CapabilityStatus.PARTIAL,
        "Guided Mission Control provides thirteen working journeys, 24 interactive trajectory lessons, topic-owned roadmaps, three versioned Case Packs, a Demo Suite, and same-origin persisted learning commands.",
        "One Case Pack is ready locally. Comprehensive first-entry keyboard acceptance, governed coach conversation, broader ready curricula, separate-account/signing acceptance, and external intelligence remain open; no live-target action is exposed.",
        ("workbench_ui", "Docs/workbench-architecture.md"),
    ),
    Capability(
        "local_fixture_executor",
        "Local fixture executor",
        CapabilityStatus.PARTIAL,
        "One bounded in-memory two-account action path is gate-bound and receipt-producing.",
        "It is not a general process broker, network broker, or live collector.",
        ("greytheory.vertical_slice",),
    ),
    Capability(
        "passive_broker_foundation",
        "Passive broker foundation",
        CapabilityStatus.PARTIAL,
        "Offline passive-head-v1 contracts provide audit-bound signed tickets, canonical HTTPS and public-address policy, default-engaged kill switch, exact-once replay storage, ticket-bound X25519/ChaCha20-Poly1305 capture envelopes, audited KEK-wrapped recipient provisioning/rotation/revocation/decryption, and signed receipt metadata.",
        "An owned-process broker/worker assembly keeps signing keys, replay state, kill-switch authority, private capture keys, and research data out of the worker. Full Ubuntu 24.04 no-route and exact-address/port default-drop nftables local-fixture acceptance passes. A Windows CurrentUser DPAPI root-KEK candidate passes same-profile restart and protected-copy recovery, but operator approval, ACL hardening, independent recovery, image-bound durable egress, a hardened image, VM/VPS acceptance, and every target action remain unverified or unavailable; PASSIVE_HTTP remains unavailable.",
        (
            "greytheory_broker",
            "Docs/decisions/ADR-0011-dark-passive-broker-foundation.md",
            "Docs/decisions/ADR-0013-passive-capture-encryption-and-key-lifecycle.md",
        ),
    ),
    Capability(
        "windows_dpapi_root_kek_candidate",
        "Windows root-key provider candidate",
        CapabilityStatus.PARTIAL,
        "An operator-side CurrentUser DPAPI provider protects a random 32-byte root KEK with UI forbidden, audited provision/lease operations, strict records, and a short-lived zeroing lease. Same-profile restart and protected-copy recovery pass on Windows.",
        "This is candidate host proof only. Windows ACL hardening, a profile/system backup procedure, recovery independent of the same account/profile, and explicit operator approval remain open. The root KEK never enters the Ubuntu worker and no posture changes.",
        (
            "greytheory_broker.os_secrets",
            "Docs/decisions/ADR-0019-windows-dpapi-root-kek-candidate.md",
        ),
    ),
    Capability(
        "passive_adapter_contract",
        "Passive adapter conformance contract",
        CapabilityStatus.PARTIAL,
        "A network-free contract plus trusted parent assembly orchestrate one typed complete DNS result through a broker address recheck into one full-request-digest-bound direct worker HEAD, then strictly parse, encrypt, and seal completed or stopped receipts.",
        "The two-phase owned-process assembly and identity/lifecycle controls pass. The complete Ubuntu 24.04 no-route service path passes, as does the namespace-lifetime exact-egress candidate. No reproducible image binding, scheduler, VPS, programme action, or posture route exists; PASSIVE_HTTP remains unavailable.",
        (
            "greytheory_worker_contract",
            "Docs/decisions/ADR-0014-network-free-passive-adapter-contract.md",
        ),
    ),
    Capability(
        "passive_worker_primitives",
        "Passive worker OS primitives",
        CapabilityStatus.PARTIAL,
        "The worker package implements the cancellable resolver and direct-TLS primitives plus a capped two-command service. On Linux the outer worker starts from a clean fork server and only the scrubbed authority-free worker forks its resolver; evidence is refused unless Linux is non-root, capability-empty, and no-new-privileges.",
        "Ubuntu 24.04 WSL2 now proves the full owned service path and a namespace-lifetime nftables candidate: default-drop input/forward/output, one exact synthetic address/port, denied address/port/IPv6 probes, and denied unprivileged route/firewall mutation. The policy is not yet bound to a reproducible hardened image; scheduler and posture route remain unverified or unimplemented.",
        (
            "greytheory_worker",
            "Docs/decisions/ADR-0015-unlaunched-passive-worker-primitives.md",
        ),
    ),
    Capability(
        "passive_http_worker",
        "Passive HTTP worker",
        CapabilityStatus.UNAVAILABLE,
        "A dark owned-process assembly, accepted Ubuntu no-route/full-service fixture, namespace-lifetime exact-egress candidate, and same-profile Windows DPAPI key-provider candidate exist, but there is no approved provider/recovery procedure, no image-bound durable egress, no hardened image, no launcher or scheduler, no programme route, and no passive target action.",
        "PASSIVE_HTTP remains dark until full host/image/egress/secret-provider controls, one reviewed programme, sustained operation, and explicit operator posture approval are proven.",
        (
            "Docs/roadmap.md",
            "THREAT_MODEL.md",
            "Docs/decisions/ADR-0011-dark-passive-broker-foundation.md",
        ),
    ),
)


_BY_ID = {capability.id: capability for capability in CAPABILITIES}
if len(_BY_ID) != len(CAPABILITIES):  # pragma: no cover - import-time invariant
    raise RuntimeError("capability ids must be unique")


def capability(capability_id: str) -> Capability:
    """Return one capability by stable id."""

    try:
        return _BY_ID[capability_id]
    except KeyError as exc:
        raise KeyError(f"unknown capability: {capability_id}") from exc


def capabilities_with_status(status: CapabilityStatus) -> tuple[Capability, ...]:
    """Return capabilities in stable display order for a truth state."""

    return tuple(item for item in CAPABILITIES if item.status is status)


__all__ = [
    "CAPABILITIES",
    "Capability",
    "CapabilityStatus",
    "capabilities_with_status",
    "capability",
]
