"""Static contract checks for the offline Ubuntu primitive acceptance harness."""

from __future__ import annotations

import ast
from pathlib import Path

from cryptography import x509


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
