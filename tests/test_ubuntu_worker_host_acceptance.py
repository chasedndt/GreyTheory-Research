"""Static contract checks for the offline Ubuntu primitive acceptance harness."""

from __future__ import annotations

import ast
import hashlib
import json
import lzma
from pathlib import Path

import pytest
from cryptography import x509

from greytheory_broker import BrokerLimits


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "acceptance"


def test_ubuntu_acceptance_fixture_has_the_exact_test_only_identity():
    certificate = ACCEPTANCE / "fixtures" / "ubuntu-canary-cert.pem"
    private_key = ACCEPTANCE / "fixtures" / "ubuntu-canary-key.pem"
    decoded = x509.load_pem_x509_certificate(certificate.read_bytes())
    names = decoded.extensions.get_extension_for_class(
        x509.SubjectAlternativeName
    ).value.get_values_for_type(x509.DNSName)

    assert names == ["greytheory-canary.invalid"]
    assert private_key.read_text(encoding="ascii").startswith(
        "-----BEGIN PRIVATE KEY-----\n"
    )
    assert "test-only" in (ACCEPTANCE / "README.md").read_text(encoding="utf-8")


def test_ubuntu_acceptance_harness_is_offline_and_uses_production_primitives():
    path = ACCEPTANCE / "ubuntu_worker_host.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert {
        "greytheory_worker",
        "greytheory_worker_contract",
        "socket",
        "ssl",
        "multiprocessing",
    }.issubset(imported)
    assert imported.isdisjoint(
        {"aiohttp", "http.client", "httpx", "requests", "subprocess", "urllib.request"}
    )
    assert '"external_network_contact": False' in source
    assert '"passive_http_enabled": False' in source
    assert '"worker_service_assembled": False' in source


def test_windows_wrapper_creates_an_ephemeral_no_route_namespace():
    source = (ACCEPTANCE / "run-ubuntu-worker-host.ps1").read_text(encoding="utf-8")

    assert "unshare -Urn" in source
    assert "ip link set lo up" in source
    assert "ip addr add 8.8.8.8/32 dev lo" in source
    assert "PYTHONDONTWRITEBYTECODE=1" in source
    assert not any(token in source.lower() for token in ("curl ", "wget ", "invoke-webrequest"))


def test_full_worker_harness_assembles_only_the_owned_offline_path():
    path = ACCEPTANCE / "ubuntu_worker_service.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert {
        "greytheory_worker",
        "greytheory_broker",
        "socket",
        "ssl",
    }.issubset(imported)
    assert imported.isdisjoint(
        {"aiohttp", "http.client", "httpx", "requests", "subprocess", "urllib.request"}
    )
    assert '"external_network_contact": False' in source
    assert '"passive_http_enabled": False' in source
    assert '"worker_service_assembled": True' in source
    assert '"vps_used": False' in source
    assert '"root_kek_present": False' in source


def test_full_worker_canary_outlives_the_bounded_action_window():
    from acceptance import ubuntu_worker_service

    max_duration = BrokerLimits().max_duration_seconds

    assert ubuntu_worker_service.CANARY_ACCEPT_TIMEOUT_SECONDS > max_duration
    assert (
        ubuntu_worker_service.CANARY_FINISH_TIMEOUT_SECONDS
        > ubuntu_worker_service.CANARY_ACCEPT_TIMEOUT_SECONDS
    )


