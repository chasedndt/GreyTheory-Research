"""Trusted broker-side assembly for one owned passive worker process."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from greytheory_broker import (
    BrokerKillSwitch,
    CaptureRecipient,
    MessageSigner,
    MessageVerifier,
    PassiveBrokerSession,
    SignedPassiveTicket,
    TicketReplayLedger,
)
from greytheory_worker.service import (
    WORKER_ID,
    WORKER_VERSION,
    SpawnedWorkerClient,
    WorkerProcessEvidence,
    WorkerServiceError,
)
from greytheory_worker_contract import PassiveAdapterResult, PassiveHeadAdapter


class WorkerClientFactory(Protocol):
    def __call__(self, **kwargs: Any) -> SpawnedWorkerClient: ...


@dataclass(frozen=True)
class PassiveWorkerRunResult:
    adapter: PassiveAdapterResult
    worker: WorkerProcessEvidence


class PassiveWorkerAssembly:
    """Keep broker authority local while one owned worker performs the I/O."""

    def __init__(
        self,
        *,
        ticket_verifier: MessageVerifier,
        receipt_signer: MessageSigner,
        ledger: TicketReplayLedger,
        kill_switch: BrokerKillSwitch,
        ca_file: str | Path,
        clock: Callable[[], datetime],
        monotonic: Callable[[], float] = time.monotonic,
        worker_factory: WorkerClientFactory = SpawnedWorkerClient,
    ) -> None:
        self.ticket_verifier = ticket_verifier
        self.receipt_signer = receipt_signer
        self.ledger = ledger
        self.kill_switch = kill_switch
        self.ca_file = Path(ca_file).expanduser().resolve()
        self.clock = clock
        self.monotonic = monotonic
        self.worker_factory = worker_factory

    def run(
        self,
        *,
        ticket: SignedPassiveTicket,
        recipient: CaptureRecipient,
    ) -> PassiveWorkerRunResult:
        session = PassiveBrokerSession.begin(
            ticket=ticket,
            method=ticket.payload.method.value,
            url=ticket.payload.canonical_url,
            ticket_verifier=self.ticket_verifier,
            receipt_signer=self.receipt_signer,
            ledger=self.ledger,
            kill_switch=self.kill_switch,
            worker_id=WORKER_ID,
            worker_version=WORKER_VERSION,
            clock=self.clock,
        )
        with self.worker_factory(
            ca_file=self.ca_file,
            monotonic=self.monotonic,
        ) as worker:
            adapter = PassiveHeadAdapter(
                resolver=worker,
                transport=worker,
                monotonic=self.monotonic,
            ).run(session=session, recipient=recipient)
            evidence = worker.evidence
        if (
            adapter.receipt.payload.worker_id != evidence.identity.worker_id
            or adapter.receipt.payload.worker_version
            != evidence.identity.worker_version
        ):
            raise WorkerServiceError(
                "signed receipt worker identity does not match process evidence"
            )
        return PassiveWorkerRunResult(adapter=adapter, worker=evidence)


__all__ = [
    "PassiveWorkerAssembly",
    "PassiveWorkerRunResult",
    "WorkerClientFactory",
]
