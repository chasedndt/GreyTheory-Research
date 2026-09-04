from pathlib import Path

import pytest

from greytheory_intelligence import INTELLIGENCE_PROVIDERS, QueryKind, build_intelligence_plan


def test_public_intelligence_plan_is_non_executing_and_source_preserving() -> None:
    plan = build_intelligence_plan("epss", "cve-2024-3094")

    assert plan.query_kind is QueryKind.CVE
    assert plan.identifier == "CVE-2024-3094"
    assert plan.posture == "CONTRACT_ONLY"
    assert plan.executable is False
    assert plan.target_interaction is False
    assert plan.preserves_source is True


def test_package_queries_are_narrow_and_osv_only() -> None:
    plan = build_intelligence_plan("osv", "PyPI:requests@2.31.0")
    assert plan.query_kind is QueryKind.PACKAGE

    with pytest.raises(ValueError, match="does not accept package"):
        build_intelligence_plan("nvd", "PyPI:requests@2.31.0")


@pytest.mark.parametrize(
    "value",
    [
        "https://target.example",
        "target.example",
        "192.0.2.1",
        "scan:CVE-2024-3094",
        "CVE-24-1",
        "npm:package",
    ],
)
def test_target_shaped_and_malformed_identifiers_fail_closed(value: str) -> None:
    with pytest.raises(ValueError, match="identifier must be"):
        build_intelligence_plan("osv", value)


def test_provider_contracts_declare_bounded_read_only_surfaces() -> None:
    assert len(INTELLIGENCE_PROVIDERS) == 5
    assert all(set(provider.allowed_methods) <= {"GET", "POST"} for provider in INTELLIGENCE_PROVIDERS.values())
    assert all(provider.maximum_response_bytes <= 4_000_000 for provider in INTELLIGENCE_PROVIDERS.values())
    assert all(provider.data_class == "PUBLIC" for provider in INTELLIGENCE_PROVIDERS.values())

    source = Path("greytheory_intelligence/registry.py").read_text(encoding="utf-8")
    assert "urllib" not in source
    assert "requests" not in source
    assert "httpx" not in source
