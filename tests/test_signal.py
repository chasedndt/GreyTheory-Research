"""The Signal Plane: collectors observe, and cannot reach past their grant."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.gate import AuthorityLevel, Gate
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeContract,
)
from greytheory.findings import Taxonomy
from greytheory.provenance import Tag
from greytheory.signal import (
    LaneContext,
    LaneContextError,
    LaneRefused,
    LaneSpec,
    RawSignal,
    SignalLevel,
    observed,
    run_lane,
)
from greytheory.signal.lanes import AgentConfigLane, DependencyManifestLane
from greytheory.signal.lanes.dependency_manifest import in_range, parse_version

NOW = datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)
LAB = Path(__file__).resolve().parent.parent / "fixtures" / "lab"


@pytest.fixture
def audit(tmp_path):
    return AuditLog(tmp_path / "audit.jsonl")


@pytest.fixture
def gate(audit):
    return Gate(audit, clock=lambda: NOW)


def contract(*assets: str) -> ScopeContract:
    return ScopeContract(
        id="s",
        programme_id="lab",
        verified_at=NOW,
        status=ContractStatus.VERIFIED,
        assets_in_scope=[AssetPattern(PatternType.EXACT, a) for a in assets],
        max_authority="LOCAL_FIXTURE",
        human_reviewed=True,
    )


class NetworkLane:
    spec = LaneSpec(
        id="bad",
        lane=3,
        title="wants the network",
        requires_authority=AuthorityLevel.PASSIVE_HTTP,
        network=True,
    )

    def collect(self, context):  # pragma: no cover - must never run
        raise AssertionError("a network lane must not execute in the core package")


class ForgingLane:
    spec = LaneSpec(
        id="forger",
        lane=4,
        title="claims its own authority",
        requires_authority=AuthorityLevel.LOCAL_FIXTURE,
    )

    def collect(self, context):
        return [
            RawSignal(
                id="s1",
                lane=4,
                asset=context.asset,
                kind="test",
                title="forged",
                level=SignalLevel.INFORMATIONAL,
                authority_ref="i-made-this-up",
            )
        ]


class EscapingLane:
    spec = LaneSpec(
        id="escaper",
        lane=4,
        title="reaches outside its root",
        requires_authority=AuthorityLevel.LOCAL_FIXTURE,
    )

    def collect(self, context):
        context.read_text("../../../etc/passwd")
        return []


class TestLaneContext:
    def test_reads_within_the_root(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
        context = LaneContext(asset="x", root=tmp_path, authority_ref="ref")
        assert context.read_text("a.txt") == "hello"

    def test_refuses_to_read_outside_the_root(self, tmp_path):
        (tmp_path / "inside").mkdir()
        context = LaneContext(asset="x", root=tmp_path / "inside", authority_ref="ref")
        with pytest.raises(LaneContextError, match="outside the granted root"):
            context.read_text("../secret.txt")

    def test_iter_files_yields_relative_paths_only(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "a.json").write_text("{}", encoding="utf-8")
        context = LaneContext(asset="x", root=tmp_path, authority_ref="ref")
        paths = context.iter_files("**/*.json")
        assert paths == [Path("sub/a.json")]
        assert not any(p.is_absolute() for p in paths)

    def test_a_missing_root_is_an_error(self, tmp_path):
        with pytest.raises(LaneContextError, match="not a directory"):
            LaneContext(asset="x", root=tmp_path / "nope", authority_ref="ref")


class TestRunnerAuthority:
    def test_a_denied_target_never_runs_the_lane(self, gate, tmp_path):
        run = run_lane(
            AgentConfigLane(),
            targets={"not-in-scope": tmp_path},
            gate=gate,
            contract=contract("something-else"),
            actor="chase",
            clock=lambda: NOW,
        )
        assert run.signals == []
        assert run.skipped[0].reason == "asset_unresolved"

    def test_no_contract_denies_everything(self, gate, tmp_path):
        run = run_lane(
            AgentConfigLane(),
            targets={"anything": tmp_path},
            gate=gate,
            contract=None,
            actor="chase",
            clock=lambda: NOW,
        )
        assert run.skipped[0].reason == "no_contract"

    def test_network_lanes_are_refused_outright(self, gate, tmp_path):
        with pytest.raises(LaneRefused, match="cannot run in the core package"):
            run_lane(
                NetworkLane(),
                targets={"x": tmp_path},
                gate=gate,
                contract=contract("x"),
                actor="chase",
            )

    def test_a_lane_cannot_forge_its_authority_reference(self, gate, tmp_path):
        run = run_lane(
            ForgingLane(),
            targets={"x": tmp_path},
            gate=gate,
            contract=contract("x"),
            actor="chase",
            clock=lambda: NOW,
        )
        signal = run.signals[0]
        assert signal.authority_ref != "i-made-this-up"
        assert signal.authority_ref == contract("x").fingerprint()

    def test_a_lane_escaping_its_root_fails_loudly(self, gate, tmp_path):
        run = run_lane(
            EscapingLane(),
            targets={"x": tmp_path},
            gate=gate,
            contract=contract("x"),
            actor="chase",
            clock=lambda: NOW,
        )
        assert run.signals == []
        assert "LaneContextError" in run.failed[0].error

    def test_partial_runs_record_what_was_skipped(self, gate, tmp_path):
        run = run_lane(
            AgentConfigLane(),
            targets={"allowed": tmp_path, "denied": tmp_path},
            gate=gate,
            contract=contract("allowed"),
            actor="chase",
            clock=lambda: NOW,
        )
        # A run that quietly covered half its targets would be worse than one
        # that failed.
        assert len(run.outcomes) == 2
        assert [o.asset for o in run.skipped] == ["denied"]

    def test_the_run_is_audited(self, gate, audit, tmp_path):
        run_lane(
            AgentConfigLane(),
            targets={"x": tmp_path},
            gate=gate,
            contract=contract("x"),
            actor="chase",
            audit=audit,
            clock=lambda: NOW,
        )
        actions = [r.action for r in audit.records()]
        assert "lane.run" in actions
        audit.verify()


class TestSignalLimits:
    def test_a_signal_cannot_exceed_contextual(self):
        assert {level.value for level in SignalLevel} == {
            "informational",
            "contextual",
        }

    def test_a_signal_without_authority_cannot_become_a_finding(self):
        signal = RawSignal(
            id="s",
            lane=4,
            asset="x",
            kind="k",
            title="t",
            level=SignalLevel.INFORMATIONAL,
        )
        with pytest.raises(ValueError, match="not produced through"):
            signal.to_finding("f1")

    def test_a_contextual_signal_lifts_to_a_contextual_finding(self):
        signal = RawSignal(
            id="s",
            lane=4,
            asset="x",
            kind="k",
            title="t",
            level=SignalLevel.CONTEXTUAL,
            claims=[observed("saw it", "lane")],
            authority_ref="ref",
        )
        finding = signal.to_finding("f1")
        assert finding.state is Taxonomy.CONTEXTUAL
        assert finding.authority_ref == "ref"


class TestAgentConfigLane:
    def run_on(self, gate, directory: Path):
        return run_lane(
            AgentConfigLane(),
            targets={"lab": directory},
            gate=gate,
            contract=contract("lab"),
            actor="chase",
            clock=lambda: NOW,
        )

    def test_finds_nothing_in_a_clean_configuration(self, gate):
        assert self.run_on(gate, LAB / "clean-agent").signals == []

    def test_detects_an_ungated_consequential_tool(self, gate):
        kinds = {s.kind for s in self.run_on(gate, LAB / "vulnerable-agent").signals}
        assert "tool_without_approval_gate" in kinds

    def test_detects_a_wildcard_permission(self, gate):
        signals = self.run_on(gate, LAB / "vulnerable-agent").signals
        wildcard = [s for s in signals if s.kind == "wildcard_tool_permission"]
        assert wildcard and wildcard[0].detail["tool"] == "delete_record"

    def test_detects_a_literal_secret_but_does_not_record_it(self, gate):
        signals = self.run_on(gate, LAB / "vulnerable-agent").signals
        secrets = [s for s in signals if s.kind == "inline_secret_reference"]
        assert secrets
        # The value must never appear in the signal. Recording it would put a
        # live credential into the evidence trail.
        blob = str(secrets[0].to_dict())
        assert "sk-live" not in blob
        assert secrets[0].detail["value_length"] > 12

    def test_an_env_reference_is_not_a_literal_secret(self, gate):
        signals = self.run_on(gate, LAB / "vulnerable-agent").signals
        paths = {
            s.detail.get("json_path", "")
            for s in signals
            if s.kind == "inline_secret_reference"
        }
        assert not any("vault" in p for p in paths)

    def test_detects_unrestricted_egress(self, gate):
        kinds = {s.kind for s in self.run_on(gate, LAB / "vulnerable-agent").signals}
        assert "unrestricted_egress" in kinds

    def test_detects_plaintext_transport_to_a_non_loopback_host(self, gate):
        signals = self.run_on(gate, LAB / "vulnerable-agent").signals
        assert any(s.kind == "plaintext_transport" for s in signals)

    def test_detects_the_composite_injection_path(self, gate):
        # Neither half is a finding alone, which is why a per-key scanner
        # never sees it.
        signals = self.run_on(gate, LAB / "vulnerable-agent").signals
        composite = [
            s for s in signals if s.kind == "untrusted_content_reaches_ungated_action"
        ]
        assert composite
        assert "fetch_web_page" in composite[0].detail["fetchers"]
        assert "delete_record" in composite[0].detail["ungated"]

    def test_every_signal_stays_at_contextual(self, gate):
        signals = self.run_on(gate, LAB / "vulnerable-agent").signals
        assert all(s.level is SignalLevel.CONTEXTUAL for s in signals)

    def test_claims_separate_what_was_checked_from_what_was_not(self, gate):
        signals = self.run_on(gate, LAB / "vulnerable-agent").signals
        gated = next(s for s in signals if s.kind == "tool_without_approval_gate")
        tags = {c.tag for c in gated.claims}
        assert Tag.CHECKED in tags
        assert Tag.OBSERVED in tags
        assert Tag.INFERRED not in tags


class TestDependencyManifestLane:
    def test_version_parsing_and_ranges(self):
        assert parse_version("1.2.3") == (1, 2, 3)
        assert parse_version("2.0.0-rc1") == (2, 0, 0)
        assert in_range("1.2.3", "1.0.0", "1.3.0")
        assert not in_range("1.3.0", "1.0.0", "1.3.0")  # fixed is exclusive
        assert not in_range("0.9.0", "1.0.0", "1.3.0")

    def test_matches_only_versions_inside_the_advisory_range(self, gate):
        run = run_lane(
            DependencyManifestLane(),
            targets={"lab": LAB / "vulnerable-agent"},
            gate=gate,
            contract=contract("lab"),
            actor="chase",
            clock=lambda: NOW,
        )
        packages = {s.detail["package"] for s in run.signals}
        assert packages == {"examplelib"}  # safelib 4.0.0 is outside its range

    def test_the_title_says_matches_not_is_vulnerable(self, gate):
        run = run_lane(
            DependencyManifestLane(),
            targets={"lab": LAB / "vulnerable-agent"},
            gate=gate,
            contract=contract("lab"),
            actor="chase",
            clock=lambda: NOW,
        )
        title = run.signals[0].title
        assert "matches advisory" in title
        assert "vulnerable" not in title.lower()

    def test_no_advisories_means_no_signals(self, gate, tmp_path):
        (tmp_path / "requirements.txt").write_text("examplelib==1.2.3", encoding="utf-8")
        run = run_lane(
            DependencyManifestLane(),
            targets={"lab": tmp_path},
            gate=gate,
            contract=contract("lab"),
            actor="chase",
            clock=lambda: NOW,
        )
        assert run.signals == []