def test_full_worker_wrapper_drops_identity_and_capabilities_in_no_route_namespace():
    powershell = (ACCEPTANCE / "run-ubuntu-worker-service.ps1").read_text(
        encoding="utf-8"
    )
    shell = (ACCEPTANCE / "run-ubuntu-worker-service.sh").read_text(
        encoding="utf-8"
    )
    source = powershell + shell

    assert '"unshare", "-Urnm"' in powershell
    assert '"--user", "root"' in powershell
    assert "WaitForExit($TimeoutSeconds * 1000)" in powershell
    assert "$ownedProcessHandle = $process.Handle" in powershell
    assert "Get-OwnedWslDescendantIds" in powershell
    assert "Stop-Process -Id $ownedWslId" in powershell
    assert "-RedirectStandardOutput $recordPath" in powershell
    assert "ConvertFrom-Json" in powershell
    assert "$record.external_network_contact -ne $false" in powershell
    assert "$record.worker_service.receipt_signature_verified -ne $true" in powershell
    assert "--map-user=65534" in source
    assert "--map-group=65534" in source
    assert "--kill-child=KILL" in source
    assert "ip link set lo up" in source
    assert "ip addr add 8.8.8.8/32 dev lo" in source
    assert "--no-new-privs" in source
    assert "--bounding-set=-all" in source
    assert "--inh-caps=-all" in source
    assert "--ambient-caps=-all" in source
    assert "mount -t overlay overlay" in source
    assert "umount /etc/hosts" in shell
    assert 'mount --bind "$runtime_dir/hosts" /etc/hosts' in shell
    assert 'source_dir="$runtime_dir/source"' in shell
    assert "cp -a --" in shell
    assert 'cd "$source_dir"' in shell
    assert "greytheory-canary.invalid" in source
    assert "greytheory-canary.invalid." in shell
    assert '"bash", "acceptance/run-ubuntu-worker-service.sh"' in powershell
    assert "case \"$runtime_dir\" in" in shell
    assert not any(
        token in source.lower() for token in ("curl ", "wget ", "invoke-webrequest")
    )


def test_full_worker_shell_entrypoint_is_lf_on_windows_checkouts():
    shell_path = ACCEPTANCE / "run-ubuntu-worker-service.sh"
    attributes = (ACCEPTANCE.parent / ".gitattributes").read_text(encoding="utf-8")

    assert b"\r\n" not in shell_path.read_bytes()
    assert "*.sh text eol=lf" in attributes


def test_egress_policy_defaults_to_drop_and_allows_only_the_owned_fixture():
    policy = (ACCEPTANCE / "fixtures" / "ubuntu-egress-policy.nft").read_text(
        encoding="utf-8"
    )

    assert policy.count("policy drop") == 3
    assert 'oifname "lo" ip daddr 8.8.8.8 tcp dport 443 ct state new accept' in policy
    assert 'iifname "lo" ip daddr 8.8.8.8 tcp dport 443 ct state new accept' in policy
    assert "counter name denied_output reject" in policy
    assert "1.1.1.1" not in policy
    assert "flush ruleset" in policy


def test_egress_acceptance_uses_hash_locked_e_drive_tools_without_installing():
    stage = (ACCEPTANCE / "stage-ubuntu-nftables.sh").read_text(encoding="utf-8")
    shell = (ACCEPTANCE / "run-ubuntu-egress-policy.sh").read_text(
        encoding="utf-8"
    )
    powershell = (ACCEPTANCE / "run-ubuntu-egress-policy.ps1").read_text(
        encoding="utf-8"
    )
    checksum = (
        ACCEPTANCE / "fixtures" / "ubuntu-nftables-amd64.sha256"
    ).read_text(encoding="ascii")

    assert "apt-get download" in stage
    assert "apt-get install" not in stage
    assert "sha256sum --check" in stage
    assert checksum.count("_amd64.deb") == 5
    assert "GREYTHEORY_NFT_CACHE" in shell
    assert "sha256sum --check" in shell
    assert "unexpected package set" in shell
    assert 'for package in "${packages[@]}"' in shell
    assert "dpkg-deb -x" in shell
    assert '"unshare", "-Urnm"' in powershell
    assert '"--map-user=65534"' in powershell
    assert '"--map-group=65534"' in powershell
    assert "hardened_worker_image_accepted -ne $false" in powershell
    assert "denied_probe_packets -lt 3" in powershell
    assert not any(
        token in (stage + shell + powershell).lower()
        for token in ("curl ", "wget ", "invoke-webrequest", "apt-get install")
    )


