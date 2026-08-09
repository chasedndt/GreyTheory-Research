"""Milestone 4: one complete, deliberately vulnerable local research slice."""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from greytheory.checks import CheckError, CheckReceipt, ValidatorRegistry
from greytheory.cli import main
from greytheory.lab import ExecutionDenied, OwnershipValidator, TwoAccountFixture
from greytheory.learning import CardUpdateProposal, load_builtin_catalogue
from greytheory.provenance import Claim, Tag
from greytheory.vertical_slice import (
    OperatorStatements,
    VerticalSliceError,
    run_local_two_account_slice,
)

NOW = datetime(2026, 8, 9, 15, 0, tzinfo=timezone.utc)


def fixture_statements() -> OperatorStatements:
    return OperatorStatements(
        operator="fixture-human-reviewer",
        kind="test_fixture",
        contract_reviewed=True,
        reproducibility="I ran this acceptance fixture from a clean, newly created local run directory.",
        impact="I confirmed only the bounded confidentiality consequence between two controlled synthetic accounts.",
        duplicate_risk="I reviewed the saved training rules and fixture changelog; residual duplicate risk remains fixture-only.",
    )


def test_complete_two_account_slice_satisfies_every_exit_condition(tmp_path):
    root = tmp_path / "run"
    result = run_local_two_account_slice(
        root, statements=fixture_statements(), clock=lambda: NOW
    )

    assert result.status == "complete"
    assert result.operating_posture == "LOCAL_FIXTURE"
    assert result.finding_state == "report_ready"
    assert result.executed_actions == result.persisted_action_receipts == 1
    assert result.submission_performed is False
    assert result.attestation_kind == "test_fixture"
    assert result.evidence_refs

    workspace = json.loads(
        (root / "research" / result.workspace_id / "workspace.json").read_text()
    )
    assert len(workspace["identities"]) == 2
    assert len(workspace["action_requests"]) == 1
    assert len(workspace["action_receipts"]) == 1
    assert len(workspace["lessons"]) == 1
    assert workspace["sessions"][0]["checked_evidence_refs"]
    assert workspace["sessions"][0]["status"] == "completed"

    report = json.loads((root / "report.json").read_text())
    assert report["claim_matrix"]
    assert all(item["evidence_refs"] for item in report["claim_matrix"])
    assert all(item["claim"]["tag"] in {"observed", "checked", "inferred"} for item in report["claim_matrix"])
    checked = [item for item in report["claim_matrix"] if item["claim"]["tag"] == "checked"]
    assert len(checked) == 1
    assert checked[0]["claim"]["check_ref"] == result.check_receipt_id

    finding = json.loads((root / "finding.json").read_text())
    check_claims = [claim for claim in finding["claims"] if claim["tag"] == "checked"]
    assert len(check_claims) == 1
    assert check_claims[0]["source"].startswith("validator:")
    validation = json.loads((root / "validation.json").read_text())
    assert validation["submission_ready"] is True
    assert all(item["status"] == "pass" for item in validation["results"])

    card = json.loads((root / "vulnerability-card-update.json").read_text())
    assert card["status"] == "proposed"
    assert card["card_id"] == "idor-bola"
    assert card["source_kind"] == "test_fixture"
    assert card["checked_claim_ref"] == result.check_receipt_id
    applied = load_builtin_catalogue().applied_revision(
        CardUpdateProposal.from_dict(card)
    )
    assert applied.version == "1.0.0"
    assert (root / "postmortem.json").is_file()
    assert (root / "result.json").is_file()


def test_fixture_refuses_direct_or_replayed_actions():
    fixture = TwoAccountFixture()
    with pytest.raises(ExecutionDenied, match="one-use ticket"):
        fixture.read_object(
            "identity-user-a", "fixture://two-account/objects/object-user-b"
        )
    assert fixture.action_count == 0


