"""The triage and earnings ledger — including the hours that produced nothing.

Invariant I6 says zero-yield hours are recorded at the same fidelity as
payouts. That sounds like bookkeeping pedantry until you see what happens
without it: divide a bounty by the hours spent on the session that found it and
bug bounty looks like a very good hourly rate. Divide it by every hour spent
studying, reading scope, hunting fruitlessly, writing reports that were
rejected, and arguing with triage, and you get the real number.

A ledger that only counts wins is not a ledger. It is a highlight reel, and it
will talk you into decisions the actual numbers would not support.

So three rules are structural here rather than advisory:

**Effective hourly rate always divides by total tracked hours.** There is no
parameter to change that. Hours are hours.

**Forecasting is refused until there is enough data to forecast from.**
:meth:`Ledger.forecast` raises rather than returning a confident-looking number
built on three data points, and the error names exactly what is missing.

**Mixed currencies are never silently summed.** Metrics take a reporting
currency and report what was excluded, because a total that quietly adds
dollars to pounds is worse than no total.

Money is :class:`decimal.Decimal` throughout. Floats accumulate error, and
this is the one part of the system where the arithmetic is the point.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterator

from greytheory.audit import AuditLog
from greytheory.evidence import find_repository_root

ZERO = Decimal("0")


class SessionKind(str, Enum):
    """Every kind of hour that counts. All of them count."""

    STUDY = "study"
    LAB = "lab"
    PROGRAMME_RESEARCH = "programme_research"
    HUNT = "hunt"
    REPORT = "report"
    TRIAGE = "triage"
    RETEST = "retest"


class TriageOutcome(str, Enum):
    """Canonical outcomes. The platform's own wording is kept alongside."""

    SUBMITTED = "submitted"
    NEEDS_MORE_INFO = "needs_more_info"
    VALID = "valid"
    DUPLICATE = "duplicate"
    INFORMATIVE = "informative"
    NOT_APPLICABLE = "not_applicable"
    OUT_OF_SCOPE = "out_of_scope"


CLOSED_OUTCOMES = {
    TriageOutcome.VALID,
    TriageOutcome.DUPLICATE,
    TriageOutcome.INFORMATIVE,
    TriageOutcome.NOT_APPLICABLE,
    TriageOutcome.OUT_OF_SCOPE,
}

MINIMUM_TRACKED_HOURS = 100
MINIMUM_SESSIONS = 20
MINIMUM_SUBMISSIONS = 5
MINIMUM_CLOSED_OUTCOMES = 5
"""Thresholds below which a personal forecast is not evidence, it is a wish."""


class LedgerError(Exception):
    """Raised when a ledger operation would be unsound."""


