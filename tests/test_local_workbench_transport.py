"""Local runtime and loopback transport acceptance without target access."""

from __future__ import annotations

import ast
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory_local import (
    MAX_REQUEST_BYTES,
    LocalRuntimeError,
    LocalTransportError,
    LocalWorkbenchHTTPServer,
    LocalWorkbenchRuntime,
    prepare_workbench_root,
)
from greytheory_app import (
    CommandField,
    CommandKind,
    WorkbenchCommand,
    WorkbenchContractError,
)


NOW = datetime(2026, 8, 25, 1, 30, tzinfo=timezone.utc)
TOKEN = "t" * 32


@contextmanager
def running_server(runtime: LocalWorkbenchRuntime):
    server = LocalWorkbenchHTTPServer(runtime.service, port=0, token=TOKEN)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def request(
    server: LocalWorkbenchHTTPServer,
    method: str,
    path: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict, dict[str, str]]:
    connection = HTTPConnection(server.host, server.port, timeout=5)
    merged = {"Host": server.expected_host_header, **(headers or {})}
    connection.request(method, path, body=body, headers=merged)
    response = connection.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    response_headers = {name.lower(): value for name, value in response.getheaders()}
    connection.close()
    return response.status, payload, response_headers


def learning_command() -> WorkbenchCommand:
    return WorkbenchCommand(
        id="transport-learning-start",
        kind=CommandKind.START_LEARNING_JOURNEY,
        operator_ref="operator-local",
        issued_at=NOW,
        idempotency_key="transport-learning-start",
        fields=(CommandField("journey_id", "journey-transport-1"),),
    )


def test_workbench_command_json_round_trip_is_strict():
    command = learning_command()
    assert WorkbenchCommand.from_dict(command.to_dict()) == command
    with pytest.raises(WorkbenchContractError, match="unexpected"):
        WorkbenchCommand.from_dict({**command.to_dict(), "authority_ref": "user-input"})
    with pytest.raises(WorkbenchContractError, match="executable false"):
        WorkbenchCommand.from_dict({**command.to_dict(), "executable": True})
    with pytest.raises(WorkbenchContractError, match="must be text"):
        WorkbenchCommand.from_dict({**command.to_dict(), "operator_ref": 7})


def test_private_runtime_root_is_outside_git_and_assembles_real_stores(tmp_path):
    repository_root = Path(__file__).resolve().parents[1]
    with pytest.raises(LocalRuntimeError, match="Git worktree"):
        prepare_workbench_root(repository_root / ".unsafe-workbench")

    runtime = LocalWorkbenchRuntime.assemble(tmp_path / "private-workbench")
    snapshot = runtime.service.snapshot()

    assert runtime.root == (tmp_path / "private-workbench").resolve()
    assert snapshot.posture is AuthorityLevel.LOCAL_FIXTURE
    assert snapshot.live_target_available is False
    assert snapshot.section("research").status.value == "empty"
    assert snapshot.section("reports").status.value == "empty"
    assert snapshot.section("learning").records[0].id.startswith("recommendation:")
    assert (runtime.root / "evidence" / "raw").is_dir()


def test_transport_refuses_every_non_loopback_binding(tmp_path):
    runtime = LocalWorkbenchRuntime.assemble(tmp_path / "private-workbench")
    for host in ("0.0.0.0", "localhost", "::1"):
        with pytest.raises(LocalTransportError, match="numeric IPv4 loopback"):
            LocalWorkbenchHTTPServer(runtime.service, host=host, token=TOKEN)


def test_local_launch_package_has_no_target_client_or_process_adapter():
    root = Path(__file__).resolve().parents[1] / "greytheory_local"
    modules: set[str] = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
    forbidden = {
        "aiohttp",
        "http.client",
        "httpx",
        "requests",
        "subprocess",
        "urllib.request",
        "webbrowser",
    }
    assert modules.isdisjoint(forbidden)
    assert "http.server" in modules


