"""Lane 4 — AI-application and agent configuration.

The differentiated lane. Every other lane competes with tooling that already
exists and is better funded; this one competes with almost nothing, because
the failure modes are new and most scanners have no model of them.

It reads agent and MCP configuration statically. No prompts are sent, no model
is invoked, nothing is executed — this is a config review, and that is
deliberate: the interesting failures in agent systems are almost all
*architectural* rather than behavioural. A jailbreak is a party trick. A tool
that can delete things without an approval gate is a vulnerability whether or
not anyone has thought of the prompt yet.

Each check names what it observed and stops there. "This tool matches a
destructive verb and has no approval requirement" is a fact. Whether it is
exploitable depends on who can reach the agent, what the tool actually does,
and what the programme considers in scope — none of which a config file knows.

The checks map one-for-one onto ChaseOS's own hardening surface, which is the
point: what this lane finds externally is what should be audited internally.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import re
from typing import Any, Iterator

from greytheory.authority.gate import AuthorityLevel
from greytheory.signal.contract import (
    LaneContext,
    LaneSpec,
    RawSignal,
    SignalLevel,
    checked,
    observed,
)

CONSEQUENTIAL_VERBS = (
    "delete", "remove", "drop", "purge", "destroy", "wipe",
    "send", "email", "publish", "post", "tweet", "message",
    "transfer", "pay", "purchase", "refund", "charge",
    "deploy", "execute", "exec", "run_command", "shell", "eval",
    "write", "update", "modify", "grant", "revoke",
)
"""Names suggesting an action with effects outside the agent."""

SECRET_KEYS = re.compile(
    r"(api[_-]?key|secret|token|password|passwd|credential|private[_-]?key|"
    r"access[_-]?key|bearer)",
    re.IGNORECASE,
)

ENV_REFERENCE = re.compile(r"^(\$\{?[A-Z_][A-Z0-9_]*\}?|env:|secret:|ref:|<[^>]+>)")
"""A value that points at a secret rather than containing one."""

WILDCARDS = {"*", "**", "all", "any", "*.*"}

FETCH_HINTS = ("fetch", "browse", "http", "web", "url", "crawl", "scrape", "read_page")
"""Tools that pull in content the operator did not write."""


def _walk(node: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    """Every node in a JSON document, with a dotted path."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{path}[{index}]")


def _tools(document: Any) -> Iterator[tuple[str, dict[str, Any]]]:
    """Tool-shaped entries, wherever they are in the document."""
    for path, node in _walk(document):
        if not isinstance(node, dict):
            continue
        name = node.get("name") or node.get("tool") or node.get("id")
        looks_like_tool = "name" in node and any(
            key in node
            for key in ("description", "approval", "requires_approval",
                        "permissions", "parameters", "input_schema", "command")
        )
        if looks_like_tool and isinstance(name, str):
            yield path, node


def _requires_approval(tool: dict[str, Any]) -> bool | None:
    """Tri-state. ``None`` means the config never says, which is its own finding."""
    for key in ("requires_approval", "approval_required", "needs_approval"):
        if key in tool:
            return bool(tool[key])
    approval = tool.get("approval")
    if isinstance(approval, bool):
        return approval
    if isinstance(approval, str):
        return approval.strip().lower() not in {"none", "never", "auto", "false"}
    if isinstance(approval, dict) and "required" in approval:
        return bool(approval["required"])
    return None


def _is_consequential(name: str) -> str | None:
    lowered = name.lower()
    for verb in CONSEQUENTIAL_VERBS:
        if verb in lowered:
            return verb
    return None


