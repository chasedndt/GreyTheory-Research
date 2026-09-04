"""Gate-bound local execution for structured research action requests."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from greytheory.authority.gate import Decision, Gate
from greytheory.authority.scope import ScopeContract
from greytheory.lab.two_account import FixtureAction, FixtureResponse, TwoAccountFixture
from greytheory.provenance import Claim, Tag
from greytheory.research.domain import ActionReceipt, EffectBudget
from greytheory.research.store import ResearchStore
from greytheory.signal.contract import RawSignal, SignalLevel


@dataclass(frozen=True)
class ExecutionAttempt:
    decision: Decision
    receipt: ActionReceipt | None
    response: FixtureResponse | None
    observation: RawSignal | None


class LocalActionExecutor:
    """The only supported route from a research ActionRequest to the fixture."""

    worker_id = "local-two-account-worker"
    tool_version = "1.0.0"

    def __init__(
        self,
        *,
        research: ResearchStore,
        gate: Gate,
        contract: ScopeContract,
        fixture: TwoAccountFixture,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.research = research
        self.gate = gate
        self.contract = contract
        self.fixture = fixture
        self._clock = clock
        self._ticket_ordinal = 0

    def execute(self, workspace_id: str, request_id: str) -> ExecutionAttempt:
        snapshot = self.research.snapshot(workspace_id)
        request = snapshot.action_requests[request_id]
        asset = snapshot.assets[request.target_asset_id]
        access = request.to_access_request(asset, actor=self.worker_id)
        before = self.fixture.action_count
        decision = self.gate.evaluate(self.contract, access)
        if not decision.allowed:
            if self.fixture.action_count != before:
                raise RuntimeError("denied gate decision changed fixture state")
            return ExecutionAttempt(decision, None, None, None)

        if decision.audit_seq is None or request.identity_id is None:
            raise RuntimeError("allowed local execution lacks an audited decision or identity")
        self._ticket_ordinal += 1
        token_material = json.dumps(
            {
                "request_id": request.id,
                "gate_seq": decision.audit_seq,
                "ordinal": self._ticket_ordinal,
            },
            sort_keys=True,
        ).encode("utf-8")
        ticket = FixtureAction(
            token=hashlib.sha256(token_material).hexdigest(),
            request_id=request.id,
            gate_decision_ref=f"audit:{decision.audit_seq}",
            action_type=request.action_type,
            identity_id=request.identity_id,
            target_identifier=asset.canonical_identifier,
        )
        started = self._clock()
        response = self.fixture._execute(ticket, capability=self.fixture._capability)
        ended = self._clock()
        output_hash = hashlib.sha256(response.body).hexdigest()
        receipt = ActionReceipt.from_execution(
            id=f"receipt-{request.id}",
            request=request,
            asset=asset,
            decision=decision,
            worker=self.worker_id,
            tool_version=self.tool_version,
            started_at=started,
            ended_at=ended,
            request_count=1,
            response_metadata={
                "status_code": response.status_code,
                "content_type": "application/json",
                "fixture_id": self.fixture.fixture_id,
            },
            output_hashes=(output_hash,),
            effects=EffectBudget.from_mapping({"reads": 1}),
        )
        self.research.record_action_receipt(receipt, actor=self.worker_id)
        if self.fixture.action_count != before + 1:
            raise RuntimeError("fixture execution and receipt counts diverged")
        observation = RawSignal(
            id=f"observation-{request.id}",
            lane=3,
            asset=asset.canonical_identifier,
            kind="local_authorization_response",
            title="Controlled cross-owner object read in local fixture",
            level=SignalLevel.CONTEXTUAL,
            claims=[
                Claim(
                    text=(
                        f"The local fixture returned HTTP {response.status_code} for "
                        f"{request.identity_id} reading {asset.canonical_identifier}."
                    ),
                    tag=Tag.OBSERVED,
                    source=self.worker_id,
                )
            ],
            detail={
                "action_receipt_ref": receipt.id,
                "response_sha256": output_hash,
            },
            authority_ref=decision.authority_ref or "",
            observed_at=ended,
        )
        return ExecutionAttempt(decision, receipt, response, observation)


__all__ = ["ExecutionAttempt", "LocalActionExecutor"]