def test_egress_probe_is_bounded_and_has_no_http_client():
    path = ACCEPTANCE / "ubuntu_egress_probe.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert {"socket", "time"}.issubset(imported)
    assert imported.isdisjoint(
        {"aiohttp", "http.client", "httpx", "requests", "subprocess", "urllib.request"}
    )
    assert "client.settimeout(1.0)" in source
    assert source.count("_denied_tcp_probe(") == 4


def test_egress_shell_entrypoints_are_lf_on_windows_checkouts():
    attributes = (ACCEPTANCE.parent / ".gitattributes").read_text(encoding="utf-8")
    for name in ("run-ubuntu-egress-policy.sh", "stage-ubuntu-nftables.sh"):
        assert b"\r\n" not in (ACCEPTANCE / name).read_bytes()
    assert "*.sh text eol=lf" in attributes


def test_worker_image_contract_keeps_authority_dark_and_root_read_only():
    contract = json.loads(
        (
            ACCEPTANCE / "fixtures" / "ubuntu-worker-image-contract.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["image"]["base"] == {
        "product": "Ubuntu Base",
        "release": "24.04.4",
        "archive": "ubuntu-base-24.04.4-base-amd64.tar.gz",
        "sha256": "c1e67ef7b17a6300e136118bd1dc04725009cb376c1aad10abcf8cd453628d58",
        "signing_fingerprint": "843938DF228D22F7B3742BC0D94AA3F0EFE21092",
    }
    assert contract["rootfs"]["read_only"] is True
    assert set(contract["rootfs"]["required_mount_options"]) == {
        "ro",
        "nodev",
        "nosuid",
    }
    assert contract["process"]["uid"] == 65534
    assert contract["process"]["gid"] == 65534
    assert contract["process"]["supplementary_groups"] == []
    assert contract["process"]["no_new_privileges"] is True
    assert contract["process"]["effective_capabilities"] == 0
    assert contract["process"]["bounding_capabilities"] == 0
    assert contract["authority"] == {
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "programme_contacted": False,
        "passive_http_enabled": False,
        "vps_used": False,
    }


def test_worker_image_staging_is_signed_pinned_and_never_binds_host_dev():
    shell = (ACCEPTANCE / "stage-ubuntu-worker-image.sh").read_text(
        encoding="utf-8"
    )
    powershell = (ACCEPTANCE / "stage-ubuntu-worker-image.ps1").read_text(
        encoding="utf-8"
    )
    base_checksum = (
        ACCEPTANCE / "fixtures" / "ubuntu-base-24.04.4-amd64.sha256"
    ).read_text(encoding="ascii")
    package_lock = json.loads(
        (
            ACCEPTANCE
            / "fixtures"
            / "ubuntu-worker-image-package-lock.json"
        ).read_text(encoding="utf-8")
    )

    assert "https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release" in shell
    assert "https://archive.ubuntu.com/ubuntu/project/ubuntu-archive-keyring.gpg" in shell
    assert "https://archive.ubuntu.com/ubuntu/pool/main/" in shell
    assert "843938DF228D22F7B3742BC0D94AA3F0EFE21092" in shell
    assert "F6ECB3762474EDA9D21B7022871920D1991BC93C" in shell
    assert "gpgv --status-fd 1" in shell
    assert "[GNUPG:] VALIDSIG $signing_fingerprint" in shell
    assert "[GNUPG:] VALIDSIG $archive_signing_fingerprint" in shell
    assert "Pinned Ubuntu base digest is absent from the signed checksum set" in shell
    assert "main/binary-amd64/Packages.xz" in shell
    verifier = (ACCEPTANCE / "verify_ubuntu_archive_packages.py").read_text(
        encoding="utf-8"
    )
    assert "signed Packages index mismatch" in verifier
    assert "package is absent from signed archive metadata" in verifier
    assert "sha256sum --check" in shell
    assert "dpkg-deb -f" in shell
    assert "unexpected package set" in shell
    assert not any(
        token in shell
        for token in ("mount ", "chroot ", "mknod ", "apt-get ", "rootfs/dev")
    )
    assert base_checksum.startswith(
        "c1e67ef7b17a6300e136118bd1dc04725009cb376c1aad10abcf8cd453628d58  "
    )
    assert package_lock["schema_version"] == 1
    assert package_lock["release"] == "24.04.4"
    assert package_lock["architecture"] == "amd64"
    assert package_lock["archive_signing_fingerprint"] == (
        "F6ECB3762474EDA9D21B7022871920D1991BC93C"
    )
    assert package_lock["archive_suites"] == [
        "noble",
        "noble-updates",
        "noble-security",
    ]
    assert len(package_lock["packages"]) == 18
    assert len({item["name"] for item in package_lock["packages"]}) == 18
    assert all(
        item["url"].startswith("https://archive.ubuntu.com/ubuntu/pool/main/")
        for item in package_lock["packages"]
    )
    assert all(len(item["sha256"]) == 64 for item in package_lock["packages"])
    assert "unshare" not in powershell
    assert "Get-OwnedWslDescendantIds" in powershell
    assert "WaitForExit($TimeoutSeconds * 1000)" in powershell
    assert "Stop-Process -Id $ownedWslId" in powershell


def test_worker_image_shell_entrypoint_is_lf_on_windows_checkouts():
    attributes = (ACCEPTANCE.parent / ".gitattributes").read_text(encoding="utf-8")

    for name in (
        "stage-ubuntu-worker-image.sh",
        "build-ubuntu-worker-image.sh",
        "run-ubuntu-worker-image.sh",
    ):
        assert b"\r\n" not in (ACCEPTANCE / name).read_bytes()
    assert "*.sh text eol=lf" in attributes


def test_worker_image_builder_requires_two_identical_read_only_builds():
    shell = (ACCEPTANCE / "build-ubuntu-worker-image.sh").read_text(
        encoding="utf-8"
    )
    powershell = (ACCEPTANCE / "build-ubuntu-worker-image.ps1").read_text(
        encoding="utf-8"
    )

    assert "Release image builds require a clean, committed source tree" in shell
    assert "build_one a" in shell
    assert "build_one b" in shell
    assert 'image_a="$build_root/a.squashfs"' in shell
    assert 'image_b="$build_root/b.squashfs"' in shell
    assert "find . -xdev -mindepth 1" in shell
    assert 'if test "$digest_a" != "$digest_b"' in shell
    assert "Independent image builds were not byte-for-byte reproducible" in shell
    assert "mksquashfs" in shell
    assert "-all-time 0" in shell
    assert "-mkfs-time 0" in shell
    assert "-no-xattrs" in shell
    assert "/bin/sh -c '/usr/bin/dpkg --unpack /packages/*.deb'" in shell
    assert "dpkg --configure -a" in shell
    assert "verify_locked_packages" in shell
    assert "git archive --format=tar HEAD" in shell
    assert 'if test "$build_mode" = "release"' in shell
    assert 'final_provenance="$final_root/package-provenance.json"' in shell
    assert "Refusing to replace provenance for the same source identity" in shell
    assert 'final_supply_chain="$final_root/supply-chain"' in shell
    assert "Refusing an invalid supply-chain bundle" in shell
    assert "refusing to replace a build manifest for the same source identity" in shell
    assert "rm -rf -- \"$rootfs/etc/apt\"" in shell
    assert "find \"$rootfs\" -xdev -perm /6000 -exec chmod a-s" in shell
    assert "mount --rbind /dev" not in shell
    assert "umount --recursive \"$root\"" in shell
    assert '"unshare", "-m", "--propagation", "private"' in powershell
    assert "WaitForExit($TimeoutSeconds * 1000)" in powershell
    assert '"timeout", "--foreground", "--signal=TERM"' in powershell
    assert "$record.runtime_accepted -ne $false" in powershell
    assert "$record.hardened_worker_image_accepted -ne $false" in powershell


def test_worker_image_scripts_normalize_linked_windows_worktree_git_context():
    for name in (
        "build-ubuntu-worker-image.sh",
        "run-ubuntu-worker-image.sh",
    ):
        shell = (ACCEPTANCE / name).read_text(encoding="utf-8")

        assert "configure_repository_git" in shell
        assert 'wslpath -u "$git_dir"' in shell
        assert 'export GIT_DIR="$git_dir"' in shell
        assert 'export GIT_WORK_TREE="$repo_root"' in shell
        assert "GIT_CONFIG_KEY_0=core.autocrlf" in shell
        assert "GIT_CONFIG_VALUE_0=true" in shell
        assert "GIT_CONFIG_KEY_1=core.filemode" in shell
        assert "GIT_CONFIG_VALUE_1=false" in shell


def test_worker_image_entrypoint_parses_and_requires_the_mount_contract():
    from acceptance.ubuntu_worker_image_entrypoint import _parse_mountinfo

    mounts = _parse_mountinfo(
        "36 25 0:31 / / ro,nosuid,nodev - squashfs image ro\n"
        "37 36 0:32 / /tmp rw,nosuid,nodev,noexec - tmpfs tmpfs rw,size=65536k\n"
    )

    assert mounts["/"]["filesystem"] == "squashfs"
    assert {"ro", "nosuid", "nodev"}.issubset(mounts["/"]["mount_options"])
    assert mounts["/tmp"]["filesystem"] == "tmpfs"
    assert "size=65536k" in mounts["/tmp"]["super_options"]


def test_worker_image_entrypoint_runs_only_owned_local_acceptance():
    path = ACCEPTANCE / "ubuntu_worker_image_entrypoint.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert {
        "acceptance",
        "contextlib",
        "json",
        "os",
        "platform",
    }.issubset(imported)
    assert imported.isdisjoint(
        {"aiohttp", "http.client", "httpx", "requests", "subprocess", "urllib.request"}
    )
    assert '"posture": "LOCAL_FIXTURE"' in source
    assert '"external_network_contact": False' in source
    assert '"programme_contacted": False' in source
    assert '"passive_http_enabled": False' in source
    assert '"vps_used": False' in source
    assert "ubuntu_egress_probe.main" in source
    assert "ubuntu_worker_service.main" in source
    assert 'filesystem="squashfs"' in source
    assert source.count("_assert_write_denied(") == 3


