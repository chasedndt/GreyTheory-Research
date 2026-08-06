"""The ledger: every hour counts, and no forecast before there is data."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from greytheory.audit import AuditLog
from greytheory.ledger import (
    Expense,
    InsufficientData,
    Ledger,
    LedgerError,
    Payout,
    Session,
    SessionKind,
    TriageEvent,
    TriageOutcome,
    resolve_ledger_root,
)

NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "ledger", clock=lambda: NOW)


def session(ledger, minutes=60, kind=SessionKind.HUNT, index=0):
    return ledger.record_session(
        Session(
            id=f"s{index}",
            kind=kind,
            minutes=minutes,
            started_at=NOW - timedelta(days=index),
        )
    )


def payout(ledger, gross="1000", currency="GBP", index=0, months_ago=0, **kw):
    received = NOW - timedelta(days=30 * months_ago)
    return ledger.record_payout(
        Payout(
            id=f"p{index}",
            finding_id=f"f{index}",
            programme_id="acme",
            gross=Decimal(gross),
            currency=currency,
            received_at=received,
            **kw,
        )
    )


def triage(ledger, outcome=TriageOutcome.VALID, index=0):
    return ledger.record_triage(
        TriageEvent(
            id=f"t{index}",
            finding_id=f"f{index}",
            programme_id="acme",
            outcome=outcome,
            occurred_at=NOW,
            programme_evidence=f"h1_msg_{index}",
        )
    )


class TestRecording:
    def test_a_session_must_have_taken_time(self):
        with pytest.raises(LedgerError, match="taken some time"):
            Session(id="s", kind=SessionKind.HUNT, minutes=0, started_at=NOW)

    def test_a_triage_outcome_needs_programme_evidence(self):
        # I5 — the system records outcomes, it never asserts them.
        with pytest.raises(LedgerError, match="never asserts them"):
            TriageEvent(
                id="t",
                finding_id="f",
                programme_id="acme",
                outcome=TriageOutcome.VALID,
                occurred_at=NOW,
                programme_evidence="  ",
            )

    def test_the_platform_wording_is_kept_verbatim(self, ledger):
        ledger.record_triage(
            TriageEvent(
                id="t1",
                finding_id="f1",
                programme_id="acme",
                outcome=TriageOutcome.NOT_APPLICABLE,
                occurred_at=NOW,
                platform_label="Informative - Won't Fix",
                programme_evidence="h1_msg_1",
            )
        )
        # Canonical mapping loses nuance; the nuance is what disputes are about.
        assert ledger.triage_events()[0].platform_label == "Informative - Won't Fix"

    def test_records_survive_reopening(self, tmp_path):
        first = Ledger(tmp_path / "l", clock=lambda: NOW)
        session(first)
        payout(first)
        second = Ledger(tmp_path / "l", clock=lambda: NOW)
        assert len(second.sessions()) == 1
        assert len(second.payouts()) == 1

    def test_writes_are_audited(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        ledger = Ledger(tmp_path / "l", audit=audit, clock=lambda: NOW)
        session(ledger)
        payout(ledger)
        assert [r.action for r in audit.records()] == [
            "ledger.session",
            "ledger.payout",
        ]
        audit.verify()


class TestRepositoryGuard:
    def test_refuses_to_sit_in_a_git_working_tree(self, tmp_path):
        (tmp_path / ".git").mkdir()
        with pytest.raises(LedgerError, match="inside the git working tree"):
            Ledger(tmp_path / "ledger")

    def test_can_be_forced(self, tmp_path):
        (tmp_path / ".git").mkdir()
        assert Ledger(tmp_path / "ledger", allow_in_repository=True)

    def test_standalone_default_root(self, monkeypatch):
        monkeypatch.delenv("GREYTHEORY_LEDGER_ROOT", raising=False)
        monkeypatch.delenv("CHASEOS_VAULT_ROOT", raising=False)
        assert "greytheory" in str(resolve_ledger_root()).lower()

    def test_chaseos_vault_is_used_when_present(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GREYTHEORY_LEDGER_ROOT", raising=False)
        monkeypatch.setenv("CHASEOS_VAULT_ROOT", str(tmp_path))
        assert resolve_ledger_root() == tmp_path / "07_LOGS" / "greytheory-ledger"


class TestMetrics:
    def test_hours_are_totalled_across_every_kind(self, ledger):
        session(ledger, 120, SessionKind.STUDY, 0)
        session(ledger, 60, SessionKind.HUNT, 1)
        session(ledger, 30, SessionKind.REPORT, 2)
        metrics = ledger.metrics()
        assert metrics.total_hours == Decimal("3.5")
        assert metrics.hours_by_kind["study"] == Decimal("2")

    def test_effective_hourly_divides_by_every_tracked_hour(self, ledger):
        # The whole point of I6. Ten hours of study, one hour of hunting, one
        # payout -- the rate is over eleven hours, not one.
        session(ledger, 600, SessionKind.STUDY, 0)
        session(ledger, 60, SessionKind.HUNT, 1)
        payout(ledger, "1100")
        assert ledger.metrics().effective_hourly == Decimal("100")

    def test_unpaid_hours_drag_the_rate_down_as_they_should(self, ledger):
        session(ledger, 60, SessionKind.HUNT, 0)
        payout(ledger, "100")
        before = ledger.metrics().effective_hourly
        session(ledger, 60, SessionKind.STUDY, 1)
        after = ledger.metrics().effective_hourly
        assert after < before

    def test_no_hours_gives_no_rate_rather_than_a_meaningless_one(self, ledger):
        payout(ledger, "500")
        assert ledger.metrics().effective_hourly is None

    def test_fees_collaboration_and_expenses_reduce_net(self, ledger):
        session(ledger, 60)
        payout(
            ledger,
            "1000",
            fees=Decimal("20"),
            collaboration_share=Decimal("100"),
            tax_provision=Decimal("200"),
        )
        ledger.record_expense(
            Expense(
                id="e1",
                description="Burp licence",
                amount=Decimal("80"),
                currency="GBP",
                incurred_at=NOW,
            )
        )
        metrics = ledger.metrics()
        assert metrics.net_before_tax == Decimal("800")
        assert metrics.net_after_tax_provision == Decimal("600")

    def test_valid_and_duplicate_rates_use_closed_outcomes_only(self, ledger):
        triage(ledger, TriageOutcome.VALID, 0)
        triage(ledger, TriageOutcome.DUPLICATE, 1)
        triage(ledger, TriageOutcome.DUPLICATE, 2)
        triage(ledger, TriageOutcome.SUBMITTED, 3)  # still open, not counted
        metrics = ledger.metrics()
        assert metrics.closed_outcomes == 3
        assert metrics.valid_rate == Decimal(1) / Decimal(3)
        assert metrics.duplicate_rate == Decimal(2) / Decimal(3)

    def test_rates_are_none_before_anything_closes(self, ledger):
        triage(ledger, TriageOutcome.SUBMITTED, 0)
        assert ledger.metrics().valid_rate is None


class TestCurrencySafety:
    def test_other_currencies_are_excluded_not_summed(self, ledger):
        # A total that quietly adds dollars to pounds is worse than no total.
        session(ledger, 60)
        payout(ledger, "1000", "GBP", 0)
        payout(ledger, "1000", "USD", 1)
        metrics = ledger.metrics(currency="GBP")
        assert metrics.gross == Decimal("1000")
        assert metrics.excluded_currencies == {"USD": 1}

    def test_reporting_currency_can_be_switched(self, ledger):
        payout(ledger, "1000", "GBP", 0)
        payout(ledger, "700", "USD", 1)
        assert ledger.metrics(currency="USD").gross == Decimal("700")

    def test_expenses_respect_the_reporting_currency(self, ledger):
        ledger.record_expense(
            Expense("e1", "VPS", Decimal("50"), "USD", NOW)
        )
        metrics = ledger.metrics(currency="GBP")
        assert metrics.expenses == Decimal("0")
        assert metrics.excluded_currencies == {"USD": 1}


class TestForecastRefusal:
    def test_refuses_on_an_empty_ledger(self, ledger):
        with pytest.raises(InsufficientData) as exc:
            ledger.forecast()
        assert len(exc.value.missing) == 4

    def test_the_error_names_exactly_what_is_missing(self, ledger):
        for i in range(20):
            session(ledger, 300, SessionKind.HUNT, i)  # 100 hours, 20 sessions
        with pytest.raises(InsufficientData) as exc:
            ledger.forecast()
        joined = " ".join(exc.value.missing)
        assert "submissions" in joined
        assert "closed triage outcomes" in joined
        assert "tracked hours" not in joined  # that threshold is met

    def test_the_message_tells_you_what_to_plan_on(self, ledger):
        with pytest.raises(InsufficientData, match="plan on zero"):
            ledger.forecast()

    def test_almost_enough_still_refuses(self, ledger):
        # 99 hours is not 100. The threshold is not a suggestion.
        for i in range(20):
            session(ledger, 297, SessionKind.HUNT, i)
        for i in range(5):
            triage(ledger, TriageOutcome.SUBMITTED, i)
            triage(ledger, TriageOutcome.VALID, 100 + i)
        with pytest.raises(InsufficientData) as exc:
            ledger.forecast()
        assert any("tracked hours" in m for m in exc.value.missing)


def stock_for_forecast(ledger, *, payouts=3):
    for i in range(20):
        session(ledger, 300, SessionKind.HUNT, i)
    for i in range(5):
        triage(ledger, TriageOutcome.SUBMITTED, i)
    for i in range(5):
        triage(ledger, TriageOutcome.VALID, 100 + i)
    for i in range(payouts):
        payout(ledger, "500", "GBP", index=i, months_ago=i * 2)


class TestForecast:
    def test_produces_a_distribution_once_thresholds_are_met(self, ledger):
        stock_for_forecast(ledger)
        forecast = ledger.forecast()
        assert forecast.months_observed >= 3
        assert forecast.currency == "GBP"

    def test_months_with_no_payout_are_in_the_distribution(self, ledger):
        # Dropping them is how a zero-income month becomes invisible.
        stock_for_forecast(ledger, payouts=2)
        forecast = ledger.forecast()
        assert forecast.zero_month_probability > 0
        assert Decimal("0") in forecast.monthly_net

    def test_income_concentration_is_reported(self, ledger):
        stock_for_forecast(ledger, payouts=1)
        payout(ledger, "10000", "GBP", index=99, months_ago=1)
        # One payout dominating means the median describes luck, not a rate.
        assert ledger.forecast().income_concentration > Decimal("0.9")

    def test_quartiles_bracket_the_median(self, ledger):
        stock_for_forecast(ledger)
        forecast = ledger.forecast()
        assert forecast.lower_quartile <= forecast.median_monthly_net
        assert forecast.median_monthly_net <= forecast.upper_quartile