def test_denied_gate_creates_no_action_receipt_or_evidence(tmp_path):
    source = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "lab"
            / "two-account-authorization"
            / "programme.json"
        ).read_text(encoding="utf-8")
    )
    source["prohibited_techniques"].append("object-ownership-check")
    programme = tmp_path / "denied-programme.json"
    programme.write_text(json.dumps(source), encoding="utf-8")
    root = tmp_path / "denied-run"

    with pytest.raises(VerticalSliceError, match="technique_prohibited"):
        run_local_two_account_slice(
            root,
            statements=fixture_statements(),
            programme_path=programme,
            clock=lambda: NOW,
        )

    workspace = json.loads(
        (root / "research" / "workspace-local-two-account" / "workspace.json").read_text()
    )
    assert workspace["action_requests"]
    assert workspace["action_receipts"] == []
    assert not list((root / "evidence" / "raw").rglob("*.*"))
    decisions = [
        json.loads(line)
        for line in (root / "audit.jsonl").read_text().splitlines()
        if line.strip()
    ]
    gate_decisions = [item for item in decisions if item["action"] == "gate.evaluate"]
    assert gate_decisions[-1]["detail"]["allowed"] is False


def test_validator_has_a_reachable_refuted_outcome():
    fixture = TwoAccountFixture(vulnerable=False)
    manifest = fixture.ownership_manifest()
    response = (
        json.dumps(
            {
                "fixture_id": fixture.fixture_id,
                "requester_identity_id": "identity-user-a",
                "status_code": 403,
                "object": None,
                "denial_reason": "object_owner_mismatch",
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()
    registry = ValidatorRegistry(clock=lambda: NOW)
    registry.register(OwnershipValidator())
    receipt = registry.run(
        OwnershipValidator.validator_id,
        inputs=(response, manifest),
        authority_ref="contract",
    )
    assert receipt.actual_outcome == "refuted"
    with pytest.raises(CheckError, match="supported"):
        registry.promote(
            Claim(receipt.exact_assertion, Tag.INFERRED, "model"), receipt
        )


def test_forged_or_modified_receipt_cannot_make_model_output_checked():
    registry = ValidatorRegistry(clock=lambda: NOW)
    registry.register(OwnershipValidator())
    response = b'{"status_code":403,"requester_identity_id":"identity-user-a","object":null}'
    manifest = TwoAccountFixture().ownership_manifest()
    receipt = registry.run(
        OwnershipValidator.validator_id,
        inputs=(response, manifest),
        authority_ref="contract",
    )
    forged = replace(receipt, actual_outcome="supported")
    claim = Claim(receipt.exact_assertion, Tag.INFERRED, "model")
    with pytest.raises(CheckError, match="not issued"):
        registry.promote(claim, forged)

    invented = CheckReceipt(
        id="check_invented",
        validator_id=OwnershipValidator.validator_id,
        validator_version="1.0.0",
        input_artifact_hashes=(hashlib.sha256(b"x").hexdigest(),),
        exact_assertion=OwnershipValidator.exact_assertion,
        possible_outcomes=("supported", "refuted"),
        actual_outcome="supported",
        issued_at=NOW,
        runner_digest=hashlib.sha256(b"validator").hexdigest(),
        authority_ref="contract",
    )
    with pytest.raises(CheckError, match="not issued"):
        registry.promote(claim, invented)


def test_completed_run_root_is_write_once(tmp_path):
    root = tmp_path / "run"
    run_local_two_account_slice(root, statements=fixture_statements(), clock=lambda: NOW)
    with pytest.raises(VerticalSliceError, match="completed result"):
        run_local_two_account_slice(
            root, statements=fixture_statements(), clock=lambda: NOW
        )


def test_cli_runs_the_local_slice_and_never_submits(tmp_path, capsys):
    root = tmp_path / "cli-run"
    assert main(
        [
            "demo",
            "local-two-account",
            "--root",
            str(root),
            "--attestations",
            str(
                Path(__file__).resolve().parents[1]
                / "fixtures"
                / "lab"
                / "two-account-authorization"
                / "test-attestations.json"
            ),
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operating_posture"] == "LOCAL_FIXTURE"
    assert payload["attestation_kind"] == "test_fixture"
    assert payload["submission_performed"] is False


def test_slice_modules_do_not_import_network_clients():
    root = Path(__file__).resolve().parents[1]
    forbidden = {"socket", "requests", "httpx", "urllib", "aiohttp"}
    for relative in (
        "greytheory/execution.py",
        "greytheory/lab/two_account.py",
        "greytheory/vertical_slice.py",
    ):
        tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert not (imported & forbidden)
