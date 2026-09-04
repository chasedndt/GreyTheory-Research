"""Static contract checks for the offline Ubuntu primitive acceptance harness."""

from __future__ import annotations

import ast
from pathlib import Path

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