def test_loopback_transport_requires_exact_host_token_and_origin(tmp_path):
    runtime = LocalWorkbenchRuntime.assemble(tmp_path / "private-workbench")
    with running_server(runtime) as server:
        status, health, headers = request(server, "GET", "/healthz")
        assert status == 200
        assert health == {
            "live_target_available": False,
            "posture": "LOCAL_FIXTURE",
            "status": "ok",
        }
        assert headers["cache-control"] == "no-store"
        assert "access-control-allow-origin" not in headers

        status, denied, _ = request(server, "GET", "/api/v1/snapshot")
        assert status == 401
        assert denied["error"]["code"] == "authentication_required"

        status, refused_host, _ = request(
            server,
            "GET",
            "/healthz",
            headers={"Host": "attacker.invalid"},
        )
        assert status == 400
        assert refused_host["error"]["code"] == "host_refused"

        duplicate_host = HTTPConnection(server.host, server.port, timeout=5)
        duplicate_host.putrequest("GET", "/healthz", skip_host=True)
        duplicate_host.putheader("Host", server.expected_host_header)
        duplicate_host.putheader("Host", "attacker.invalid")
        duplicate_host.endheaders()
        duplicate_response = duplicate_host.getresponse()
        duplicate_payload = json.loads(duplicate_response.read().decode("utf-8"))
        assert duplicate_response.status == 400
        assert duplicate_payload["error"]["code"] == "host_refused"
        duplicate_host.close()

        auth = {"Authorization": f"Bearer {TOKEN}"}
        status, snapshot, _ = request(
            server, "GET", "/api/v1/snapshot", headers=auth
        )
        assert status == 200
        assert snapshot["posture"] == "LOCAL_FIXTURE"
        assert snapshot["live_target_available"] is False

        body = json.dumps(learning_command().to_dict()).encode("utf-8")
        post_headers = {**auth, "Content-Type": "application/json"}
        status, refused_origin, _ = request(
            server,
            "POST",
            "/api/v1/commands",
            body=body,
            headers=post_headers,
        )
        assert status == 403
        assert refused_origin["error"]["code"] == "origin_refused"

        status, accepted, _ = request(
            server,
            "POST",
            "/api/v1/commands",
            body=body,
            headers={**post_headers, "Origin": server.base_url},
        )
        assert status == 200
        assert accepted["disposition"] == "accepted"
        assert accepted["executed"] is False
        assert len(runtime.service.journeys.journeys()) == 1


def test_transport_rejects_oversized_or_non_json_commands_before_dispatch(tmp_path):
    runtime = LocalWorkbenchRuntime.assemble(tmp_path / "private-workbench")
    with running_server(runtime) as server:
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Origin": server.base_url,
            "Content-Type": "application/json",
        }
        connection = HTTPConnection(server.host, server.port, timeout=5)
        connection.putrequest("POST", "/api/v1/commands", skip_host=True)
        connection.putheader("Host", server.expected_host_header)
        connection.putheader("Authorization", f"Bearer {TOKEN}")
        connection.putheader("Origin", server.base_url)
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(MAX_REQUEST_BYTES + 1))
        connection.endheaders()
        oversized_response = connection.getresponse()
        oversized = json.loads(oversized_response.read().decode("utf-8"))
        assert oversized_response.status == 413
        assert oversized["error"]["code"] == "request_too_large"
        connection.close()

        status, content_type, _ = request(
            server,
            "POST",
            "/api/v1/commands",
            body=b"{}",
            headers={**headers, "Content-Type": "text/plain"},
        )
        assert status == 415
        assert content_type["error"]["code"] == "content_type_refused"

        status, duplicate_json, _ = request(
            server,
            "POST",
            "/api/v1/commands",
            body=b'{"id":"one","id":"two"}',
            headers=headers,
        )
        assert status == 400
        assert duplicate_json["error"]["code"] == "invalid_command"
        assert "duplicate JSON key" in duplicate_json["error"]["message"]
        assert runtime.service.journeys.journeys() == ()
