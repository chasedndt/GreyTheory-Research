"""Private local-store assembly for the GreyTheory operator workbench."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from greytheory.audit import AuditLog
from greytheory.authority.approvals import LocalApprovalStore
from greytheory.authority.gate import AuthorityLevel
from greytheory.evidence import EvidenceVault, find_repository_root
from greytheory.learning import (
    FixtureReceiptStore,
    LearningJourneyStore,
    MasteryStore,
    load_builtin_catalogue,
)
from greytheory.registry import ProgrammeRegistry
from greytheory.directory_lookups import DirectoryLookupStore
from greytheory.shortlist import ShortlistStore
from greytheory.models import (
    CoachHistoryStore,
    DataClass,
    LocalTutorProvider,
    ModelGateway,
    ProviderPolicy,
)
from greytheory.report_store import ReportStore
from greytheory.research import ResearchStore
from greytheory_intelligence.credential_cipher import default_credential_cipher
from greytheory_intelligence.platform_credentials import PlatformCredentialStore
from greytheory_app import ReportExportWriter, WorkbenchApplicationService


class LocalRuntimeError(ValueError):
    """Raised when the local workbench runtime would use an unsafe location."""


def resolve_workbench_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the private runtime root without silently using the repository."""

    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    if configured := os.environ.get("GREYTHEORY_WORKBENCH_ROOT"):
        return Path(configured).expanduser().resolve()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return (Path(base) / "GreyTheory" / "workbench").resolve()
        return (
            Path.home() / "AppData" / "Local" / "GreyTheory" / "workbench"
        ).resolve()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return (base / "greytheory" / "workbench").resolve()


def prepare_workbench_root(
    explicit: str | os.PathLike[str] | None = None,
) -> Path:
    root = resolve_workbench_root(explicit)
    repository = find_repository_root(root)
    if repository is not None:
        raise LocalRuntimeError(
            f"workbench runtime data is refused inside the Git worktree at {repository}"
        )
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        # Windows ACL acceptance is a packaging/host proof, not simulated here.
        pass
    return root


@dataclass(frozen=True)
class LocalWorkbenchRuntime:
    """Assembled private stores and their transport-neutral application service."""

    root: Path
    service: WorkbenchApplicationService
    #: Platform credentials the operator enters themselves. Held beside the
    #: service rather than inside it, so a token never reaches the command bus.
    credentials: PlatformCredentialStore | None = None

    @classmethod
    def assemble(
        cls, root: str | os.PathLike[str] | None = None
    ) -> LocalWorkbenchRuntime:
        private_root = prepare_workbench_root(root)
        audit = AuditLog(private_root / "audit" / "audit.jsonl")
        catalogue = load_builtin_catalogue()
        service = WorkbenchApplicationService(
            posture=AuthorityLevel.LOCAL_FIXTURE,
            registry=ProgrammeRegistry(private_root / "programmes", audit=audit),
            shortlist=ShortlistStore(private_root / "shortlist", audit=audit),
            # No connection factory here: in the running application a real
            # request is the point, and it happens only when the operator asks.
            directory_lookups=DirectoryLookupStore(
                private_root / "directory", audit=audit
            ),
            audit=audit,
            research=ResearchStore(private_root / "research", audit=audit),
            mastery=MasteryStore(
                private_root / "learning", catalogue=catalogue, audit=audit
            ),
            journeys=LearningJourneyStore(
                private_root / "learning", catalogue=catalogue, audit=audit
            ),
            fixture_receipts=FixtureReceiptStore(
                private_root / "learning", catalogue=catalogue, audit=audit
            ),
            evidence=EvidenceVault(private_root / "evidence", audit=audit),
            report_store=ReportStore(private_root / "reports", audit=audit),
            report_export_writer=ReportExportWriter(
                private_root / "exports", audit=audit
            ),
            approvals=LocalApprovalStore(),
            coach_history=CoachHistoryStore(private_root / "coach", audit=audit),
            coach_gateway=ModelGateway(
                LocalTutorProvider(),
                ProviderPolicy(
                    "local.tutor",
                    local=True,
                    max_data_class=DataClass.PUBLIC,
                    approved_by="built-in-local-runtime",
                    note="Deterministic network-free tutor; public curriculum only.",
                ),
                audit=audit,
                budget=Decimal("0.01"),
            ),
        )
        return cls(
            private_root,
            service,
            credentials=PlatformCredentialStore(
                private_root / "platform-credentials",
                # None on a host without DPAPI: saving is then refused
                # rather than silently downgraded to plaintext.
                cipher=default_credential_cipher(),
            ),
        )


__all__ = [
    "LocalRuntimeError",
    "LocalWorkbenchRuntime",
    "prepare_workbench_root",
    "resolve_workbench_root",
]
