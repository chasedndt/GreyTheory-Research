"""Windows-first launcher for the local GreyTheory workbench API."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import argparse

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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime = LocalWorkbenchRuntime.assemble(args.root)
    server = LocalWorkbenchHTTPServer(runtime.service, port=args.port)
    print(f"GreyTheory local API: {server.base_url}")
    print("Operating posture: LOCAL_FIXTURE; live targets unavailable")
    print(f"Private data root: {runtime.root}")
    print(f"Session token: {server.session_token}")
    print("Graphical shell: awaiting operator-selected visual direction")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_parser", "main"]
