"""Capability truth shared by the dashboard and future workbench."""

from greytheory.capabilities import (
    CAPABILITIES,
    CapabilityStatus,
    capabilities_with_status,
    capability,
)


def test_capability_ids_are_unique_and_stable():
    ids = [item.id for item in CAPABILITIES]
    assert len(ids) == len(set(ids))
    assert all(identifier and identifier == identifier.lower() for identifier in ids)


def test_current_offline_collectors_do_not_imply_a_web_lane():
    assert capability("lane_1_dependency").status is CapabilityStatus.LIVE
    assert capability("lane_2_exposure").status is CapabilityStatus.LIVE
    assert capability("lane_3_web").status is CapabilityStatus.UNAVAILABLE
    assert capability("lane_4_agent_config").status is CapabilityStatus.LIVE
    assert "network" in capability("lane_3_web").boundary.lower()


def test_offline_scope_watch_and_external_collection_are_separate():
    assert capability("scope_watch_offline").status is CapabilityStatus.LIVE
    assert capability("scope_watch_collector").status is CapabilityStatus.UNAVAILABLE
    assert "no network fetch" in capability("scope_watch_offline").boundary.lower()


def test_learning_core_does_not_overstate_guided_or_adaptive_learning():
    assert capability("learning_core").status is CapabilityStatus.LIVE
    guided = capability("guided_learning")
    assert guided.status is CapabilityStatus.PARTIAL
    assert "not built" in guided.boundary.lower()


def test_application_service_is_partial_while_ui_and_passive_http_remain_unimplemented():
    application = capability("workbench_application_service")
    assert application.status is CapabilityStatus.PARTIAL
    assert "action and report" in application.boundary.lower()
    assert "typed but refused" in application.boundary.lower()
    assert "configured local operator" in application.boundary.lower()
    transport = capability("local_workbench_transport")
    assert transport.status is CapabilityStatus.PARTIAL
    assert "numeric-loopback" in transport.detail.lower()
    assert "no graphical shell" in transport.boundary.lower()
    assert capability("graphical_workbench").status is CapabilityStatus.PLANNED
    broker = capability("passive_broker_foundation")
    assert broker.status is CapabilityStatus.PARTIAL
    assert "no dns resolver" in broker.boundary.lower()
    assert capability("passive_http_worker").status is CapabilityStatus.UNAVAILABLE
    assert "passive_http remains dark" in capability("passive_http_worker").boundary.lower()


def test_status_filter_preserves_register_order():
    unavailable = capabilities_with_status(CapabilityStatus.UNAVAILABLE)
    assert tuple(item.id for item in unavailable) == (
        "lane_3_web",
        "scope_watch_collector",
        "passive_http_worker",
    )


def test_unknown_capability_fails_explicitly():
    try:
        capability("imaginary")
    except KeyError as exc:
        assert "unknown capability: imaginary" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("unknown capabilities must fail explicitly")
