# Codex activity — GreyTheory Ubuntu full-service acceptance

## Scope

Continue the passive-pilot roadmap by running the already bounded full Ubuntu
worker-service harness without enabling network posture.

## Actions

- Inspected the active Ubuntu WSL state and preserved unrelated WSL clients.
- Reproduced a CRLF shell-entrypoint failure before namespace setup.
- Enforced LF checkout for all repository shell scripts and normalized the
  worker-service entrypoint.
- Re-ran the full service successfully on Ubuntu 24.04.4.
- Added durable JSON/error evidence plus wrapper-side invariant validation.
- Updated capability truth, roadmap, transition documentation, logs, and
  indexes from host-unaccepted to no-route local-fixture accepted.

## Guardrails retained

The accepted harness has only loopback and no default route. It uses an owned
synthetic TLS canary, retains `LOCAL_FIXTURE`, and explicitly records no
external/programme contact, no root KEK, no VPS, and no passive posture.

## Handoff

The next passive-host foundations are durable egress policy, an approved
OS-bound KEK provider/recovery contract, and a reproducible hardened image.
They must remain independent gates and cannot be inferred from this WSL proof.