def test_worker_image_runtime_mounts_only_bounded_owned_filesystems():
    shell = (ACCEPTANCE / "run-ubuntu-worker-image.sh").read_text(
        encoding="utf-8"
    )
    powershell = (ACCEPTANCE / "run-ubuntu-worker-image.ps1").read_text(
        encoding="utf-8"
    )
    source = shell + powershell

    assert "Ubuntu worker-image runtime acceptance requires a clean" in powershell
    assert '"unshare", "--mount", "--net", "--fork"' in powershell
    assert '"timeout", "--foreground", "--signal=TERM"' in powershell
    assert '"--user", "root"' in powershell
    assert "--map-user" not in powershell
    assert "mount --make-rprivate /" in shell
    assert "mount -t squashfs -o loop,ro,nodev,nosuid" in shell
    assert "size=64M,nodev,nosuid,noexec" in shell
    assert "size=8M,nodev,nosuid,noexec" in shell
    assert "size=1M,nosuid,noexec" in shell
    assert shell.count("mknod -m 666") == 6
    assert "mount --rbind /dev" not in shell
    assert "umount --recursive \"$rootfs\"" in shell
    assert "chroot \"$rootfs\" /usr/bin/setpriv" in shell
    assert "--reuid=65534 --regid=65534 --clear-groups" in shell
    assert "/usr/bin/env -i" in shell
    assert "GREYTHEORY_IMAGE_DIR" in source
    assert 'provenance="$image_dir/package-provenance.json"' in shell
    assert "gpgv --status-fd 1" in shell
    assert "cmp --silent \"$provenance\"" in shell
    assert "$record.image_runtime_accepted -ne $true" in powershell
    assert "$record.hardened_worker_image_accepted -ne $false" in powershell
    assert not any(
        token in source.lower()
        for token in ("curl ", "wget ", "invoke-webrequest", "apt-get")
    )


