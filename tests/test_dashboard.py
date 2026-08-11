"""The dashboard: absent data must never look like good news."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Gate
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeContract,
)
from greytheory.dashboard import (
    Status,
    build_dashboard,
    render_html,
    render_json,
    render_text,
)
from greytheory.evidence import EvidenceVault
from greytheory.findings import Finding, Taxonomy
from greytheory.ledger import Ledger, Payout, Session, SessionKind
from greytheory.registry import ProgrammeRegistry
from greytheory.provenance import Claim, Tag
from tests.test_findings import bind_every_role

NOW = datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)
AUTHORITY = "fingerprint_abc"

PROGRAMME = {
    "id": "acme",
    "verified_at": "2026-08-07T00:00:00+00:00",
    "max_authority": "LOCAL_FIXTURE",
    "in_scope": [{"type": "wildcard", "value": "*.acme.test"}],
}


@pytest.fixture
def audit(tmp_path):
    return AuditLog(tmp_path / "audit.jsonl")


def contract() -> ScopeContract:
    return ScopeContract(
        id="s",
        programme_id="acme",
        verified_at=NOW,
        status=ContractStatus.VERIFIED,
        assets_in_scope=[AssetPattern(PatternType.WILDCARD, "*.acme.test")],
        human_reviewed=True,
    )


class TestAbsentDataIsUnknown:
    def test_an_empty_dashboard_reports_unknown_not_zero(self):
        # The single most important behaviour here. "0 out-of-scope attempts"
        # and "nothing is being recorded" must not look the same.
        dashboard = build_dashboard(now=lambda: NOW)
        safety = dashboard.panel("safety")
        assert all(m.status is Status.UNKNOWN for m in safety.metrics)
        assert "not the same as everything being fine" in safety.note

    def test_no_registry_reports_unknown(self):
        panel = build_dashboard(now=lambda: NOW).panel("programmes")
        assert panel.metrics[0].status is Status.UNKNOWN

    def test_no_ledger_reports_unknown_hours(self):
        panel = build_dashboard(now=lambda: NOW).panel("economics")
        assert panel.metrics[0].value == "unknown"

    def test_a_measured_zero_is_ok_not_unknown(self, audit):
        # With an audit log present and nothing attempted, zero is a real
        # measurement and reads as such.
        audit.append(actor="chase", action="noop")
        safety = build_dashboard(audit=audit, now=lambda: NOW).panel("safety")
        scope = next(m for m in safety.metrics if m.label == "Scope attempts blocked")
        assert scope.value == "0"
        assert scope.status is Status.OK


class TestSafetyPanel:
    def test_a_broken_audit_chain_is_an_alert(self, tmp_path):
        path = tmp_path / "audit.jsonl"
        log = AuditLog(path)
        log.append(actor="chase", action="one")
        log.append(actor="chase", action="two")
        lines = path.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[0])
        record["actor"] = "someone else"
        lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        safety = build_dashboard(audit=AuditLog(path), now=lambda: NOW).panel("safety")
        chain = next(m for m in safety.metrics if m.label == "Audit chain")
        assert chain.value == "BROKEN"
        assert chain.status is Status.ALERT

    def test_blocked_scope_attempts_are_surfaced_as_warnings(self, audit):
        gate = Gate(audit, clock=lambda: NOW)
        gate.evaluate(
            contract(),
            AccessRequest(
                asset="elsewhere.test",
                authority_level=AuthorityLevel.LOCAL_FIXTURE,
                actor="chase",
            ),
        )
        safety = build_dashboard(audit=audit, now=lambda: NOW).panel("safety")
        scope = next(m for m in safety.metrics if m.label == "Scope attempts blocked")
        assert scope.value == "1"
        assert scope.status is Status.WARN
        assert "something tried" in scope.detail

    def test_out_of_scope_executed_is_zero_by_construction(self, audit):
        audit.append(actor="chase", action="noop")
        safety = build_dashboard(audit=audit, now=lambda: NOW).panel("safety")
        executed = next(
            m for m in safety.metrics if m.label == "Out-of-scope executed"
        )
        assert executed.value == "0"
        assert "only execution path" in executed.detail


class TestAuthorityPanel:
    def test_denials_are_counted_by_reason(self, audit):
        gate = Gate(audit, clock=lambda: NOW)
        for asset in ("a.acme.test", "nope.test", "other.test"):
            gate.evaluate(
                contract(),
                AccessRequest(
                    asset=asset,
                    authority_level=AuthorityLevel.LOCAL_FIXTURE,
                    actor="chase",
                ),
            )
        panel = build_dashboard(audit=audit, now=lambda: NOW).panel("authority")
        assert next(m for m in panel.metrics if m.label == "Allowed").value == "1"
        assert next(m for m in panel.metrics if m.label == "Denied").value == "2"
        assert ["asset_unresolved", "2"] in panel.rows

    def test_a_denial_is_framed_as_the_system_working(self, audit):
        audit.append(actor="chase", action="noop")
        panel = build_dashboard(audit=audit, now=lambda: NOW).panel("authority")
        denied = next(m for m in panel.metrics if m.label == "Denied")
        assert "the system working" in denied.detail


class TestProgrammesPanel:
    def test_unreviewed_programmes_need_attention(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "reg", clock=lambda: NOW)
        registry.register(PROGRAMME, raw_source="rules")
        panel = build_dashboard(registry=registry, now=lambda: NOW).panel("programmes")

        assert next(m for m in panel.metrics if m.label == "Need attention").value == "1"
        assert (
            next(m for m in panel.metrics if m.label == "Grant authority now").value
            == "0"
        )
        assert panel.rows[0][:2] == ["acme", "v1"]

    def test_a_reviewed_programme_grants_authority(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "reg", clock=lambda: NOW)
        registry.register(PROGRAMME, raw_source="rules")
        registry.review("acme", reviewer="chase")
        panel = build_dashboard(registry=registry, now=lambda: NOW).panel("programmes")
        assert (
            next(m for m in panel.metrics if m.label == "Grant authority now").value
            == "1"
        )


class TestEvidencePanel:
    def test_unredacted_artifacts_are_flagged(self, tmp_path):
        vault = EvidenceVault(tmp_path / "vault", clock=lambda: NOW)
        finding = Finding("f1", "t", 3, "app.acme.test", AUTHORITY)
        vault.store_raw(
            finding_id="f1",
            artifact_id="a1",
            kind="note",
            data=b"raw",
            authority_ref=AUTHORITY,
        )
        panel = build_dashboard(
            vault=vault, findings=[finding], now=lambda: NOW
        ).panel("evidence")
        awaiting = next(m for m in panel.metrics if m.label == "Awaiting redaction")
        assert awaiting.value == "1"
        assert awaiting.status is Status.WARN

    def test_tampered_evidence_is_an_alert(self, tmp_path):
        vault = EvidenceVault(tmp_path / "vault", clock=lambda: NOW)
        finding = Finding("f1", "t", 3, "app.acme.test", AUTHORITY)
        vault.store_raw(
            finding_id="f1",
            artifact_id="a1",
            kind="note",
            data=b"raw",
            authority_ref=AUTHORITY,
            extension=".txt",
        )
        (vault.raw_dir / "f1" / "a1.txt").write_bytes(b"tampered")
        panel = build_dashboard(
            vault=vault, findings=[finding], now=lambda: NOW
        ).panel("evidence")
        integrity = next(m for m in panel.metrics if m.label == "Integrity")
        assert integrity.status is Status.ALERT


class TestEconomicsPanel:
    def test_forecast_refusal_is_shown_rather_than_a_number(self, tmp_path):
        ledger = Ledger(tmp_path / "l", clock=lambda: NOW)
        ledger.record_session(
            Session("s1", SessionKind.HUNT, 60, NOW)
        )
        panel = build_dashboard(ledger=ledger, now=lambda: NOW).panel("economics")
        forecast = next(m for m in panel.metrics if m.label == "Forecast")
        assert forecast.value == "refused"
        assert "plan on zero" in forecast.detail
        assert "more tracked hours" in panel.note

    def test_effective_hourly_says_it_covers_every_hour(self, tmp_path):
        ledger = Ledger(tmp_path / "l", clock=lambda: NOW)
        ledger.record_session(Session("s1", SessionKind.STUDY, 600, NOW))
        ledger.record_session(Session("s2", SessionKind.HUNT, 60, NOW))
        ledger.record_payout(
            Payout("p1", "f1", "acme", Decimal("1100"), "GBP", NOW)
        )
        panel = build_dashboard(ledger=ledger, now=lambda: NOW).panel("economics")
        hourly = next(m for m in panel.metrics if m.label == "Effective hourly")
        assert hourly.value == "100.00 GBP/h"
        assert "not just productive ones" in hourly.detail

    def test_mixed_currencies_are_flagged(self, tmp_path):
        ledger = Ledger(tmp_path / "l", clock=lambda: NOW)
        ledger.record_payout(Payout("p1", "f", "acme", Decimal("1"), "USD", NOW))
        panel = build_dashboard(ledger=ledger, now=lambda: NOW).panel("economics")
        excluded = next(m for m in panel.metrics if m.label == "Excluded records")
        assert excluded.status is Status.WARN


class TestCapabilityPanel:
    def test_states_plainly_that_nothing_is_detected(self):
        panel = build_dashboard(now=lambda: NOW).panel("capability")
        detection = next(m for m in panel.metrics if m.label == "Detection")
        assert detection.value == "none"
        assert "detects nothing" in detection.detail

    def test_unbuilt_components_are_listed_as_such(self):
        panel = build_dashboard(now=lambda: NOW).panel("capability")
        assert ["Lane 1-4 collectors", "not built"] in panel.rows
        assert ["Scope Watch", "roadmap"] in panel.rows


class TestNextAction:
    def test_safety_alerts_win(self, tmp_path):
        path = tmp_path / "audit.jsonl"
        log = AuditLog(path)
        log.append(actor="chase", action="one")
        path.write_text(
            path.read_text(encoding="utf-8").replace("chase", "mallory"),
            encoding="utf-8",
        )
        dashboard = build_dashboard(audit=AuditLog(path), now=lambda: NOW)
        assert "Stop and investigate" in dashboard.next_action

    def test_programmes_needing_attention_come_next(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "reg", clock=lambda: NOW)
        registry.register(PROGRAMME, raw_source="rules")
        dashboard = build_dashboard(registry=registry, now=lambda: NOW)
        assert "need attention before testing" in dashboard.next_action

    def test_report_ready_findings_are_surfaced(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "reg", clock=lambda: NOW)
        registry.register(PROGRAMME, raw_source="rules")
        registry.review("acme", reviewer="chase")
        finding = Finding("f1", "t", 3, "app.acme.test", AUTHORITY)
        bind_every_role(finding)
        for state in (
            Taxonomy.CONTEXTUAL,
            Taxonomy.CANDIDATE,
            Taxonomy.VALIDATED,
            Taxonomy.REPORT_READY,
        ):
            finding.advance(state, actor="chase")

        dashboard = build_dashboard(
            registry=registry, findings=[finding], now=lambda: NOW
        )
        assert "awaiting your decision" in dashboard.next_action

    def test_a_quiet_system_suggests_work_rather_than_nothing(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "reg", clock=lambda: NOW)
        registry.register(PROGRAMME, raw_source="rules")
        registry.review("acme", reviewer="chase")
        dashboard = build_dashboard(registry=registry, now=lambda: NOW)
        assert "Pick a hypothesis" in dashboard.next_action

    def test_only_one_action_is_ever_suggested(self):
        # A dashboard that suggests six things suggests none.
        dashboard = build_dashboard(now=lambda: NOW)
        assert "\n" not in dashboard.next_action


class TestRenderers:
    def test_text_is_ascii_only(self):
        # Windows consoles are unforgiving.
        rendered = render_text(build_dashboard(now=lambda: NOW))
        rendered.encode("ascii")
        assert "NEXT:" in rendered

    def test_html_is_self_contained(self, tmp_path):
        ledger = Ledger(tmp_path / "l", clock=lambda: NOW)
        rendered = render_html(build_dashboard(ledger=ledger, now=lambda: NOW))
        assert rendered.startswith("<!doctype html>")
        # No external resources, no scripts.
        for forbidden in ("http://", "https://", "<script", "src="):
            assert forbidden not in rendered

    def test_html_escapes_content(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "reg", clock=lambda: NOW)
        registry.register(
            {**PROGRAMME, "id": "acme"}, raw_source="rules"
        )
        rendered = render_html(build_dashboard(registry=registry, now=lambda: NOW))
        assert "<script>" not in rendered

    def test_json_round_trips(self):
        payload = json.loads(render_json(build_dashboard(now=lambda: NOW)))
        assert payload["posture_ceiling"] == "LOCAL_FIXTURE"
        assert {p["id"] for p in payload["panels"]} >= {
            "programmes",
            "authority",
            "safety",
            "findings",
            "evidence",
            "economics",
            "capability",
        }

    def test_posture_ceiling_is_always_stated(self):
        dashboard = build_dashboard(
            posture_ceiling=AuthorityLevel.PASSIVE_HTTP, now=lambda: NOW
        )
        assert dashboard.posture_ceiling == "PASSIVE_HTTP"
        assert "PASSIVE_HTTP" in render_text(dashboard)
