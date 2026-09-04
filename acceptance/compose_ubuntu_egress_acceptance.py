"""Validate and compose the retained Ubuntu egress acceptance record."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


class CompositionError(RuntimeError):
    """Raised when runtime evidence does not prove the fixture contract."""


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CompositionError(f"invalid JSON evidence: {path.name}") from exc


def _required_ruleset(ruleset: str) -> int:
    required = (
        "table inet greytheory",
        "chain input",
        "chain forward",
        "chain output",
        "policy drop",
        "ip daddr 8.8.8.8 tcp dport 443 ct state new accept",
        'counter name "denied_output" reject',
    )
    if any(fragment not in ruleset for fragment in required):
        raise CompositionError("loaded nftables ruleset is missing a required boundary")
    if "ip daddr 1.1.1.1" in ruleset and "accept" in ruleset.split(
        "ip daddr 1.1.1.1", 1
    )[1].splitlines()[0]:
        raise CompositionError("decoy address was unexpectedly allowlisted")
    match = re.search(
        r'counter denied_output \{\s+packets (\d+) bytes (\d+)', ruleset
    )
    if match is None:
        raise CompositionError("nftables denial counter is absent")
    denied_packets = int(match.group(1))
    if denied_packets < 3:
        raise CompositionError("nftables did not account for all denied probes")
    return denied_packets


def _validate_network(network: dict[str, Any]) -> None:
    links = network.get("links")
    addresses = network.get("addresses")
    routes = network.get("routes")
    if not isinstance(links, list) or [item.get("ifname") for item in links] != ["lo"]:
        raise CompositionError("worker network namespace must expose only loopback")
    if not isinstance(addresses, list) or len(addresses) != 1:
        raise CompositionError("worker address evidence is invalid")
    assigned = {
        info.get("local") for info in addresses[0].get("addr_info", [])
    }
    expected_addresses = {"127.0.0.1", "::1", "8.8.8.8", "1.1.1.1"}
    if assigned != expected_addresses:
        raise CompositionError("fixture addresses are incomplete")
    if not isinstance(routes, list) or any(
        route.get("dst") == "default" for route in routes
    ):
        raise CompositionError("worker namespace has a default route")
    allowed_routes = {
        "1.1.1.1",
        "8.8.8.8",
        "127.0.0.0/8",
        "127.0.0.1",
        "127.255.255.255",
        "::1",
    }
    if any(
        route.get("dev") != "lo" or route.get("dst") not in allowed_routes
        for route in routes
    ):
        raise CompositionError("worker namespace contains an unexpected route")


def main(arguments: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if arguments is None else arguments)
    if len(args) != 8:
        raise CompositionError(
            "expected service, probes, ruleset, policy, network, route mutation, "
            "firewall mutation, and tool manifest paths"
        )
    (
        service_path,
        probes_path,
        ruleset_path,
        policy_path,
        network_path,
        route_mutation_path,
        firewall_mutation_path,
        tool_manifest_path,
    ) = map(Path, args)
    service = _json(service_path)
    probes = _json(probes_path)
    network = _json(network_path)
    tool_manifest = _json(tool_manifest_path)
    ruleset = ruleset_path.read_text(encoding="utf-8")
    denied_packets = _required_ruleset(ruleset)
    _validate_network(network)
    if len(probes.get("probes", [])) != 3 or any(
        probe.get("connected") is not False for probe in probes["probes"]
    ):
        raise CompositionError("forbidden egress probe evidence is incomplete")
    if route_mutation_path.read_text(encoding="ascii").strip() != "denied":
        raise CompositionError("unprivileged route mutation was not denied")
    if firewall_mutation_path.read_text(encoding="ascii").strip() != "denied":
        raise CompositionError("unprivileged firewall mutation was not denied")
    if (
        service.get("posture") != "LOCAL_FIXTURE"
        or service.get("external_network_contact") is not False
        or service.get("passive_http_enabled") is not False
        or service.get("programme_contacted") is not False
    ):
        raise CompositionError("service evidence crossed the local fixture boundary")
    policy_bytes = policy_path.read_bytes()
    record = {
        "schema_version": 1,
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "programme_contacted": False,
        "passive_http_enabled": False,
        "vps_used": False,
        "hardened_worker_image_accepted": False,
        "egress_policy": {
            "engine": "nftables",
            "table": "inet greytheory",
            "default_input": "drop",
            "default_forward": "drop",
            "default_output": "drop",
            "allowed": [
                {
                    "interface": "lo",
                    "family": "ipv4",
                    "address": "8.8.8.8",
                    "protocol": "tcp",
                    "port": 443,
                }
            ],
            "denied_probe_packets": denied_packets,
            "denied_probes": probes["probes"],
            "route_mutation_denied": True,
            "firewall_mutation_denied": True,
            "policy_sha256": hashlib.sha256(policy_bytes).hexdigest(),
            "policy_lifetime": "owned-network-namespace",
        },
        "network_namespace": network,
        "worker_service": service["worker_service"],
        "worker_namespace": service["namespace"],
        "tool_manifest": tool_manifest,
        "limits": {
            "proof_scope": "owned synthetic canary only",
            "image_binding": "not yet accepted",
            "programme_authority": "none",
        },
    }
    print(json.dumps(record, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
