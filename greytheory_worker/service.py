"""Owned-process assembly for the bounded Ubuntu passive worker.

The broker remains in the trusted operator process. The spawned worker receives
only one hostname-resolution command followed by one exact direct-TLS request;
it never receives signing keys, the replay ledger, kill-switch authority, the
research store, a capture private key, or a second action.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import math
import multiprocessing
import os
import platform
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from greytheory_worker.primitives import (
    CancellableSystemResolver,
    DirectTlsHeadTransport,
)
from greytheory_worker_contract import (
    AdapterContractError,
    AdapterTimedOut,
    DirectHeadRequest,
    HeadTransportResult,
    ResolutionFailed,
    ResolutionResult,
    TransportCaptureLimitExceeded,
    TransportFailed,
)


WORKER_IPC_SCHEMA_VERSION = "greytheory.worker-ipc.v1"
WORKER_ID = "greytheory-ubuntu-passive"
WORKER_VERSION = "0.1.0"
MAX_FRAME_BYTES = 196_608
MAX_ERROR_CHARS = 512
DEFAULT_SHUTDOWN_GRACE_SECONDS = 0.5
SAFE_WORKER_ID = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
WORKER_SAFE_ENVIRONMENT = {
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
}


class WorkerServiceError(RuntimeError):
    """Raised when the local worker process boundary is unsafe or ambiguous."""


class WorkerProtocolError(WorkerServiceError):
    """Raised for an invalid or out-of-order worker IPC message."""


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise WorkerProtocolError(f"{label} must be a finite monotonic value")
    return number


def _exact_keys(
    value: Mapping[str, Any], expected: set[str], label: str
) -> None:
    if set(value) != expected:
        raise WorkerProtocolError(
            f"{label} fields are invalid: missing={sorted(expected - set(value))!r}, "
            f"unexpected={sorted(set(value) - expected)!r}"
        )


def _canonical_frame(value: Mapping[str, Any]) -> bytes:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    if len(encoded) > MAX_FRAME_BYTES:
        raise WorkerProtocolError("worker IPC frame exceeds the fixed ceiling")
    return encoded


def _decode_frame(raw: bytes) -> Mapping[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_FRAME_BYTES:
        raise WorkerProtocolError("worker IPC frame size is invalid")
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerProtocolError("worker IPC frame is not canonical JSON") from exc
    if not isinstance(value, dict):
        raise WorkerProtocolError("worker IPC frame must be an object")
    return value


@dataclass(frozen=True)
class WorkerIdentity:
    worker_id: str
    worker_version: str
    platform: str
    process_id: int
    effective_uid: int | None
    effective_gid: int | None
    effective_capabilities: int | None
    bounding_capabilities: int | None
    no_new_privileges: bool | None
    supplementary_gids: tuple[int, ...]
    environment_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if not SAFE_WORKER_ID.fullmatch(self.worker_id):
            raise WorkerProtocolError("worker identity is invalid")
        if not str(self.worker_version or "").strip():
            raise WorkerProtocolError("worker version is required")
        if self.process_id <= 0:
            raise WorkerProtocolError("worker process id is invalid")

    @property
    def is_unprivileged_linux(self) -> bool:
        return (
            self.platform == "linux"
            and self.effective_uid not in (None, 0)
            and self.effective_gid not in (None, 0)
            and self.effective_capabilities == 0
            and self.bounding_capabilities == 0
            and self.no_new_privileges is True
            and all(group == self.effective_gid for group in self.supplementary_gids)
            and self.environment_keys == tuple(sorted(WORKER_SAFE_ENVIRONMENT))
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "worker_version": self.worker_version,
            "platform": self.platform,
            "process_id": self.process_id,
            "effective_uid": self.effective_uid,
            "effective_gid": self.effective_gid,
            "effective_capabilities": self.effective_capabilities,
            "bounding_capabilities": self.bounding_capabilities,
            "no_new_privileges": self.no_new_privileges,
            "supplementary_gids": list(self.supplementary_gids),
            "environment_keys": list(self.environment_keys),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkerIdentity:
        _exact_keys(
            data,
            {
                "worker_id",
                "worker_version",
                "platform",
                "process_id",
                "effective_uid",
                "effective_gid",
                "effective_capabilities",
                "bounding_capabilities",
                "no_new_privileges",
                "supplementary_gids",
                "environment_keys",
            },
            "worker identity",
        )

        def optional_int(name: str) -> int | None:
            value = data[name]
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise WorkerProtocolError(f"worker {name} is invalid")
            return value

        no_new_privileges = data["no_new_privileges"]
        if no_new_privileges not in (True, False, None):
            raise WorkerProtocolError("worker no-new-privileges state is invalid")
        for name in ("worker_id", "worker_version", "platform"):
            if not isinstance(data[name], str):
                raise WorkerProtocolError(f"worker {name} must be text")
        supplementary = data["supplementary_gids"]
        environment_keys = data["environment_keys"]
        if not isinstance(supplementary, list) or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            for value in supplementary
        ):
            raise WorkerProtocolError("worker supplementary groups are invalid")
        if not isinstance(environment_keys, list) or any(
            not isinstance(value, str) for value in environment_keys
        ):
            raise WorkerProtocolError("worker environment keys are invalid")
        return cls(
            worker_id=data["worker_id"],
            worker_version=data["worker_version"],
            platform=data["platform"],
            process_id=optional_int("process_id") or 0,
            effective_uid=optional_int("effective_uid"),
            effective_gid=optional_int("effective_gid"),
            effective_capabilities=optional_int("effective_capabilities"),
            bounding_capabilities=optional_int("bounding_capabilities"),
            no_new_privileges=no_new_privileges,
            supplementary_gids=tuple(supplementary),
            environment_keys=tuple(environment_keys),
        )


def _linux_status() -> tuple[int | None, int | None, bool | None]:
    path = Path("/proc/self/status")
    if not path.is_file():
        return None, None, None
    values: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key] = value.strip()
    try:
        effective = int(values["CapEff"], 16)
        bounding = int(values["CapBnd"], 16)
        no_new_privileges = values["NoNewPrivs"] == "1"
    except (KeyError, ValueError):
        return None, None, None
    return effective, bounding, no_new_privileges


def current_worker_identity() -> WorkerIdentity:
    effective, bounding, no_new_privileges = _linux_status()
    return WorkerIdentity(
        worker_id=WORKER_ID,
        worker_version=WORKER_VERSION,
        platform=platform.system().lower(),
        process_id=os.getpid(),
        effective_uid=os.geteuid() if hasattr(os, "geteuid") else None,
        effective_gid=os.getegid() if hasattr(os, "getegid") else None,
        effective_capabilities=effective,
        bounding_capabilities=bounding,
        no_new_privileges=no_new_privileges,
        supplementary_gids=(
            tuple(sorted(os.getgroups())) if hasattr(os, "getgroups") else ()
        ),
        environment_keys=tuple(sorted(os.environ)),
    )


def _sanitize_worker_environment() -> None:
    os.environ.clear()
    os.environ.update(WORKER_SAFE_ENVIRONMENT)


def _default_worker_process_context() -> Any:
    if platform.system().lower() == "linux":
        multiprocessing.set_forkserver_preload(["greytheory_worker.service"])
        return multiprocessing.get_context("forkserver")
    return multiprocessing.get_context("spawn")


class WorkerProtocolService:
    """One resolve command followed by one bound direct-HEAD command."""

    def __init__(
        self,
        *,
        resolver: Any,
        transport: Any,
        identity: WorkerIdentity | None = None,
    ) -> None:
        self.resolver = resolver
        self.transport = transport
        self.identity = identity or current_worker_identity()
        self.sequence = 0
        self.resolution: ResolutionResult | None = None
        self.closed = False

    def handle(self, frame: Mapping[str, Any]) -> dict[str, Any]:
        if self.closed:
            raise WorkerProtocolError("worker protocol is already closed")
        _exact_keys(
            frame,
            {"schema_version", "sequence", "command", "payload"},
            "worker command",
        )
        if frame["schema_version"] != WORKER_IPC_SCHEMA_VERSION:
            raise WorkerProtocolError("worker IPC schema is unsupported")
        sequence = frame["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            raise WorkerProtocolError("worker command sequence must be an integer")
        if sequence != self.sequence + 1:
            raise WorkerProtocolError("worker command sequence is not contiguous")
        command = frame["command"]
        if not isinstance(command, str):
            raise WorkerProtocolError("worker command must be text")
        payload = frame["payload"]
        if not isinstance(payload, dict):
            raise WorkerProtocolError("worker command payload must be an object")
        self.sequence = sequence
        try:
            if command == "resolve" and self.resolution is None and sequence == 1:
                _exact_keys(
                    payload,
                    {"canonical_host", "deadline_monotonic"},
                    "resolve payload",
                )
                canonical_host = payload["canonical_host"]
                if not isinstance(canonical_host, str):
                    raise WorkerProtocolError("resolve host must be text")
                result = self.resolver.resolve(
                    canonical_host,
                    deadline_monotonic=_finite(
                        payload["deadline_monotonic"], "resolve deadline"
                    ),
                )
                if type(result) is not ResolutionResult:
                    raise WorkerProtocolError("resolver returned an untyped result")
                self.resolution = result
                return self._success(sequence, "resolution", result.to_dict())
            if command == "head" and self.resolution is not None and sequence == 2:
                _exact_keys(payload, {"request"}, "head payload")
                request_data = payload["request"]
                if not isinstance(request_data, dict):
                    raise WorkerProtocolError("head request must be an object")
                request = DirectHeadRequest.from_dict(request_data)
                if request.canonical_host != self.resolution.canonical_host:
                    raise WorkerProtocolError(
                        "direct request host does not match the worker resolution"
                    )
                if request.exact_address not in self.resolution.addresses:
                    raise WorkerProtocolError(
                        "direct request address was not returned by the worker resolution"
                    )
                result = self.transport.head(request)
                if type(result) is not HeadTransportResult:
                    raise WorkerProtocolError("transport returned an untyped result")
                self.closed = True
                return self._success(sequence, "transport", result.to_dict())
            raise WorkerProtocolError(
                "worker permits exactly one resolve followed by one head command"
            )
        except AdapterTimedOut as exc:
            self.closed = True
            return self._error(sequence, "timeout", str(exc))
        except TransportCaptureLimitExceeded as exc:
            self.closed = True
            return self._error(sequence, "capture_limit", str(exc))
        except ResolutionFailed as exc:
            self.closed = True
            return self._error(sequence, "resolution_failed", str(exc))
        except TransportFailed as exc:
            self.closed = True
            return self._error(sequence, "transport_failed", str(exc))
        except (AdapterContractError, WorkerServiceError, ValueError) as exc:
            self.closed = True
            return self._error(sequence, "protocol_error", str(exc))
        except Exception as exc:
            self.closed = True
            return self._error(
                sequence,
                "worker_failed",
                f"{type(exc).__name__}: {exc}",
            )

    def _success(
        self, sequence: int, result_type: str, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        return {
            "schema_version": WORKER_IPC_SCHEMA_VERSION,
            "sequence": sequence,
            "status": "ok",
            "result_type": result_type,
            "payload": dict(payload),
            "worker": self.identity.to_dict(),
        }

    def _error(self, sequence: int, code: str, detail: str) -> dict[str, Any]:
        return {
            "schema_version": WORKER_IPC_SCHEMA_VERSION,
            "sequence": sequence,
            "status": "error",
            "error_code": code,
            "detail": str(detail or "worker failed closed")[:MAX_ERROR_CHARS],
            "worker": self.identity.to_dict(),
        }


def _worker_child(channel: Any, ca_file: str) -> None:
    """Serve the fixed two-command protocol in one owned spawned process."""

    _sanitize_worker_environment()
    if platform.system().lower() != "linux":
        raise WorkerServiceError("the passive worker child requires Linux")
    resolver_context = multiprocessing.get_context("fork")
    service = WorkerProtocolService(
        resolver=CancellableSystemResolver(process_context=resolver_context),
        transport=DirectTlsHeadTransport(ca_file=ca_file),
    )
    try:
        while not service.closed:
            try:
                raw = channel.recv_bytes(MAX_FRAME_BYTES)
                frame = _decode_frame(raw)
                response = service.handle(frame)
            except (EOFError, OSError):
                break
            except Exception as exc:
                service.closed = True
                response = service._error(
                    max(service.sequence, 0),
                    "protocol_error",
                    f"{type(exc).__name__}: {exc}",
                )
            channel.send_bytes(_canonical_frame(response))
    finally:
        try:
            channel.close()
        except Exception:
            pass


@dataclass(frozen=True)
class WorkerProcessEvidence:
    identity: WorkerIdentity
    process_start_method: str
    commands_completed: tuple[str, ...]
    exitcode: int
    child_alive: bool = False

    def __post_init__(self) -> None:
        if self.child_alive:
            raise WorkerServiceError("worker process evidence cannot claim a live child")
        if self.exitcode != 0:
            raise WorkerServiceError("worker process did not exit successfully")
        if self.commands_completed != ("resolve", "head"):
            raise WorkerServiceError("worker did not complete the exact command sequence")

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "process_start_method": self.process_start_method,
            "commands_completed": list(self.commands_completed),
            "exitcode": self.exitcode,
            "child_alive": False,
        }


class SpawnedWorkerClient:
    """Broker-side resolver/transport proxy for one owned Ubuntu process."""

    def __init__(
        self,
        *,
        ca_file: str | Path,
        process_context: Any | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        shutdown_grace_seconds: float = DEFAULT_SHUTDOWN_GRACE_SECONDS,
        require_unprivileged_linux: bool = True,
    ) -> None:
        self.ca_file = Path(ca_file).expanduser().resolve()
        if not self.ca_file.is_file():
            raise WorkerServiceError("worker CA bundle must be an existing file")
        self.process_context = (
            process_context or _default_worker_process_context()
        )
        self.monotonic = monotonic
        self.shutdown_grace_seconds = float(shutdown_grace_seconds)
        if (
            not math.isfinite(self.shutdown_grace_seconds)
            or not 0 < self.shutdown_grace_seconds <= 2
        ):
            raise WorkerServiceError(
                "worker shutdown grace must be positive and at most two seconds"
            )
        self.require_unprivileged_linux = require_unprivileged_linux
        self._channel: Any | None = None
        self._process: Any | None = None
        self._identity: WorkerIdentity | None = None
        self._commands: list[str] = []
        self._resolved: ResolutionResult | None = None
        self._exitcode: int | None = None

    @property
    def started(self) -> bool:
        return self._process is not None

    def _start(self) -> None:
        if self.started:
            return
        parent, child = self.process_context.Pipe(duplex=True)
        process = self.process_context.Process(
            target=_worker_child,
            args=(child, str(self.ca_file)),
            name="greytheory-ubuntu-passive-worker",
            daemon=False,
        )
        try:
            process.start()
            child.close()
        except Exception:
            parent.close()
            child.close()
            raise
        self._channel = parent
        self._process = process

    def _remaining(self, deadline: float, label: str) -> float:
        remaining = _finite(deadline, "worker deadline") - _finite(
            self.monotonic(), label
        )
        if remaining <= 0:
            self.close()
            raise AdapterTimedOut(f"{label} exceeded the adapter deadline")
        return remaining

    def _exchange(
        self, command: str, payload: Mapping[str, Any], *, deadline: float
    ) -> Mapping[str, Any]:
        self._start()
        assert self._channel is not None
        sequence = len(self._commands) + 1
        frame = {
            "schema_version": WORKER_IPC_SCHEMA_VERSION,
            "sequence": sequence,
            "command": command,
            "payload": dict(payload),
        }
        try:
            self._channel.send_bytes(_canonical_frame(frame))
            if not self._channel.poll(
                self._remaining(deadline, f"worker {command} wait")
            ):
                self.close()
                raise AdapterTimedOut(
                    f"worker {command} exceeded the adapter deadline"
                )
            response = _decode_frame(self._channel.recv_bytes(MAX_FRAME_BYTES))
        except AdapterTimedOut:
            raise
        except Exception as exc:
            self.close()
            raise WorkerServiceError(
                f"worker {command} channel failed closed: {exc}"
            ) from exc
        try:
            _exact_keys(
                response,
                (
                    {
                        "schema_version",
                        "sequence",
                        "status",
                        "result_type",
                        "payload",
                        "worker",
                    }
                    if response.get("status") == "ok"
                    else {
                        "schema_version",
                        "sequence",
                        "status",
                        "error_code",
                        "detail",
                        "worker",
                    }
                ),
                "worker response",
            )
            if (
                response["schema_version"] != WORKER_IPC_SCHEMA_VERSION
                or isinstance(response["sequence"], bool)
                or not isinstance(response["sequence"], int)
                or response["sequence"] != sequence
            ):
                raise WorkerProtocolError(
                    "worker response does not match the request"
                )
            worker_data = response["worker"]
            if not isinstance(worker_data, dict):
                raise WorkerProtocolError("worker response identity is not an object")
            identity = WorkerIdentity.from_dict(worker_data)
            if self._identity is not None and identity != self._identity:
                raise WorkerProtocolError(
                    "worker identity changed during one attempt"
                )
            if (
                self.require_unprivileged_linux
                and not identity.is_unprivileged_linux
            ):
                raise WorkerProtocolError(
                    "worker is not an unprivileged Linux process with no capabilities"
                )
            self._identity = identity
        except Exception:
            self.close()
            raise
        if response["status"] == "error":
            self.close()
            code = response["error_code"]
            detail = response["detail"]
            if not isinstance(code, str) or not isinstance(detail, str):
                raise WorkerProtocolError("worker error response must contain text")
            if code == "timeout":
                raise AdapterTimedOut(detail)
            if code == "capture_limit":
                raise TransportCaptureLimitExceeded(detail)
            if code == "resolution_failed":
                raise ResolutionFailed(detail)
            if code == "transport_failed":
                raise TransportFailed(detail)
            raise WorkerProtocolError(f"worker failed closed: {code}: {detail}")
        expected_result_type = {
            "resolve": "resolution",
            "head": "transport",
        }[command]
        if (
            response["status"] != "ok"
            or response["result_type"] != expected_result_type
        ):
            self.close()
            raise WorkerProtocolError("worker returned an invalid success response")
        result = response["payload"]
        if not isinstance(result, dict):
            self.close()
            raise WorkerProtocolError("worker result payload is not an object")
        self._commands.append(command)
        return result

    def resolve(
        self, canonical_host: str, *, deadline_monotonic: float
    ) -> ResolutionResult:
        if self._commands:
            raise ResolutionFailed("worker permits exactly one resolver command")
        result = ResolutionResult.from_dict(
            self._exchange(
                "resolve",
                {
                    "canonical_host": canonical_host,
                    "deadline_monotonic": deadline_monotonic,
                },
                deadline=deadline_monotonic,
            )
        )
        self._resolved = result
        return result

    def head(self, request: DirectHeadRequest) -> HeadTransportResult:
        if self._resolved is None or self._commands != ["resolve"]:
            raise TransportFailed("worker requires one completed resolution first")
        result = HeadTransportResult.from_dict(
            self._exchange(
                "head",
                {"request": request.to_dict()},
                deadline=request.deadline_monotonic,
            )
        )
        self._join_after_success(request.deadline_monotonic)
        return result

    def _join_after_success(self, deadline: float) -> None:
        assert self._process is not None
        self._process.join(
            min(
                self.shutdown_grace_seconds,
                max(self._remaining(deadline, "worker process exit"), 0),
            )
        )
        if self._process.is_alive():
            self.close()
            raise TransportFailed("worker remained alive after its one permitted action")
        self._exitcode = self._process.exitcode
        if self._exitcode != 0:
            raise TransportFailed(
                f"worker exited with unexpected status {self._exitcode!r}"
            )

    def close(self) -> None:
        if self._channel is not None:
            try:
                self._channel.close()
            except Exception:
                pass
        process = self._process
        if process is not None and process.is_alive():
            process.terminate()
            process.join(self.shutdown_grace_seconds)
        if process is not None and process.is_alive():
            process.kill()
            process.join(self.shutdown_grace_seconds)
        if process is not None and not process.is_alive():
            self._exitcode = process.exitcode

    @property
    def evidence(self) -> WorkerProcessEvidence:
        if self._identity is None or self._process is None or self._exitcode is None:
            raise WorkerServiceError("worker process evidence is incomplete")
        return WorkerProcessEvidence(
            identity=self._identity,
            process_start_method=str(self.process_context.get_start_method()),
            commands_completed=tuple(self._commands),
            exitcode=self._exitcode,
            child_alive=self._process.is_alive(),
        )

    def __enter__(self) -> SpawnedWorkerClient:
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        del exc_type, exc, traceback
        self.close()


__all__ = [
    "MAX_FRAME_BYTES",
    "SpawnedWorkerClient",
    "WORKER_ID",
    "WORKER_IPC_SCHEMA_VERSION",
    "WORKER_SAFE_ENVIRONMENT",
    "WORKER_VERSION",
    "WorkerIdentity",
    "WorkerProcessEvidence",
    "WorkerProtocolError",
    "WorkerProtocolService",
    "WorkerServiceError",
    "current_worker_identity",
]
