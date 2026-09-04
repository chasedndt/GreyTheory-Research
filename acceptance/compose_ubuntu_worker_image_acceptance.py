"""Validate and compose read-only Ubuntu worker-image runtime evidence."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from acceptance.compose_ubuntu_egress_acceptance import (
    CompositionError,
    _required_ruleset,
    _validate_network,
)


def _json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CompositionError(f"invalid JSON evidence: {path.name}") from exc
    if not isinstance(payload, dict):
        raise CompositionError(f"JSON evidence must be an object: {path.name}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_build(manifest: dict[str, Any], image_path: Path) -> None:
    image = manifest.get("image", {})
    source = manifest.get("source", {})
    inputs = manifest.get("inputs", {})
    reproducibility = manifest.get("reproducibility", {})
    if (
        manifest.get("schema_version") != 1
        or image.get("name") != image_path.name
        or image.get("format") != "squashfs"
        or image.get("read_only_format") is not True
        or image.get("sha256") != _sha256(image_path)
        or image.get("bytes") != image_path.stat().st_size
        or not re.fullmatch(r"[0-9a-f]{40}", source.get("git_revision", ""))
        or image_path.parent.name != source.get("git_revision")
        or not re.fullmatch(r"[0-9a-f]{64}", source.get("tree_digest", ""))
        or source.get("dirty") is not False
        or any(
            not re.fullmatch(r"[0-9a-f]{64}", inputs.get(name, ""))
            for name in (
                "ubuntu_base_sha256",
                "package_lock_sha256",
                "image_contract_sha256",
                "archive_provenance_sha256",
            )
        )
        or reproducibility.get("independent_builds") != 2
        or reproducibility.get("byte_identical") is not True
        or manifest.get("runtime_accepted") is not False
        or manifest.get("hardened_worker_image_accepted") is not False
        or manifest.get("posture") != "LOCAL_FIXTURE"
        or manifest.get("external_network_contact") is not False
        or manifest.get("programme_contacted") is not False
        or manifest.get("passive_http_enabled") is not False
        or manifest.get("vps_used") is not False
    ):
        raise CompositionError("worker image build manifest is not acceptable")


def _validate_contract(
    contract: dict[str, Any], manifest: dict[str, Any], contract_path: Path
) -> None:
    expected_authority = {
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "programme_contacted": False,
        "passive_http_enabled": False,
        "vps_used": False,
    }
    image = contract.get("image", {})
    base = image.get("base", {})
    process = contract.get("process", {})
    network = contract.get("network", {})
    writable = {
        item.get("path"): item for item in contract.get("rootfs", {}).get(
            "writable_mounts", ()
        )
    }
    if (
        contract.get("schema_version") != 1
        or image.get("name") != "greytheory-passive-worker"
        or image.get("platform") != "linux"
        or image.get("architecture") != "amd64"
        or image.get("format") != "squashfs"
        or base
        != {
            "product": "Ubuntu Base",
            "release": "24.04.4",
            "archive": "ubuntu-base-24.04.4-base-amd64.tar.gz",
            "sha256": manifest.get("inputs", {}).get("ubuntu_base_sha256"),
            "signing_fingerprint": "843938DF228D22F7B3742BC0D94AA3F0EFE21092",
        }
        or manifest.get("inputs", {}).get("image_contract_sha256")
        != _sha256(contract_path)
        or contract.get("rootfs", {}).get("read_only") is not True
        or contract.get("admission", {}).get("verify_package_archive_signature")
        is not True
        or set(contract.get("rootfs", {}).get("required_mount_options", ()))
        != {"ro", "nodev", "nosuid"}
        or set(writable) != {"/tmp", "/run", "/dev"}
        or len(contract.get("rootfs", {}).get("writable_mounts", ())) != 3
        or set(writable["/tmp"].get("options", ()))
        != {"nodev", "nosuid", "noexec", "size=64M"}
        or set(writable["/run"].get("options", ()))
        != {"nodev", "nosuid", "noexec", "size=8M"}
        or set(writable["/dev"].get("options", ()))
        != {"nosuid", "noexec", "size=1M"}
        or writable["/dev"].get("device_allowlist")
        != ["full", "null", "random", "tty", "urandom", "zero"]
        or process
        != {
            "uid": 65534,
            "gid": 65534,
            "supplementary_groups": [],
            "no_new_privileges": True,
            "effective_capabilities": 0,
            "bounding_capabilities": 0,
            "environment_allowlist": [
                "HOME",
                "LANG",
                "PATH",
                "PYTHONDONTWRITEBYTECODE",
                "PYTHONPATH",
                "TMPDIR",
            ],
        }
        or network.get("engine") != "nftables"
        or network.get("policy") != "acceptance/fixtures/ubuntu-egress-policy.nft"
        or network.get("default_input") != "drop"
        or network.get("default_forward") != "drop"
        or network.get("default_output") != "drop"
        or network.get("allowed_fixture")
        != {
            "interface": "lo",
            "family": "ipv4",
            "address": "8.8.8.8",
            "protocol": "tcp",
            "port": 443,
        }
        or set(network.get("required_denials", ()))
        != {
            "allowed-address-wrong-port",
            "decoy-address-allowed-port",
            "ipv6-loopback-allowed-port",
            "route-mutation",
            "firewall-mutation",
        }
        or contract.get("authority") != expected_authority
        or contract.get("admission")
        != {
            "verify_base_signature": True,
            "verify_base_sha256": True,
            "verify_package_archive_signature": True,
            "verify_package_lock": True,
            "verify_image_sha256": True,
            "verify_read_only_root": True,
            "verify_network_policy": True,
            "verify_process_identity": True,
            "verify_worker_receipt": True,
        }
    ):
        raise CompositionError("worker image contract is not acceptable")


def _validate_supply_chain(
    manifest: dict[str, Any],
    package_lock: dict[str, Any],
    provenance: dict[str, Any],
    package_lock_path: Path,
    provenance_path: Path,
    keyring_path: Path,
) -> None:
    inputs = manifest.get("inputs", {})
    fingerprint = "F6ECB3762474EDA9D21B7022871920D1991BC93C"
    suites = ["noble", "noble-updates", "noble-security"]
    packages = package_lock.get("packages")
    if (
        inputs.get("package_lock_sha256") != _sha256(package_lock_path)
        or inputs.get("archive_provenance_sha256") != _sha256(provenance_path)
        or package_lock.get("schema_version") != 1
        or package_lock.get("release") != "24.04.4"
        or package_lock.get("architecture") != "amd64"
        or package_lock.get("archive_signing_fingerprint") != fingerprint
        or package_lock.get("archive_suites") != suites
        or not isinstance(packages, list)
        or len(packages) != 18
        or any(not isinstance(item, dict) for item in packages)
        or any(
            not isinstance(item.get("name"), str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9+.-]+", item["name"])
            or not isinstance(item.get("version"), str)
            or not re.fullmatch(r"[A-Za-z0-9.+:~_-]+", item["version"])
            or item.get("architecture") not in {"all", "amd64"}
            or not isinstance(item.get("filename"), str)
            or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9.+~_-]+[.]deb",
                item["filename"],
            )
            or not isinstance(item.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
            or not isinstance(item.get("url"), str)
            or not item["url"].startswith(
                "https://archive.ubuntu.com/ubuntu/pool/main/"
            )
            or item.get("filename") != item["url"].rsplit("/", 1)[-1]
            for item in packages
        )
        or provenance.get("schema_version") != 1
        or provenance.get("archive_signing_fingerprint") != fingerprint
        or provenance.get("archive_keyring_sha256") != _sha256(keyring_path)
    ):
        raise CompositionError("worker image supply-chain evidence is invalid")
    suite_evidence = provenance.get("suites")
    if (
        not isinstance(suite_evidence, list)
        or any(not isinstance(item, dict) for item in suite_evidence)
        or [item.get("suite") for item in suite_evidence] != suites
        or any(
            item.get("packages_index") != "main/binary-amd64/Packages.xz"
            or not isinstance(item.get("packages_index_bytes"), int)
            or item["packages_index_bytes"] <= 0
            or any(
                not re.fullmatch(r"[0-9a-f]{64}", item.get(field, ""))
                for field in (
                    "inrelease_sha256",
                    "release_sha256",
                    "packages_index_sha256",
                )
            )
            for item in suite_evidence
        )
    ):
        raise CompositionError("Ubuntu archive suite evidence is invalid")
    locked = {
        (
            item.get("name"),
            item.get("version"),
            item.get("architecture"),
            item.get("sha256"),
        )
        for item in packages
    }
    proven_items = provenance.get("packages")
    if (
        not isinstance(proven_items, list)
        or len(proven_items) != 18
        or any(not isinstance(item, dict) for item in proven_items)
    ):
        raise CompositionError("Ubuntu package provenance is incomplete")
    proven = {
        (
            item.get("name"),
            item.get("version"),
            item.get("architecture"),
            item.get("sha256"),
        )
        for item in proven_items
    }
    if (
        len(locked) != 18
        or proven != locked
        or any(
            not isinstance(item.get("suites"), list)
            or not item["suites"]
            or any(suite not in suites for suite in item["suites"])
            for item in proven_items
        )
    ):
        raise CompositionError("Ubuntu package provenance does not match the lock")


def _validate_runtime(runtime: dict[str, Any]) -> None:
    if (
        runtime.get("schema_version") != 1
        or runtime.get("posture") != "LOCAL_FIXTURE"
        or runtime.get("external_network_contact") is not False
        or runtime.get("programme_contacted") is not False
        or runtime.get("passive_http_enabled") is not False
        or runtime.get("vps_used") is not False
    ):
        raise CompositionError("image runtime crossed the local fixture boundary")
    image_runtime = runtime.get("image_runtime", {})
    security = image_runtime.get("security", {})
    if security != {
        "effective_uid": 65534,
        "effective_gid": 65534,
        "supplementary_groups": [],
        "effective_capabilities": 0,
        "bounding_capabilities": 0,
        "no_new_privileges": True,
    }:
        raise CompositionError("image runtime identity is not unprivileged")
    mounts = image_runtime.get("mounts", {})
    required_mounts = {
        "root": ("squashfs", {"ro", "nodev", "nosuid"}, None),
        "tmp": ("tmpfs", {"rw", "nodev", "nosuid", "noexec"}, "size=65536k"),
        "run": ("tmpfs", {"rw", "nodev", "nosuid", "noexec"}, "size=8192k"),
        "dev": ("tmpfs", {"rw", "nosuid", "noexec"}, "size=1024k"),
        "proc": ("proc", {"ro", "nodev", "nosuid", "noexec"}, None),
    }
    for name, (filesystem, options, size) in required_mounts.items():
        mount = mounts.get(name, {})
        actual_options = set(mount.get("mount_options", ())) | set(
            mount.get("super_options", ())
        )
        if mount.get("filesystem") != filesystem or not options.issubset(
            actual_options
        ) or (size is not None and size not in actual_options):
            raise CompositionError(f"image runtime mount is invalid: {name}")
    if image_runtime.get("devices") != [
        "full",
        "null",
        "random",
        "tty",
        "urandom",
        "zero",
    ]:
        raise CompositionError("image runtime device allowlist is invalid")
    if image_runtime.get("environment") != [
        "HOME",
        "LANG",
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONPATH",
        "TMPDIR",
    ]:
        raise CompositionError("image runtime environment allowlist is invalid")
    write_denials = image_runtime.get("write_denials")
    if not isinstance(write_denials, list) or len(write_denials) != 2 or any(
        item.get("denied") is not True for item in write_denials
    ):
        raise CompositionError("image root write-denial evidence is incomplete")
    if {item.get("path") for item in write_denials} != {
        "/etc/.greytheory-write-probe",
        "/opt/greytheory/.greytheory-write-probe",
    }:
        raise CompositionError("image write-denial paths are invalid")
    probes = runtime.get("egress_probes", {}).get("probes")
    expected_probes = {
        "allowed-address-wrong-port",
        "decoy-address-allowed-port",
        "ipv6-loopback-allowed-port",
    }
    if (
        not isinstance(probes, list)
        or {item.get("name") for item in probes} != expected_probes
        or any(item.get("connected") is not False for item in probes)
    ):
        raise CompositionError("image egress probe evidence is incomplete")
    service = runtime.get("worker_service", {})
    worker = service.get("worker_service", {})
    namespace = service.get("namespace", {})
    if (
        service.get("posture") != "LOCAL_FIXTURE"
        or service.get("external_network_contact") is not False
        or service.get("programme_contacted") is not False
        or service.get("passive_http_enabled") is not False
        or service.get("vps_used") is not False
        or service.get("root_kek_present") is not False
        or namespace.get("default_route") is not False
        or namespace.get("interfaces") != ["lo"]
        or worker.get("capture_encrypted") is not True
        or worker.get("receipt_signature_verified") is not True
        or worker.get("replay_state") != "completed"
        or worker.get("worker", {}).get("child_alive") is not False
        or worker.get("worker", {}).get("exitcode") != 0
        or worker.get("canary_request_exact") is not True
    ):
        raise CompositionError("full worker service did not complete inside the image")


def main(arguments: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if arguments is None else arguments)
    if len(args) != 12:
        raise CompositionError(
            "expected build manifest, image, runtime, ruleset, policy, network, "
            "route mutation, firewall mutation, image contract, package lock, "
            "package provenance, and archive keyring paths"
        )
    (
        manifest_path,
        image_path,
        runtime_path,
        ruleset_path,
        policy_path,
        network_path,
        route_mutation_path,
        firewall_mutation_path,
        contract_path,
        package_lock_path,
        provenance_path,
        keyring_path,
    ) = map(Path, args)
    manifest = _json(manifest_path)
    runtime = _json(runtime_path)
    network = _json(network_path)
    contract = _json(contract_path)
    package_lock = _json(package_lock_path)
    provenance = _json(provenance_path)
    _validate_build(manifest, image_path)
    _validate_contract(contract, manifest, contract_path)
    _validate_supply_chain(
        manifest,
        package_lock,
        provenance,
        package_lock_path,
        provenance_path,
        keyring_path,
    )
    _validate_runtime(runtime)
    _validate_network(network)
    denied_packets = _required_ruleset(ruleset_path.read_text(encoding="utf-8"))
    if route_mutation_path.read_text(encoding="ascii").strip() != "denied":
        raise CompositionError("image runtime allowed route mutation")
    if firewall_mutation_path.read_text(encoding="ascii").strip() != "denied":
        raise CompositionError("image runtime allowed firewall mutation")
    record = {
        "schema_version": 1,
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "programme_contacted": False,
        "passive_http_enabled": False,
        "vps_used": False,
        "image_runtime_accepted": True,
        "hardened_worker_image_accepted": False,
        "reboot_vm_conformance_accepted": False,
        "image": manifest["image"],
        "source": manifest["source"],
        "inputs": manifest["inputs"],
        "reproducibility": manifest["reproducibility"],
        "supply_chain": {
            "ubuntu_base_sha256": manifest["inputs"]["ubuntu_base_sha256"],
            "package_lock_sha256": manifest["inputs"]["package_lock_sha256"],
            "archive_provenance_sha256": manifest["inputs"][
                "archive_provenance_sha256"
            ],
            "archive_signing_fingerprint": provenance[
                "archive_signing_fingerprint"
            ],
            "archive_keyring_sha256": provenance["archive_keyring_sha256"],
            "archive_suites": [item["suite"] for item in provenance["suites"]],
            "package_count": len(provenance["packages"]),
        },
        "egress_policy": {
            "engine": "nftables",
            "default_input": "drop",
            "default_forward": "drop",
            "default_output": "drop",
            "denied_probe_packets": denied_packets,
            "route_mutation_denied": True,
            "firewall_mutation_denied": True,
            "policy_sha256": _sha256(policy_path),
        },
        "network_namespace": network,
        "image_runtime": runtime["image_runtime"],
        "worker_service": runtime["worker_service"]["worker_service"],
        "limits": {
            "proof_scope": "owned synthetic canary only",
            "programme_authority": "none",
            "reboot_vm_conformance": "not yet accepted",
            "broker_transport_authentication": "not yet accepted",
        },
    }
    print(json.dumps(record, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