def test_worker_image_composer_accepts_only_bound_clean_runtime(
    tmp_path, capsys
):
    from acceptance.compose_ubuntu_worker_image_acceptance import (
        CompositionError,
        _validate_build,
        _validate_runtime,
        main,
    )

    revision = "a" * 40
    image_root = tmp_path / revision
    image_root.mkdir()
    image = image_root / "greytheory-passive-worker-amd64.squashfs"
    image.write_bytes(b"deterministic-image-fixture")
    contract_source = ACCEPTANCE / "fixtures" / "ubuntu-worker-image-contract.json"
    contract = image_root / "ubuntu-worker-image-contract.json"
    contract.write_bytes(contract_source.read_bytes())
    contract_payload = json.loads(contract.read_text(encoding="utf-8"))
    package_lock_source = (
        ACCEPTANCE / "fixtures" / "ubuntu-worker-image-package-lock.json"
    )
    package_lock = image_root / "ubuntu-worker-image-package-lock.json"
    package_lock.write_bytes(package_lock_source.read_bytes())
    package_lock_payload = json.loads(package_lock.read_text(encoding="utf-8"))
    keyring = image_root / "ubuntu-archive-keyring.gpg"
    keyring.write_bytes(b"fixture-keyring")
    provenance_payload = {
        "schema_version": 1,
        "archive_signing_fingerprint": package_lock_payload[
            "archive_signing_fingerprint"
        ],
        "archive_keyring_sha256": hashlib.sha256(keyring.read_bytes()).hexdigest(),
        "suites": [
            {
                "suite": suite,
                "inrelease_sha256": "1" * 64,
                "release_sha256": "2" * 64,
                "packages_index": "main/binary-amd64/Packages.xz",
                "packages_index_sha256": "3" * 64,
                "packages_index_bytes": 1,
            }
            for suite in package_lock_payload["archive_suites"]
        ],
        "packages": [
            {
                "name": item["name"],
                "version": item["version"],
                "architecture": item["architecture"],
                "sha256": item["sha256"],
                "suites": ["noble"],
            }
            for item in package_lock_payload["packages"]
        ],
    }
    provenance = image_root / "package-provenance.json"
    provenance.write_text(json.dumps(provenance_payload), encoding="utf-8")
    manifest_payload = {
        "schema_version": 1,
        "image": {
            "name": image.name,
            "format": "squashfs",
            "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            "bytes": image.stat().st_size,
            "read_only_format": True,
        },
        "source": {
            "git_revision": revision,
            "tree_digest": "b" * 64,
            "dirty": False,
        },
        "inputs": {
            "ubuntu_base_sha256": contract_payload["image"]["base"]["sha256"],
            "package_lock_sha256": hashlib.sha256(package_lock.read_bytes()).hexdigest(),
            "image_contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
            "archive_provenance_sha256": hashlib.sha256(
                provenance.read_bytes()
            ).hexdigest(),
        },
        "reproducibility": {"independent_builds": 2, "byte_identical": True},
        "runtime_accepted": False,
        "hardened_worker_image_accepted": False,
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "programme_contacted": False,
        "passive_http_enabled": False,
        "vps_used": False,
    }
    runtime_payload = {
        "schema_version": 1,
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "programme_contacted": False,
        "passive_http_enabled": False,
        "vps_used": False,
        "image_runtime": {
            "security": {
                "effective_uid": 65534,
                "effective_gid": 65534,
                "supplementary_groups": [],
                "effective_capabilities": 0,
                "bounding_capabilities": 0,
                "no_new_privileges": True,
            },
            "mounts": {
                "root": {
                    "filesystem": "squashfs",
                    "mount_options": ["ro", "nodev", "nosuid"],
                    "super_options": [],
                },
                "tmp": {
                    "filesystem": "tmpfs",
                    "mount_options": ["rw", "nodev", "nosuid", "noexec"],
                    "super_options": ["size=65536k"],
                },
                "run": {
                    "filesystem": "tmpfs",
                    "mount_options": ["rw", "nodev", "nosuid", "noexec"],
                    "super_options": ["size=8192k"],
                },
                "dev": {
                    "filesystem": "tmpfs",
                    "mount_options": ["rw", "nosuid", "noexec"],
                    "super_options": ["size=1024k"],
                },
                "proc": {
                    "filesystem": "proc",
                    "mount_options": ["ro", "nodev", "nosuid", "noexec"],
                    "super_options": [],
                },
            },
            "devices": ["full", "null", "random", "tty", "urandom", "zero"],
            "write_denials": [
                {"path": "/etc/.greytheory-write-probe", "denied": True},
                {
                    "path": "/opt/greytheory/.greytheory-write-probe",
                    "denied": True,
                },
            ],
            "environment": [
                "HOME",
                "LANG",
                "PATH",
                "PYTHONDONTWRITEBYTECODE",
                "PYTHONPATH",
                "TMPDIR",
            ],
        },
        "egress_probes": {
            "probes": [
                {"name": "allowed-address-wrong-port", "connected": False},
                {"name": "decoy-address-allowed-port", "connected": False},
                {"name": "ipv6-loopback-allowed-port", "connected": False},
            ]
        },
        "worker_service": {
            "posture": "LOCAL_FIXTURE",
            "external_network_contact": False,
            "programme_contacted": False,
            "passive_http_enabled": False,
            "vps_used": False,
            "root_kek_present": False,
            "namespace": {"default_route": False, "interfaces": ["lo"]},
            "worker_service": {
                "capture_encrypted": True,
                "receipt_signature_verified": True,
                "replay_state": "completed",
                "worker": {"child_alive": False, "exitcode": 0},
                "canary_request_exact": True,
            },
        },
    }
    network_payload = {
        "links": [{"ifname": "lo"}],
        "addresses": [
            {
                "addr_info": [
                    {"local": "127.0.0.1"},
                    {"local": "::1"},
                    {"local": "8.8.8.8"},
                    {"local": "1.1.1.1"},
                ]
            }
        ],
        "routes": [
            {"dst": address, "dev": "lo"}
            for address in ("127.0.0.0/8", "::1", "8.8.8.8", "1.1.1.1")
        ],
    }
    ruleset = """
table inet greytheory {
 counter denied_output { packets 3 bytes 180 }
 chain input { type filter hook input priority filter; policy drop;
  ip daddr 8.8.8.8 tcp dport 443 ct state new accept }
 chain forward { type filter hook forward priority filter; policy drop; }
 chain output { type filter hook output priority filter; policy drop;
  ip daddr 8.8.8.8 tcp dport 443 ct state new accept
  counter name "denied_output" reject }
}
"""

    paths = {}
    for name, payload in (
        ("manifest", manifest_payload),
        ("runtime", runtime_payload),
        ("network", network_payload),
    ):
        paths[name] = image_root / f"{name}.json"
        paths[name].write_text(json.dumps(payload), encoding="utf-8")
    paths["ruleset"] = image_root / "ruleset.txt"
    paths["ruleset"].write_text(ruleset, encoding="utf-8")
    paths["route"] = image_root / "route.txt"
    paths["route"].write_text("denied\n", encoding="ascii")
    paths["firewall"] = image_root / "firewall.txt"
    paths["firewall"].write_text("denied\n", encoding="ascii")

    arguments = [
        str(paths["manifest"]),
        str(image),
        str(paths["runtime"]),
        str(paths["ruleset"]),
        str(ACCEPTANCE / "fixtures" / "ubuntu-egress-policy.nft"),
        str(paths["network"]),
        str(paths["route"]),
        str(paths["firewall"]),
        str(contract),
        str(package_lock),
        str(provenance),
        str(keyring),
    ]
    assert main(arguments) == 0
    record = json.loads(capsys.readouterr().out)

    assert record["image_runtime_accepted"] is True
    assert record["hardened_worker_image_accepted"] is False
    assert record["reboot_vm_conformance_accepted"] is False
    assert record["posture"] == "LOCAL_FIXTURE"
    assert record["egress_policy"]["denied_probe_packets"] == 3
    assert record["supply_chain"]["package_count"] == 18

    manifest_payload["source"]["dirty"] = True
    with pytest.raises(CompositionError, match="build manifest"):
        _validate_build(manifest_payload, image)
    runtime_payload["image_runtime"]["devices"].append("ptmx")
    with pytest.raises(CompositionError, match="device allowlist"):
        _validate_runtime(runtime_payload)
    keyring.write_bytes(b"tampered-keyring")
    with pytest.raises(CompositionError, match="supply-chain evidence"):
        main(arguments)


