"""Authenticated numeric-loopback JSON transport for the local workbench."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hmac
import json
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

from greytheory.authority.gate import AuthorityLevel
from greytheory_app import (
    CommandDisposition,
    WorkbenchApplicationService,
    WorkbenchCommand,
    WorkbenchContractError,
)


LOOPBACK_HOST = "127.0.0.1"
MAX_REQUEST_BYTES = 65_536


class LocalTransportError(ValueError):
    """Raised when transport configuration could widen local access."""


class LocalWorkbenchHTTPServer(ThreadingHTTPServer):
    """One in-process workbench server with no target-network adapter."""

    allow_reuse_address = False
    daemon_threads = True

    def __init__(
        self,
        service: WorkbenchApplicationService,
        *,
        host: str = LOOPBACK_HOST,
        port: int = 0,
        token: str | None = None,
        allowed_ui_origin: str | None = None,
    ) -> None:
        if host != LOOPBACK_HOST:
            raise LocalTransportError(
                "the pilot transport binds only to numeric IPv4 loopback 127.0.0.1"
            )
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65_535:
            raise LocalTransportError("port must be an integer from 0 through 65535")
        session_token = token or secrets.token_urlsafe(32)
        if len(session_token) < 32 or any(character.isspace() for character in session_token):
            raise LocalTransportError(
                "the in-memory workbench token must contain at least 32 non-space characters"
            )
        self.service = service
        self.session_token = session_token
        self.allowed_ui_origin = _validate_ui_origin(allowed_ui_origin)
        super().__init__((host, port), LocalWorkbenchRequestHandler)

    @property
    def host(self) -> str:
        return str(self.server_address[0])

    @property
    def port(self) -> int:
        return int(self.server_address[1])

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def expected_host_header(self) -> str:
        return f"{self.host}:{self.port}"

    def authorised(self, value: str | None) -> bool:
        expected = f"Bearer {self.session_token}"
        return bool(value) and hmac.compare_digest(str(value), expected)

    def get_request(self):
        request, client_address = super().get_request()
        request.settimeout(5.0)
        return request, client_address


class LocalWorkbenchRequestHandler(BaseHTTPRequestHandler):
    """Strict v1 JSON handler. It never serves files or follows URLs."""

    server: LocalWorkbenchHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        # The caller owns structured launch logging; never echo tokens or bodies.
        return

    def _reply(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self._cors_headers()
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(encoded)
        self.close_connection = True

    def _cors_headers(self) -> None:
        origins = self.headers.get_all("Origin", failobj=[])
        if self.server.allowed_ui_origin and origins == [self.server.allowed_ui_origin]:
            self.send_header("Access-Control-Allow-Origin", self.server.allowed_ui_origin)
            self.send_header("Vary", "Origin")

    def _error(self, status: HTTPStatus, code: str, message: str) -> None:
        self._reply(status, {"error": {"code": code, "message": message}})

    def _admit_common(self) -> bool:
        hosts = self.headers.get_all("Host", failobj=[])
        if hosts != [self.server.expected_host_header]:
            self._error(
                HTTPStatus.BAD_REQUEST,
                "host_refused",
                "Host must exactly match the numeric loopback listener",
            )
            return False
        return True

    def _admit_token(self) -> bool:
        values = self.headers.get_all("Authorization", failobj=[])
        if len(values) != 1 or not self.server.authorised(values[0]):
            self._error(
                HTTPStatus.UNAUTHORIZED,
                "authentication_required",
                "A valid in-memory workbench session token is required",
            )
            return False
        return True

    def do_GET(self) -> None:
        if not self._admit_common():
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/healthz" and not parsed.query:
            self._reply(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "posture": AuthorityLevel.LOCAL_FIXTURE.name,
                    "live_target_available": False,
                },
            )
            return
        if parsed.path != "/api/v1/snapshot":
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Unknown local route")
            return
        if not self._admit_token():
            return
        query = parse_qs(parsed.query, keep_blank_values=True)
        if set(query) - {"workspace_id"} or any(len(values) != 1 for values in query.values()):
            self._error(
                HTTPStatus.BAD_REQUEST,
                "invalid_query",
                "Only one optional workspace_id is accepted",
            )
            return
        workspace_id = query.get("workspace_id", [None])[0]
        if workspace_id == "":
            self._error(
                HTTPStatus.BAD_REQUEST,
                "invalid_query",
                "workspace_id cannot be empty",
            )
            return
        try:
            snapshot = self.server.service.snapshot(
                active_workspace_id=workspace_id
            )
        except Exception:
            self._error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "snapshot_failed",
                "The local snapshot failed closed; inspect local logs",
            )
            return
        self._reply(HTTPStatus.OK, snapshot.to_dict())

    def do_POST(self) -> None:
        if not self._admit_common() or not self._admit_token():
            return
        parsed = urlsplit(self.path)
        if parsed.path != "/api/v1/commands" or parsed.query:
            self._error(HTTPStatus.NOT_FOUND, "not_found", "Unknown local route")
            return
        origins = self.headers.get_all("Origin", failobj=[])
        if origins != [self.server.base_url]:
            self._error(
                HTTPStatus.FORBIDDEN,
                "origin_refused",
                "State-changing requests require the exact loopback origin",
            )
            return
        if self.headers.get_all("Transfer-Encoding", failobj=[]):
            self._error(
                HTTPStatus.BAD_REQUEST,
                "transfer_encoding_refused",
                "Chunked or transformed request bodies are not accepted",
            )
            return
        content_types = self.headers.get_all("Content-Type", failobj=[])
        charset = self.headers.get_param("charset")
        if (
            len(content_types) != 1
            or self.headers.get_content_type() != "application/json"
            or (charset is not None and charset.lower() != "utf-8")
        ):
            self._error(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "content_type_refused",
                "Commands require application/json",
            )
            return
        lengths = self.headers.get_all("Content-Length", failobj=[])
        raw_length = lengths[0] if len(lengths) == 1 else None
        if raw_length is None or not raw_length.isdigit():
            self._error(
                HTTPStatus.LENGTH_REQUIRED,
                "content_length_required",
                "A numeric Content-Length is required",
            )
            return
        length = int(raw_length)
        if length < 1 or length > MAX_REQUEST_BYTES:
            self._error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "request_too_large",
                f"Command bodies must contain 1 through {MAX_REQUEST_BYTES} bytes",
            )
            return
        try:
            body = self.rfile.read(length)
        except OSError:
            self._error(
                HTTPStatus.REQUEST_TIMEOUT,
                "body_timeout",
                "The command body was not received within the local timeout",
            )
            return
        if len(body) != length:
            self._error(
                HTTPStatus.BAD_REQUEST,
                "body_incomplete",
                "The command body ended before Content-Length",
            )
            return
        try:
            decoded = json.loads(
                body.decode("utf-8"), object_pairs_hook=_unique_json_object
            )
            if not isinstance(decoded, dict):
                raise WorkbenchContractError("command payload must be an object")
            command = WorkbenchCommand.from_dict(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError, WorkbenchContractError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_command", str(exc))
            return
        result = self.server.service.handle(command)
        status = {
            CommandDisposition.ACCEPTED: HTTPStatus.OK,
            CommandDisposition.CONFLICT: HTTPStatus.CONFLICT,
            CommandDisposition.REFUSED: HTTPStatus.FORBIDDEN,
            CommandDisposition.INVALID: HTTPStatus.UNPROCESSABLE_ENTITY,
        }[result.disposition]
        self._reply(status, result.to_dict())

    def do_OPTIONS(self) -> None:
        if not self._admit_common():
            return
        parsed = urlsplit(self.path)
        origins = self.headers.get_all("Origin", failobj=[])
        methods = self.headers.get_all("Access-Control-Request-Method", failobj=[])
        requested_headers = self.headers.get_all("Access-Control-Request-Headers", failobj=[])
        header_names = {
            item.strip().lower()
            for value in requested_headers
            for item in value.split(",")
            if item.strip()
        }
        if (
            not self.server.allowed_ui_origin
            or origins != [self.server.allowed_ui_origin]
            or parsed.path != "/api/v1/snapshot"
            or parsed.query
            or methods != ["GET"]
            or header_names != {"authorization"}
        ):
            self._error(
                HTTPStatus.METHOD_NOT_ALLOWED,
                "cors_disabled",
                "Cross-origin transport is disabled for this origin or operation",
            )
            return
        self.send_response(HTTPStatus.NO_CONTENT.value)
        self.send_header("Access-Control-Allow-Origin", self.server.allowed_ui_origin)
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "Authorization")
        self.send_header("Access-Control-Max-Age", "300")
        self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WorkbenchContractError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _validate_ui_origin(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise LocalTransportError("UI origin must contain a valid port") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != LOOPBACK_HOST
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or value.rstrip("/") != f"http://{LOOPBACK_HOST}:{port}"
    ):
        raise LocalTransportError(
            "UI origin must be an exact numeric IPv4 loopback origin such as http://127.0.0.1:4173"
        )
    return f"http://{LOOPBACK_HOST}:{port}"


__all__ = [
    "LOOPBACK_HOST",
    "MAX_REQUEST_BYTES",
    "LocalTransportError",
    "LocalWorkbenchHTTPServer",
]
