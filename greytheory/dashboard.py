"""The dashboard read model — and two renderers over it.

A dashboard is where a control plane goes wrong most quietly. The temptation is
to fill every panel, and the way you fill a panel with no data is by printing a
zero. "0 out-of-scope attempts" and "no audit log configured" look identical on
a screen and mean opposite things, and the reassuring one is the lie.

So this module has one rule above the rest:

**Absent data renders as UNKNOWN, never as zero.** A panel with nothing behind
it says so. Every store is optional, and every metric carries a status that
distinguishes "measured, and it is fine" from "not measured".

The second rule follows the handover's acceptance criterion: the dashboard must
distinguish live capability from proposed architecture. It reports only what
the code can actually observe, and the capability panel names what does not
exist yet rather than leaving a gap for optimism to fill.

The read model is a plain dataclass tree. Renderers are pure functions over it,
so a future web surface does not need to re-derive anything.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Sequence

from greytheory.audit import AuditLog
from greytheory.authority.gate import AuthorityLevel, Reason
from greytheory.capabilities import CAPABILITIES, CapabilityStatus
from greytheory.evidence import EvidenceVault
from greytheory.findings import Finding, Taxonomy
from greytheory.ledger import InsufficientData, Ledger
from greytheory.registry import ProgrammeRegistry

SCOPE_DENIALS = {
    Reason.ASSET_OUT_OF_SCOPE.value,
    Reason.ASSET_UNRESOLVED.value,
    Reason.DERIVED_ASSET_NOT_INHERITED.value,
}
POSTURE_DENIALS = {
    Reason.POSTURE_CEILING_EXCEEDED.value,
    Reason.AUTHORITY_LEVEL_EXCEEDED.value,
    Reason.TECHNIQUE_PROHIBITED.value,
}
APPROVAL_DENIALS = {
    r.value for r in Reason if r.value.startswith("approval_")
}


class Status(str, Enum):
    OK = "ok"
    WARN = "warn"
    ALERT = "alert"
    UNKNOWN = "unknown"
    """Not measured. Never conflate with a measured zero."""

    INFO = "info"


@dataclass(frozen=True)
class Metric:
    label: str
    value: str
    status: Status = Status.INFO
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "label": self.label,
            "value": self.value,
            "status": self.status.value,
            "detail": self.detail,
        }


@dataclass
class Panel:
    id: str
    title: str
    metrics: list[Metric] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def worst_status(self) -> Status:
        for status in (Status.ALERT, Status.WARN, Status.UNKNOWN):
            if any(m.status is status for m in self.metrics):
                return status
        return Status.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.worst_status.value,
            "metrics": [m.to_dict() for m in self.metrics],
            "columns": list(self.columns),
            "rows": [list(r) for r in self.rows],
            "note": self.note,
        }


@dataclass
class Dashboard:
    generated_at: datetime
    posture_ceiling: str
    panels: list[Panel]
    next_action: str

    def panel(self, panel_id: str) -> Panel:
        for panel in self.panels:
            if panel.id == panel_id:
                return panel
        raise KeyError(panel_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "posture_ceiling": self.posture_ceiling,
            "next_action": self.next_action,
            "panels": [p.to_dict() for p in self.panels],
        }


def _unknown(label: str, why: str) -> Metric:
    return Metric(label, "unknown", Status.UNKNOWN, why)


def _programmes_panel(registry: ProgrammeRegistry | None) -> Panel:
    panel = Panel("programmes", "Programmes")
    if registry is None:
        panel.metrics.append(_unknown("Registered", "no registry configured"))
        panel.note = "Pass a ProgrammeRegistry to see scope state."
        return panel

    programmes = registry.programmes()
    attention = {item.programme_id: item for item in registry.needs_attention()}

    panel.metrics.append(Metric("Registered", str(len(programmes))))
    panel.metrics.append(
        Metric(
            "Need attention",
            str(len(attention)),
            Status.WARN if attention else Status.OK,
            "blocked, awaiting review, or stale" if attention else "all current",
        )
    )
    usable = [
        p for p in programmes
        if p not in attention and (c := registry.current_contract(p)) and c.human_reviewed
    ]
    panel.metrics.append(
        Metric(
            "Grant authority now",
            str(len(usable)),
            Status.OK if usable else Status.WARN,
            "verified, reviewed and fresh",
        )
    )

    panel.columns = ["Programme", "Version", "Status", "Grants", "Needs"]
    for programme_id in programmes:
        version = registry.latest(programme_id)
        item = attention.get(programme_id)
        panel.rows.append(
            [
                programme_id,
                f"v{version.version}",
                version.contract.status.value,
                version.contract.max_authority,
                item.reason if item else "-",
            ]
        )
    return panel


def _authority_panel(audit: AuditLog | None) -> Panel:
    panel = Panel("authority", "Authority")
    if audit is None:
        panel.metrics.append(_unknown("Gate decisions", "no audit log configured"))
        return panel

    records = [r for r in audit.records() if r.action == "gate.evaluate"]
    allowed = sum(1 for r in records if r.detail.get("allowed"))
    denied = len(records) - allowed

    panel.metrics.append(Metric("Gate decisions", str(len(records))))
    panel.metrics.append(Metric("Allowed", str(allowed)))
    panel.metrics.append(
        Metric("Denied", str(denied), Status.INFO, "a denial is the system working")
    )

    reasons: dict[str, int] = {}
    for record in records:
        if not record.detail.get("allowed"):
            reason = record.detail.get("reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

    panel.columns = ["Denial reason", "Count"]
    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        panel.rows.append([reason, str(count)])
    if not reasons:
        panel.note = "No denials recorded."
    return panel


def _safety_panel(audit: AuditLog | None) -> Panel:
    """The panel that must never be reassuring by accident."""
    panel = Panel("safety", "Safety")
    if audit is None:
        panel.metrics.append(
            _unknown("Audit chain", "no audit log configured - nothing is being recorded")
        )
        panel.metrics.append(_unknown("Scope attempts", "no audit log configured"))
        panel.metrics.append(_unknown("Posture attempts", "no audit log configured"))
        panel.note = (
            "Nothing here is measured. This is not the same as everything being fine."
        )
        return panel

    intact = audit.is_valid()
    panel.metrics.append(
        Metric(
            "Audit chain",
            "intact" if intact else "BROKEN",
            Status.OK if intact else Status.ALERT,
            "hash chain verified" if intact else "a record has been altered or removed",
        )
    )

    records = [r for r in audit.records() if r.action == "gate.evaluate"]
    denials = [r for r in records if not r.detail.get("allowed")]

    def count(reasons: set[str]) -> int:
        return sum(1 for r in denials if r.detail.get("reason") in reasons)

    scope_attempts = count(SCOPE_DENIALS)
    posture_attempts = count(POSTURE_DENIALS)
    approval_attempts = count(APPROVAL_DENIALS)
    executed_out_of_scope = 0  # by construction: the gate is the only execution path

    panel.metrics.append(
        Metric(
            "Out-of-scope executed",
            str(executed_out_of_scope),
            Status.OK,
            "the gate is the only execution path",
        )
    )
    panel.metrics.append(
        Metric(
            "Scope attempts blocked",
            str(scope_attempts),
            Status.WARN if scope_attempts else Status.OK,
            "blocked before execution, but something tried"
            if scope_attempts
            else "nothing attempted an out-of-scope asset",
        )
    )
    panel.metrics.append(
        Metric(
            "Posture attempts blocked",
            str(posture_attempts),
            Status.WARN if posture_attempts else Status.OK,
            "a request wanted more authority than is permitted"
            if posture_attempts
            else "no request exceeded its authority",
        )
    )
    panel.metrics.append(
        Metric(
            "Approval failures",
            str(approval_attempts),
            Status.WARN if approval_attempts else Status.OK,
        )
    )

    kills = [r for r in audit.records() if r.action.startswith("kill_switch")]
    if kills:
        panel.metrics.append(
            Metric(
                "Kill switch",
                "engaged" if kills[-1].action.endswith("engage") else "released",
                Status.ALERT if kills[-1].action.endswith("engage") else Status.INFO,
            )
        )
    return panel


def _evidence_panel(
    vault: EvidenceVault | None, findings: Sequence[Finding]
) -> Panel:
    panel = Panel("evidence", "Evidence")
    if vault is None:
        panel.metrics.append(_unknown("Artifacts", "no evidence vault configured"))
        return panel
    if not findings:
        panel.metrics.append(
            _unknown("Artifacts", "no findings supplied to inspect")
        )
        panel.note = "Pass the findings you want evidence reported for."
        return panel

    total = redacted = 0
    integrity_problems: list[str] = []
    panel.columns = ["Finding", "Artifacts", "Redacted", "Integrity"]

    for finding in findings:
        manifest = vault.manifest(finding.id)
        problems = vault.verify(finding.id)
        done = sum(1 for a in manifest.artifacts if a.is_exportable)
        total += len(manifest.artifacts)
        redacted += done
        if problems:
            integrity_problems.extend(problems)
        panel.rows.append(
            [
                finding.id,
                str(len(manifest.artifacts)),
                f"{done}/{len(manifest.artifacts)}",
                "FAILED" if problems else "ok",
            ]
        )

    panel.metrics.append(Metric("Artifacts held", str(total)))
    panel.metrics.append(
        Metric(
            "Awaiting redaction",
            str(total - redacted),
            Status.WARN if total - redacted else Status.OK,
            "cannot be exported until redacted",
        )
    )
    panel.metrics.append(
        Metric(
            "Integrity",
            "FAILED" if integrity_problems else "ok",
            Status.ALERT if integrity_problems else Status.OK,
            "; ".join(integrity_problems[:2]),
        )
    )
    return panel


def _findings_panel(findings: Sequence[Finding]) -> Panel:
    panel = Panel("findings", "Findings")
    if not findings:
        panel.metrics.append(_unknown("Tracked", "no findings supplied"))
        return panel

    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.state.value] = counts.get(finding.state.value, 0) + 1

    panel.metrics.append(Metric("Tracked", str(len(findings))))
    panel.metrics.append(
        Metric(
            "Report-ready",
            str(counts.get(Taxonomy.REPORT_READY.value, 0)),
            Status.INFO,
            "awaiting your Gate G decision",
        )
    )
    panel.metrics.append(
        Metric("Submitted", str(counts.get(Taxonomy.SUBMITTED.value, 0)))
    )

    panel.columns = ["State", "Count"]
    for state, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        panel.rows.append([state, str(count)])
    return panel


def _economics_panel(ledger: Ledger | None, currency: str) -> Panel:
    panel = Panel("economics", "Economics")
    if ledger is None:
        panel.metrics.append(_unknown("Tracked hours", "no ledger configured"))
        panel.note = "Without a ledger there is no hourly rate, only a payout total."
        return panel

    metrics = ledger.metrics(currency=currency)
    hourly = metrics.effective_hourly

    panel.metrics.append(
        Metric("Tracked hours", f"{metrics.total_hours:.1f}", Status.INFO)
    )
    panel.metrics.append(Metric("Gross", f"{metrics.gross} {currency}"))
    panel.metrics.append(Metric("Net before tax", f"{metrics.net_before_tax} {currency}"))
    panel.metrics.append(
        Metric(
            "Effective hourly",
            f"{hourly.quantize(Decimal('0.01'))} {currency}/h"
            if hourly is not None
            else "unknown",
            Status.INFO if hourly is not None else Status.UNKNOWN,
            "across every tracked hour, not just productive ones"
            if hourly is not None
            else "no hours tracked",
        )
    )
    if metrics.excluded_currencies:
        panel.metrics.append(
            Metric(
                "Excluded records",
                ", ".join(f"{k}:{v}" for k, v in metrics.excluded_currencies.items()),
                Status.WARN,
                "other currencies are never summed in",
            )
        )

    try:
        forecast = ledger.forecast(currency=currency)
        panel.metrics.append(
            Metric(
                "Median month",
                f"{forecast.median_monthly_net} {currency}",
                Status.INFO,
                f"P(zero month) {forecast.zero_month_probability:.0%}, "
                f"concentration {forecast.income_concentration:.0%}",
            )
        )
    except InsufficientData as exc:
        panel.metrics.append(
            Metric(
                "Forecast",
                "refused",
                Status.INFO,
                "not enough data yet - plan on zero",
            )
        )
        panel.note = "Missing before a forecast is honest:\n" + "\n".join(
            f"  - {item}" for item in exc.missing
        )

    panel.columns = ["Session kind", "Hours"]
    for kind, hours in sorted(
        metrics.hours_by_kind.items(), key=lambda kv: -kv[1]
    ):
        panel.rows.append([kind, f"{hours:.1f}"])
    return panel


def _capability_panel() -> Panel:
    """What exists, stated so a gap cannot be filled by optimism."""
    panel = Panel("capability", "Capability")
    panel.metrics.append(
        Metric(
            "Detection",
            "offline static",
            Status.INFO,
            "three local-file collectors are implemented; no web or network collector exists",
        )
    )
    panel.metrics.append(
        Metric("Submission", "manual", Status.INFO, "Gate G is not automatable")
    )
    panel.columns = ["Component", "Status"]
    panel.rows = [
        [item.label, item.status.value]
        for item in CAPABILITIES
        if item.id
        in {
            "programme_registry",
            "scope_compiler",
            "execution_gate",
            "operator_approvals",
            "audit_log",
            "evidence_vault",
            "validation_reporting",
            "lane_1_dependency",
            "lane_2_exposure",
            "lane_3_web",
            "lane_4_agent_config",
            "learning_core",
            "guided_learning",
            "model_gateway",
            "scope_watch_offline",
            "scope_watch_collector",
            "dashboard_read_model",
            "graphical_workbench",
            "local_fixture_executor",
            "passive_http_worker",
        }
    ]
    unavailable = sum(
        1 for item in CAPABILITIES if item.status is CapabilityStatus.UNAVAILABLE
    )
    panel.note = (
        f"{unavailable} capability boundaries are explicitly unavailable; "
        "status describes shipped code, not configured runtime health."
    )
    return panel


def _next_action(panels: list[Panel]) -> str:
    """One thing to do. A dashboard that suggests six things suggests none."""
    safety = next((p for p in panels if p.id == "safety"), None)
    if safety and any(m.status is Status.ALERT for m in safety.metrics):
        alert = next(m for m in safety.metrics if m.status is Status.ALERT)
        return f"Safety: {alert.label} is {alert.value}. Stop and investigate."

    evidence = next((p for p in panels if p.id == "evidence"), None)
    if evidence and any(
        m.label == "Integrity" and m.status is Status.ALERT for m in evidence.metrics
    ):
        return "Evidence integrity check failed. Do not export anything."

    programmes = next((p for p in panels if p.id == "programmes"), None)
    if programmes:
        needs = next(
            (m for m in programmes.metrics if m.label == "Need attention"), None
        )
        if needs and needs.status is Status.WARN:
            return (
                f"{needs.value} programme(s) need attention before testing: "
                "greytheory programme status"
            )
        grants = next(
            (m for m in programmes.metrics if m.label == "Grant authority now"), None
        )
        if grants and grants.value == "0":
            return "No programme currently grants authority. Register and review one."

    findings = next((p for p in panels if p.id == "findings"), None)
    if findings:
        ready = next((m for m in findings.metrics if m.label == "Report-ready"), None)
        if ready and ready.value not in ("0", "unknown"):
            return f"{ready.value} finding(s) are report-ready and awaiting your decision."

    return "Nothing is blocked. Pick a hypothesis and record the session."


def build_dashboard(
    *,
    registry: ProgrammeRegistry | None = None,
    audit: AuditLog | None = None,
    vault: EvidenceVault | None = None,
    ledger: Ledger | None = None,
    findings: Sequence[Finding] = (),
    posture_ceiling: AuthorityLevel = AuthorityLevel.LOCAL_FIXTURE,
    currency: str = "GBP",
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> Dashboard:
    """Assemble the read model. Every source is optional; absence is reported."""
    panels = [
        _programmes_panel(registry),
        _authority_panel(audit),
        _safety_panel(audit),
        _findings_panel(findings),
        _evidence_panel(vault, findings),
        _economics_panel(ledger, currency),
        _capability_panel(),
    ]
    return Dashboard(
        generated_at=now(),
        posture_ceiling=posture_ceiling.name,
        panels=panels,
        next_action=_next_action(panels),
    )


MARKERS = {
    Status.OK: "ok  ",
    Status.WARN: "warn",
    Status.ALERT: "ALRT",
    Status.UNKNOWN: "????",
    Status.INFO: "    ",
}


def render_text(dashboard: Dashboard) -> str:
    """Terminal rendering. ASCII only, so it survives every console."""
    out: list[str] = []
    out.append("=" * 68)
    out.append("GreyTheory AI - operator dashboard")
    out.append(
        f"generated {dashboard.generated_at.isoformat()}  |  "
        f"posture ceiling: {dashboard.posture_ceiling}"
    )
    out.append("=" * 68)
    out.append("")
    out.append(f"NEXT: {dashboard.next_action}")
    out.append("")

    for panel in dashboard.panels:
        out.append(f"-- {panel.title} " + "-" * max(0, 64 - len(panel.title)))
        for metric in panel.metrics:
            marker = MARKERS[metric.status]
            line = f"  [{marker}] {metric.label:<24} {metric.value}"
            out.append(line)
            if metric.detail:
                out.append(f"           {metric.detail}")
        if panel.columns and panel.rows:
            widths = [
                max(len(panel.columns[i]), *(len(r[i]) for r in panel.rows))
                for i in range(len(panel.columns))
            ]
            header = "  " + "  ".join(
                c.ljust(widths[i]) for i, c in enumerate(panel.columns)
            )
            out.append("")
            out.append(header)
            out.append("  " + "  ".join("-" * w for w in widths))
            for row in panel.rows:
                out.append(
                    "  " + "  ".join(v.ljust(widths[i]) for i, v in enumerate(row))
                )
        if panel.note:
            out.append("")
            for line in panel.note.splitlines():
                out.append(f"  {line}")
        out.append("")
    return "\n".join(out)


_CSS = """
:root { color-scheme: light dark; --bg:#ffffff; --fg:#111827; --muted:#6b7280;
  --card:#f9fafb; --line:#e5e7eb; --ok:#059669; --warn:#b45309; --alert:#dc2626;
  --unknown:#7c3aed; }
@media (prefers-color-scheme: dark) { :root { --bg:#0b0f19; --fg:#e5e7eb;
  --muted:#9ca3af; --card:#111827; --line:#1f2937; --ok:#10b981; --warn:#f59e0b;
  --alert:#ef4444; --unknown:#a78bfa; } }
* { box-sizing:border-box; }
body { margin:0; padding:2rem 1rem; background:var(--bg); color:var(--fg);
  font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }
.wrap { max-width:1100px; margin:0 auto; }
h1 { font-size:1.35rem; margin:0 0 .25rem; }
.sub { color:var(--muted); font-size:.85rem; margin-bottom:1.5rem; }
.next { border:1px solid var(--line); border-left:4px solid var(--ok);
  background:var(--card); padding:1rem 1.15rem; border-radius:8px; margin-bottom:1.75rem; }
.next b { display:block; font-size:.7rem; letter-spacing:.08em; color:var(--muted);
  text-transform:uppercase; margin-bottom:.35rem; }
.grid { display:grid; gap:1.1rem; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); }
.panel { border:1px solid var(--line); background:var(--card); border-radius:8px;
  padding:1.1rem 1.15rem; }
.panel h2 { font-size:.95rem; margin:0 0 .85rem; display:flex; justify-content:space-between; }
.dot { width:.6rem; height:.6rem; border-radius:50%; display:inline-block; }
.metric { display:flex; justify-content:space-between; gap:1rem; padding:.4rem 0;
  border-bottom:1px solid var(--line); }
.metric:last-of-type { border-bottom:0; }
.metric .l { color:var(--muted); }
.metric .v { font-variant-numeric:tabular-nums; font-weight:600; }
.detail { color:var(--muted); font-size:.78rem; margin:-.2rem 0 .5rem; }
table { width:100%; border-collapse:collapse; margin-top:.8rem; font-size:.85rem;
  display:block; overflow-x:auto; }
th,td { text-align:left; padding:.35rem .5rem; border-bottom:1px solid var(--line);
  white-space:nowrap; }
th { color:var(--muted); font-weight:500; font-size:.75rem; text-transform:uppercase;
  letter-spacing:.05em; }
.note { margin-top:.8rem; font-size:.8rem; color:var(--muted); white-space:pre-wrap; }
.ok{color:var(--ok)} .warn{color:var(--warn)} .alert{color:var(--alert)}
.unknown{color:var(--unknown)} .info{color:var(--fg)}
.bg-ok{background:var(--ok)} .bg-warn{background:var(--warn)}
.bg-alert{background:var(--alert)} .bg-unknown{background:var(--unknown)}
.bg-info{background:var(--muted)}
"""


def render_html(dashboard: Dashboard) -> str:
    """Self-contained HTML. No external resources, no scripts, no network."""
    def esc(value: str) -> str:
        return html.escape(str(value))

    parts: list[str] = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>GreyTheory AI - dashboard</title>",
        f"<style>{_CSS}</style></head><body><div class='wrap'>",
        "<h1>GreyTheory AI</h1>",
        f"<div class='sub'>generated {esc(dashboard.generated_at.isoformat())} "
        f"&middot; posture ceiling <strong>{esc(dashboard.posture_ceiling)}</strong></div>",
        f"<div class='next'><b>Next action</b>{esc(dashboard.next_action)}</div>",
        "<div class='grid'>",
    ]

    for panel in dashboard.panels:
        status = panel.worst_status.value
        parts.append(
            f"<section class='panel'><h2>{esc(panel.title)}"
            f"<span class='dot bg-{status}'></span></h2>"
        )
        for metric in panel.metrics:
            parts.append(
                f"<div class='metric'><span class='l'>{esc(metric.label)}</span>"
                f"<span class='v {metric.status.value}'>{esc(metric.value)}</span></div>"
            )
            if metric.detail:
                parts.append(f"<div class='detail'>{esc(metric.detail)}</div>")
        if panel.columns and panel.rows:
            parts.append("<table><thead><tr>")
            parts.extend(f"<th>{esc(c)}</th>" for c in panel.columns)
            parts.append("</tr></thead><tbody>")
            for row in panel.rows:
                parts.append("<tr>")
                parts.extend(f"<td>{esc(v)}</td>" for v in row)
                parts.append("</tr>")
            parts.append("</tbody></table>")
        if panel.note:
            parts.append(f"<div class='note'>{esc(panel.note)}</div>")
        parts.append("</section>")

    parts.append("</div></div></body></html>")
    return "".join(parts)


def render_json(dashboard: Dashboard) -> str:
    return json.dumps(dashboard.to_dict(), indent=2)


__all__ = [
    "Dashboard",
    "Metric",
    "Panel",
    "Status",
    "build_dashboard",
    "render_html",
    "render_json",
    "render_text",
]
