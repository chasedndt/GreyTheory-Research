"""Windows-first launcher for the local GreyTheory workbench API."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping

from greytheory_local.packaged_ui import packaged_ui_root
from greytheory_local.runtime import LocalWorkbenchRuntime
from greytheory_local.transport import LocalWorkbenchHTTPServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greytheory-workbench",
        description="Launch GreyTheory's authenticated LOCAL_FIXTURE workbench API",
    )
    parser.add_argument(
        "--root",
        help="private workbench data root outside every Git worktree",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="numeric-loopback port (default: 8765; use 0 for an ephemeral port)",
    )
    parser.add_argument(
        "--ui-origin",
        help="optional exact numeric-loopback UI origin permitted to read snapshots",
    )
    ui_group = parser.add_mutually_exclusive_group()
    ui_group.add_argument(
        "--ui-root",
        help="optional built workbench UI directory served from the exact API origin",
    )
    ui_group.add_argument(
        "--no-ui",
        action="store_true",
        help="launch only the local API even when a packaged UI is available",
    )
    parser.add_argument(
        "--session-token-env",
        action="store_true",
        help="read the token from GREYTHEORY_SESSION_TOKEN and do not echo it",
    )
    return parser


def session_token_from_environment(
    enabled: bool,
    environment: Mapping[str, str] | None = None,
) -> str | None:
    """Read the fixed launch-token variable only when explicitly requested."""

    if not enabled:
        return None
    token = (environment if environment is not None else os.environ).get("GREYTHEORY_SESSION_TOKEN", "")
    if not token:
        raise ValueError("GREYTHEORY_SESSION_TOKEN is required with --session-token-env")
    return token


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        session_token = session_token_from_environment(args.session_token_env)
    except ValueError as exc:
        parser.error(str(exc))
    runtime = LocalWorkbenchRuntime.assemble(args.root)
    ui_root = None if args.no_ui else (args.ui_root or packaged_ui_root())
    server = LocalWorkbenchHTTPServer(
        runtime.service,
        port=args.port,
        allowed_ui_origin=args.ui_origin,
        ui_root=ui_root,
        token=session_token,
    )
    print(f"GreyTheory local API: {server.base_url}", flush=True)
    print("Operating posture: LOCAL_FIXTURE; live targets unavailable", flush=True)
    print(f"Private data root: {runtime.root}", flush=True)
    if args.session_token_env:
        print("Session token: supplied through process environment (not echoed)", flush=True)
    else:
        print(f"Session token: {server.session_token}", flush=True)
    print(
        "Graphical read model: "
        + (f"enabled for {server.allowed_ui_origin}" if server.allowed_ui_origin else "cross-origin access disabled"),
        flush=True,
    )
    print(
        "Same-origin graphical commands: "
        + (f"available from {server.base_url}" if server.ui_root else "disabled (no built UI root configured)"),
        flush=True,
    )
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_parser", "main", "session_token_from_environment"]