class InsufficientData(LedgerError):
    """Raised when a forecast is requested before there is data to forecast from."""

    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(
            "not enough personal data to forecast honestly. Missing:\n  - "
            + "\n  - ".join(missing)
            + "\nUntil then, plan on zero."
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _money(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def resolve_ledger_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Same resolution order as the evidence vault, different subdirectory."""
    if explicit is not None:
        return Path(explicit).expanduser()
    override = os.environ.get("GREYTHEORY_LEDGER_ROOT")
    if override:
        return Path(override).expanduser()
    vault = os.environ.get("CHASEOS_VAULT_ROOT")
    if vault:
        return Path(vault).expanduser() / "07_LOGS" / "greytheory-ledger"
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / "GreyTheory" / "ledger"
        return Path.home() / "AppData" / "Local" / "GreyTheory" / "ledger"
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "greytheory" / "ledger"


@dataclass(frozen=True)
class Session:
    """Time spent. Attributed where possible, counted always."""

    id: str
    kind: SessionKind
    minutes: int
    started_at: datetime
    programme_id: str | None = None
    finding_id: str | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.minutes <= 0:
            raise LedgerError("a session must have taken some time")

    @property
    def hours(self) -> Decimal:
        return Decimal(self.minutes) / Decimal(60)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "minutes": self.minutes,
            "started_at": self.started_at.isoformat(),
            "programme_id": self.programme_id,
            "finding_id": self.finding_id,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        return cls(
            id=data["id"],
            kind=SessionKind(data["kind"]),
            minutes=data["minutes"],
            started_at=_parse_dt(data["started_at"]),
            programme_id=data.get("programme_id"),
            finding_id=data.get("finding_id"),
            note=data.get("note", ""),
        )


@dataclass(frozen=True)
class TriageEvent:
    """A programme outcome, recorded — never asserted (I5)."""

    id: str
    finding_id: str
    programme_id: str
    outcome: TriageOutcome
    occurred_at: datetime
    platform_label: str = ""
    """The platform's own wording, kept verbatim. Canonical mapping loses
    nuance, and the nuance is sometimes what the dispute is about."""

    programme_evidence: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.programme_evidence.strip():
            raise LedgerError(
                "a triage outcome must reference what the programme actually "
                "said (I5 — the system records outcomes, it never asserts them)"
            )

    @property
    def is_closed(self) -> bool:
        return self.outcome in CLOSED_OUTCOMES

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "programme_id": self.programme_id,
            "outcome": self.outcome.value,
            "occurred_at": self.occurred_at.isoformat(),
            "platform_label": self.platform_label,
            "programme_evidence": self.programme_evidence,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TriageEvent:
        return cls(
            id=data["id"],
            finding_id=data["finding_id"],
            programme_id=data["programme_id"],
            outcome=TriageOutcome(data["outcome"]),
            occurred_at=_parse_dt(data["occurred_at"]),
            platform_label=data.get("platform_label", ""),
            programme_evidence=data.get("programme_evidence", ""),
            note=data.get("note", ""),
        )


@dataclass(frozen=True)
class Payout:
    id: str
    finding_id: str
    programme_id: str
    gross: Decimal
    currency: str
    received_at: datetime
    fees: Decimal = ZERO
    tax_provision: Decimal = ZERO
    collaboration_share: Decimal = ZERO
    severity: str = ""

    @property
    def net_before_tax(self) -> Decimal:
        return self.gross - self.fees - self.collaboration_share

    @property
    def net_after_tax_provision(self) -> Decimal:
        return self.net_before_tax - self.tax_provision

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "programme_id": self.programme_id,
            "gross": str(self.gross),
            "currency": self.currency.upper(),
            "received_at": self.received_at.isoformat(),
            "fees": str(self.fees),
            "tax_provision": str(self.tax_provision),
            "collaboration_share": str(self.collaboration_share),
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Payout:
        return cls(
            id=data["id"],
            finding_id=data["finding_id"],
            programme_id=data["programme_id"],
            gross=_money(data["gross"]),
            currency=data["currency"].upper(),
            received_at=_parse_dt(data["received_at"]),
            fees=_money(data.get("fees", 0)),
            tax_provision=_money(data.get("tax_provision", 0)),
            collaboration_share=_money(data.get("collaboration_share", 0)),
            severity=data.get("severity", ""),
        )


@dataclass(frozen=True)
class Expense:
    id: str
    description: str
    amount: Decimal
    currency: str
    incurred_at: datetime
    category: str = "tooling"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "amount": str(self.amount),
            "currency": self.currency.upper(),
            "incurred_at": self.incurred_at.isoformat(),
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Expense:
        return cls(
            id=data["id"],
            description=data["description"],
            amount=_money(data["amount"]),
            currency=data["currency"].upper(),
            incurred_at=_parse_dt(data["incurred_at"]),
            category=data.get("category", "tooling"),
        )


@dataclass
class Metrics:
    currency: str
    total_hours: Decimal
    hours_by_kind: dict[str, Decimal]
    session_count: int
    submissions: int
    closed_outcomes: int
    outcome_counts: dict[str, int]
    gross: Decimal
    fees: Decimal
    collaboration_share: Decimal
    tax_provision: Decimal
    expenses: Decimal
    excluded_currencies: dict[str, int]
    """Records skipped because they were in another currency. Never summed in."""

    @property
    def net_before_tax(self) -> Decimal:
        return self.gross - self.fees - self.collaboration_share - self.expenses

    @property
    def net_after_tax_provision(self) -> Decimal:
        return self.net_before_tax - self.tax_provision

    @property
    def effective_hourly(self) -> Decimal | None:
        """Net divided by *every* tracked hour. There is no other version.

        Returns ``None`` only when no hours have been tracked at all, because
        a rate computed from zero hours is not a small number, it is a
        meaningless one.
        """
        if self.total_hours <= ZERO:
            return None
        return self.net_before_tax / self.total_hours

    @property
    def valid_rate(self) -> Decimal | None:
        if not self.closed_outcomes:
            return None
        return Decimal(self.outcome_counts.get("valid", 0)) / Decimal(
            self.closed_outcomes
        )

    @property
    def duplicate_rate(self) -> Decimal | None:
        if not self.closed_outcomes:
            return None
        return Decimal(self.outcome_counts.get("duplicate", 0)) / Decimal(
            self.closed_outcomes
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency": self.currency,
            "total_hours": str(self.total_hours.quantize(Decimal("0.01"))),
            "hours_by_kind": {k: str(v.quantize(Decimal("0.01")))
                              for k, v in self.hours_by_kind.items()},
            "session_count": self.session_count,
            "submissions": self.submissions,
            "closed_outcomes": self.closed_outcomes,
            "outcome_counts": dict(self.outcome_counts),
            "gross": str(self.gross),
            "net_before_tax": str(self.net_before_tax),
            "expenses": str(self.expenses),
            "effective_hourly": (
                str(self.effective_hourly.quantize(Decimal("0.01")))
                if self.effective_hourly is not None
                else None
            ),
            "valid_rate": str(self.valid_rate) if self.valid_rate is not None else None,
            "duplicate_rate": (
                str(self.duplicate_rate) if self.duplicate_rate is not None else None
            ),
            "excluded_currencies": dict(self.excluded_currencies),
        }


@dataclass
class Forecast:
    """Descriptive, not predictive. Built only from observed personal data."""

    currency: str
    months_observed: int
    monthly_net: list[Decimal]
    median_monthly_net: Decimal
    lower_quartile: Decimal
    upper_quartile: Decimal
    zero_month_probability: Decimal
    income_concentration: Decimal
    """Share of all income from the single largest payout. High concentration
    means the median is describing luck, not a rate."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency": self.currency,
            "months_observed": self.months_observed,
            "median_monthly_net": str(self.median_monthly_net),
            "lower_quartile": str(self.lower_quartile),
            "upper_quartile": str(self.upper_quartile),
            "zero_month_probability": str(self.zero_month_probability),
            "income_concentration": str(self.income_concentration),
        }


class Ledger:
    """Append-only records of time, outcomes, payouts and costs.

    Args:
        root: Where records live. Omit for the resolution order in
            :func:`resolve_ledger_root`.
        audit: Every write is recorded.
        allow_in_repository: Permit a root inside a git working tree. Off by
            default — this is personal financial data and programme outcome
            history, neither of which belongs in a repository.
    """

    FILES = {
        "sessions": "sessions.jsonl",
        "triage": "triage.jsonl",
        "payouts": "payouts.jsonl",
        "expenses": "expenses.jsonl",
    }

    def __init__(
        self,
        root: str | os.PathLike[str] | None = None,
        *,
        audit: AuditLog | None = None,
        allow_in_repository: bool = False,
        clock: Callable[[], datetime] = _utcnow,
    ):
        self.root = resolve_ledger_root(root).resolve()
        self._audit = audit
        self._clock = clock

        if not allow_in_repository:
            repository = find_repository_root(self.root)
            if repository is not None:
                raise LedgerError(
                    f"refusing to place the ledger at {self.root} — it is inside "
                    f"the git working tree at {repository}. This holds personal "
                    "financial data and programme outcome history. Set "
                    "GREYTHEORY_LEDGER_ROOT to a path outside it."
                )
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, kind: str) -> Path:
        return self.root / self.FILES[kind]

    def _append(self, kind: str, payload: dict[str, Any], *, action: str) -> None:
        with self._path(kind).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        if self._audit is not None:
            self._audit.append(
                actor="ledger", action=action, detail={"id": payload.get("id")}
            )

    def _read(self, kind: str) -> Iterator[dict[str, Any]]:
        path = self._path(kind)
        if not path.is_file():
            return
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def record_session(self, session: Session) -> Session:
        self._append("sessions", session.to_dict(), action="ledger.session")
        return session

    def record_triage(self, event: TriageEvent) -> TriageEvent:
        self._append("triage", event.to_dict(), action="ledger.triage")
        return event

    def record_payout(self, payout: Payout) -> Payout:
        self._append("payouts", payout.to_dict(), action="ledger.payout")
        return payout

    def record_expense(self, expense: Expense) -> Expense:
        self._append("expenses", expense.to_dict(), action="ledger.expense")
        return expense

    def sessions(self) -> list[Session]:
        return [Session.from_dict(d) for d in self._read("sessions")]

    def triage_events(self) -> list[TriageEvent]:
        return [TriageEvent.from_dict(d) for d in self._read("triage")]

    def payouts(self) -> list[Payout]:
        return [Payout.from_dict(d) for d in self._read("payouts")]

    def expenses(self) -> list[Expense]:
        return [Expense.from_dict(d) for d in self._read("expenses")]

    def metrics(self, *, currency: str = "GBP") -> Metrics:
        currency = currency.upper()
        sessions = self.sessions()
        events = self.triage_events()

        hours_by_kind: dict[str, Decimal] = {}
        for session in sessions:
            hours_by_kind[session.kind.value] = (
                hours_by_kind.get(session.kind.value, ZERO) + session.hours
            )
        total_hours = sum(hours_by_kind.values(), ZERO)

        outcome_counts: dict[str, int] = {}
        for event in events:
            outcome_counts[event.outcome.value] = (
                outcome_counts.get(event.outcome.value, 0) + 1
            )

        excluded: dict[str, int] = {}
        gross = fees = collaboration = tax = expenses_total = ZERO

        for payout in self.payouts():
            if payout.currency != currency:
                excluded[payout.currency] = excluded.get(payout.currency, 0) + 1
                continue
            gross += payout.gross
            fees += payout.fees
            collaboration += payout.collaboration_share
            tax += payout.tax_provision

        for expense in self.expenses():
            if expense.currency != currency:
                excluded[expense.currency] = excluded.get(expense.currency, 0) + 1
                continue
            expenses_total += expense.amount

        return Metrics(
            currency=currency,
            total_hours=total_hours,
            hours_by_kind=hours_by_kind,
            session_count=len(sessions),
            submissions=sum(
                1 for e in events if e.outcome is TriageOutcome.SUBMITTED
            ),
            closed_outcomes=sum(1 for e in events if e.is_closed),
            outcome_counts=outcome_counts,
            gross=gross,
            fees=fees,
            collaboration_share=collaboration,
            tax_provision=tax,
            expenses=expenses_total,
            excluded_currencies=excluded,
        )

    def forecast(self, *, currency: str = "GBP") -> Forecast:
        """Describe observed monthly income. Refuse if there is too little of it.

        Raises:
            InsufficientData: Naming exactly what is missing. A forecast from
                three data points is not a forecast; it is a number with a
                confidence interval wide enough to contain any belief you
                brought to it.
        """
        currency = currency.upper()
        metrics = self.metrics(currency=currency)

        missing: list[str] = []
        if metrics.total_hours < MINIMUM_TRACKED_HOURS:
            missing.append(
                f"{MINIMUM_TRACKED_HOURS - metrics.total_hours:.1f} more tracked hours "
                f"(have {metrics.total_hours:.1f} of {MINIMUM_TRACKED_HOURS})"
            )
        if metrics.session_count < MINIMUM_SESSIONS:
            missing.append(
                f"{MINIMUM_SESSIONS - metrics.session_count} more sessions "
                f"(have {metrics.session_count} of {MINIMUM_SESSIONS})"
            )
        if metrics.submissions < MINIMUM_SUBMISSIONS:
            missing.append(
                f"{MINIMUM_SUBMISSIONS - metrics.submissions} more submissions "
                f"(have {metrics.submissions} of {MINIMUM_SUBMISSIONS})"
            )
        if metrics.closed_outcomes < MINIMUM_CLOSED_OUTCOMES:
            missing.append(
                f"{MINIMUM_CLOSED_OUTCOMES - metrics.closed_outcomes} more closed "
                f"triage outcomes (have {metrics.closed_outcomes} of "
                f"{MINIMUM_CLOSED_OUTCOMES})"
            )
        if missing:
            raise InsufficientData(missing)

        payouts = [p for p in self.payouts() if p.currency == currency]
        by_month: dict[str, Decimal] = {}
        for payout in payouts:
            key = payout.received_at.strftime("%Y-%m")
            by_month[key] = by_month.get(key, ZERO) + payout.net_before_tax

        # Months with no payout are real months and belong in the distribution.
        # Dropping them is how a £0 month becomes invisible.
        first = min(p.received_at for p in payouts) if payouts else self._clock()
        last = self._clock()
        months: list[str] = []
        year, month = first.year, first.month
        while (year, month) <= (last.year, last.month):
            months.append(f"{year:04d}-{month:02d}")
            month += 1
            if month > 12:
                year, month = year + 1, 1

        monthly = [by_month.get(key, ZERO) for key in months] or [ZERO]
        ordered = sorted(monthly)
        zero_months = sum(1 for value in monthly if value <= ZERO)
        largest = max((p.net_before_tax for p in payouts), default=ZERO)
        total = sum((p.net_before_tax for p in payouts), ZERO)

        def quantile(fraction: float) -> Decimal:
            index = min(int(len(ordered) * fraction), len(ordered) - 1)
            return ordered[index]

        return Forecast(
            currency=currency,
            months_observed=len(monthly),
            monthly_net=monthly,
            median_monthly_net=Decimal(str(statistics.median(monthly))),
            lower_quartile=quantile(0.25),
            upper_quartile=quantile(0.75),
            zero_month_probability=Decimal(zero_months) / Decimal(len(monthly)),
            income_concentration=(largest / total) if total > ZERO else ZERO,
        )


__all__ = [
    "CLOSED_OUTCOMES",
    "Expense",
    "Forecast",
    "InsufficientData",
    "Ledger",
    "LedgerError",
    "Metrics",
    "Payout",
    "Session",
    "SessionKind",
    "TriageEvent",
    "TriageOutcome",
    "resolve_ledger_root",
]