def test_worker_package_provenance_binds_lock_to_signed_index_hashes(tmp_path):
    from acceptance.verify_ubuntu_archive_packages import (
        ArchiveVerificationError,
        EXPECTED_FINGERPRINT,
        EXPECTED_SUITES,
        verify,
    )

    filename = "pool/main/f/fixture/fixture_1.0_amd64.deb"
    package_digest = "1" * 64
    package_index = lzma.compress(
        (
            "Package: fixture\n"
            "Version: 1.0\n"
            "Architecture: amd64\n"
            f"Filename: {filename}\n"
            f"SHA256: {package_digest}\n\n"
        ).encode("utf-8")
    )
    for suite in EXPECTED_SUITES:
        suite_root = tmp_path / "metadata" / suite
        suite_root.mkdir(parents=True)
        (suite_root / "InRelease").write_bytes(f"signed:{suite}".encode())
        (suite_root / "Packages.xz").write_bytes(package_index)
        (suite_root / "Release").write_text(
            "SHA256:\n"
            f" {hashlib.sha256(package_index).hexdigest()} "
            f"{len(package_index)} main/binary-amd64/Packages.xz\n",
            encoding="utf-8",
        )
    lock = tmp_path / "lock.json"
    lock.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "release": "24.04.4",
                "architecture": "amd64",
                "archive_signing_fingerprint": EXPECTED_FINGERPRINT,
                "archive_suites": EXPECTED_SUITES,
                "packages": [
                    {
                        "name": "fixture",
                        "version": "1.0",
                        "architecture": "amd64",
                        "url": "https://archive.ubuntu.com/ubuntu/" + filename,
                        "sha256": package_digest,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    keyring = tmp_path / "archive-keyring.gpg"
    keyring.write_bytes(b"fixture-keyring")
    record = verify(lock, tmp_path / "metadata", EXPECTED_FINGERPRINT, keyring)

    assert [item["suite"] for item in record["suites"]] == EXPECTED_SUITES
    assert record["packages"][0]["suites"] == EXPECTED_SUITES
    (tmp_path / "metadata" / "noble" / "Packages.xz").write_bytes(b"tampered")
    with pytest.raises(ArchiveVerificationError, match="signed Packages index"):
        verify(lock, tmp_path / "metadata", EXPECTED_FINGERPRINT, keyring)