class AgentConfigLane:
    """Static review of agent and MCP configuration."""

    spec = LaneSpec(
        id="lane4_agent_config",
        lane=4,
        title="Agent and MCP configuration review",
        requires_authority=AuthorityLevel.LOCAL_FIXTURE,
        network=False,
        description=(
            "Static inspection of agent/MCP configuration for missing approval "
            "gates, wildcard permissions, inline secrets, unrestricted egress "
            "and untrusted-content exposure. Sends no prompts and invokes no "
            "model."
        ),
    )

    CONFIG_GLOB = "**/*.json"

    def collect(self, context: LaneContext) -> list[RawSignal]:
        signals: list[RawSignal] = []
        for relative in context.iter_files(self.CONFIG_GLOB):
            try:
                document = json.loads(context.read_text(relative))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue  # not a config we can reason about; say nothing
            signals.extend(self._inspect(context, str(relative), document))
        return signals

    def _inspect(
        self, context: LaneContext, filename: str, document: Any
    ) -> list[RawSignal]:
        signals: list[RawSignal] = []
        source = f"{self.spec.id}:{filename}"

        def signal(kind: str, title: str, claims: list, **detail: Any) -> RawSignal:
            return RawSignal(
                id=f"{self.spec.id}_{kind}_{len(signals)}_{abs(hash(filename)) % 10000}",
                lane=4,
                asset=context.asset,
                kind=kind,
                title=title,
                level=SignalLevel.CONTEXTUAL,
                claims=claims,
                detail={"file": filename, **detail},
                observed_at=context.now(),
            )

        fetchers: list[str] = []
        consequential_ungated: list[str] = []

        for path, tool in _tools(document):
            name = str(tool.get("name") or tool.get("tool") or tool.get("id"))
            approval = _requires_approval(tool)
            verb = _is_consequential(name)

            if any(hint in name.lower() for hint in FETCH_HINTS):
                fetchers.append(name)

            if verb and approval is not True:
                consequential_ungated.append(name)
                state = "explicitly false" if approval is False else "not declared"
                signals.append(
                    signal(
                        "tool_without_approval_gate",
                        f"Tool {name!r} suggests a consequential action and has no "
                        "approval requirement",
                        [
                            checked(
                                f"tool {name!r} at {path} matches consequential verb "
                                f"{verb!r} and its approval requirement is {state}",
                                source,
                                f"check:approval:{name}",
                            ),
                            observed(
                                "whether this is exploitable depends on who can "
                                "reach the agent and what the tool actually does",
                                source,
                            ),
                        ],
                        tool=name,
                        verb=verb,
                        approval=state,
                        json_path=path,
                    )
                )

            permissions = tool.get("permissions") or tool.get("scopes") or []
            if isinstance(permissions, (str, list)):
                values = [permissions] if isinstance(permissions, str) else permissions
                wild = [v for v in values if str(v).strip().lower() in WILDCARDS]
                if wild:
                    signals.append(
                        signal(
                            "wildcard_tool_permission",
                            f"Tool {name!r} holds a wildcard permission",
                            [
                                checked(
                                    f"tool {name!r} permissions include {wild!r}",
                                    source,
                                    f"check:wildcard:{name}",
                                )
                            ],
                            tool=name,
                            permissions=wild,
                        )
                    )

        for path, node in _walk(document):
            if not isinstance(node, dict):
                continue
            for key, value in node.items():
                if not isinstance(value, str) or not SECRET_KEYS.search(key):
                    continue
                if ENV_REFERENCE.match(value.strip()) or len(value.strip()) < 12:
                    continue
                signals.append(
                    signal(
                        "inline_secret_reference",
                        f"Configuration key {key!r} appears to hold a literal secret",
                        [
                            checked(
                                f"{path}.{key} is a {len(value)}-character literal, "
                                "not an environment or secret-store reference",
                                source,
                                f"check:inline_secret:{path}.{key}",
                            ),
                            observed(
                                "the value was not read, validated or recorded",
                                source,
                            ),
                        ],
                        json_path=f"{path}.{key}",
                        value_length=len(value),
                    )
                )

        for path, node in _walk(document):
            if not isinstance(node, dict):
                continue
            for key in ("allowed_hosts", "egress", "network", "allowed_domains"):
                value = node.get(key)
                values = (
                    [value] if isinstance(value, str)
                    else value if isinstance(value, list)
                    else []
                )
                wild = [v for v in values if str(v).strip().lower() in WILDCARDS]
                if wild:
                    signals.append(
                        signal(
                            "unrestricted_egress",
                            f"Network egress at {path}.{key} is unrestricted",
                            [
                                checked(
                                    f"{path}.{key} includes {wild!r}",
                                    source,
                                    f"check:egress:{path}.{key}",
                                )
                            ],
                            json_path=f"{path}.{key}",
                        )
                    )

        for path, node in _walk(document):
            if isinstance(node, dict):
                url = node.get("url") or node.get("endpoint")
                if isinstance(url, str) and url.startswith("http://"):
                    if not re.match(r"^http://(localhost|127\.0\.0\.1|\[::1\])", url):
                        signals.append(
                            signal(
                                "plaintext_transport",
                                f"Server at {path} is configured over plaintext HTTP",
                                [
                                    checked(
                                        f"{path} url uses the http:// scheme to a "
                                        "non-loopback host",
                                        source,
                                        f"check:transport:{path}",
                                    )
                                ],
                                json_path=path,
                            )
                        )

        # Composite: untrusted content reaching an agent that can act. Neither
        # half is a finding on its own, which is exactly why a per-key scanner
        # never sees it.
        if fetchers and consequential_ungated:
            signals.append(
                signal(
                    "untrusted_content_reaches_ungated_action",
                    "Agent can fetch external content and hold ungated "
                    "consequential tools in the same context",
                    [
                        checked(
                            f"content-fetching tools {fetchers!r} and ungated "
                            f"consequential tools {consequential_ungated!r} are "
                            "configured together",
                            source,
                            "check:composite:injection_path",
                        ),
                        observed(
                            "this is the shape of an indirect prompt-injection "
                            "path; whether one exists depends on how the harness "
                            "isolates fetched content",
                            source,
                        ),
                    ],
                    fetchers=fetchers,
                    ungated=consequential_ungated,
                )
            )

        return signals


__all__ = ["AgentConfigLane", "CONSEQUENTIAL_VERBS", "FETCH_HINTS"]
