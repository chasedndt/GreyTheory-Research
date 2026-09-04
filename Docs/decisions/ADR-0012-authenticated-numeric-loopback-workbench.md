# ADR-0012 - Authenticate the workbench on numeric loopback

**Status:** Accepted - 2026-08-25

**Relates to:** Product workstream and ADR-0010.

## Context

A local browser shell still crosses a security boundary. Any web page open in
the operator's browser can attempt loopback requests; permissive host handling
can enable DNS rebinding; ambient CORS can expose private snapshots; and an
oversized or ambiguous request can bypass assumptions made by a thin UI.

The transport must also remain outside `greytheory_app`. That package is the
transport-neutral application boundary and retains its no-network/process
import proof. A loopback listener is not a target collector and must never
become an informal route to one.

## Decision

Create `greytheory_local` as a separate local-launch package:

- assemble real programme, research, learning, evidence, approval, and audit
  stores under one private root outside every Git worktree;
- bind only to numeric IPv4 loopback `127.0.0.1`; neither `localhost`, `::1`,
  `0.0.0.0`, a LAN address, nor a configurable hostname is accepted in v1;
- require the exact numeric Host header on every request, preventing an
  attacker-controlled hostname from reaching the local API through rebinding;
- generate an in-memory high-entropy bearer token at launch and require it for
  every snapshot or command request;
- require the exact server Origin as well as the token for every POST, emit no
  CORS permission, and refuse preflight rather than widening browser access;
- accept only strict versioned JSON commands with `executable: false`, reject
  duplicate JSON keys and duplicate security headers, reject transfer
  encoding, cap bodies at 64 KiB, and time out incomplete reads;
- return no-store JSON with defensive response headers and expose only a
  minimal unauthenticated health record containing posture and no private data;
- launch through `greytheory-workbench` / `python -m greytheory_local`, printing
  the local API address, private root, posture, and one in-memory token.

The listener may call only the transport-neutral application service. It has
no target HTTP client, worker, broker adapter, model provider, subprocess, file
server, static shell, CORS surface, or posture-changing route.

## Consequences

The selected graphical shell can bind to a tested local contract without
inventing its own storage or command path. Compromise of another website is not
enough to read or mutate the workbench: it lacks the token, exact numeric Host,
and same-origin POST context.

This is not an OS isolation claim. Another process running as the same user may
inspect terminal output or local process memory, and Windows current-user ACL,
installer, shortcut, firewall, clean-user, and packaged-shell acceptance remain
unverified. TLS is intentionally absent because the v1 listener is numeric
loopback only; any remote/VPS or LAN transport requires a new architecture and
must not reuse this decision as authority.
