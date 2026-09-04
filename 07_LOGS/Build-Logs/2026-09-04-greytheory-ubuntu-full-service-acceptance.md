# GreyTheory Ubuntu full-service acceptance — build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, the full Ubuntu worker-service source and bounded WSL
wrapper existed, but no run had emitted the complete required JSON. The latest
recorded attempt had failed inside WSL startup before namespace setup.

The first retry on 2026-09-04 exposed a different, repository-owned defect:
Windows had checked out `acceptance/run-ubuntu-worker-service.sh` with CRLF, so
Bash rejected `set -euo pipefail` as `pipefail\r`. The fix adds an explicit
`*.sh text eol=lf` repository rule and normalizes the entrypoint.

After that fix, the full service harness passed twice. The final wrapper also:

- writes stdout as a durable `acceptance.json` under a unique E: run root;
- keeps stderr in a separate retained log;
- parses the record and independently checks the local-only, identity,
  encryption, receipt, replay, and cleanup invariants; and
- retains its exact 120-second ceiling and only-owned-descendant cleanup.

## Accepted proof

```text
distribution=Ubuntu 24.04.4 LTS
kernel=6.6.114.1-microsoft-standard-WSL2
posture=LOCAL_FIXTURE
passive_http_enabled=false
external_network_contact=false
programme_contacted=false
vps_used=false
root_kek_present=false
interfaces=[lo]
default_route=false
effective_uid=65534
effective_gid=65534
effective_capabilities=0
bounding_capabilities=0
no_new_privileges=true
commands_completed=[resolve, head]
canary_request_exact=true
capture_encrypted=true
capture_round_trip_verified=true
receipt_signature_verified=true
replay_state=completed
child_alive=false
exitcode=0
```

Accepted record:
`E:\Projects\GreyTheory\acceptance\ubuntu-worker-service-20260904-092741-23640\acceptance.json`.

Error log: same directory, `acceptance-error.log`, zero bytes.

Repository verification after adding host/install regression contracts:

```text
python -m pytest -q tests/test_windows_user_install_contract.py tests/test_ubuntu_worker_host_acceptance.py tests/test_packaged_ui.py tests/test_local_workbench_transport.py
21 passed in 1.08s

python -m pytest -q
686 passed in 19.94s
```

## Untouched boundaries

- `8.8.8.8/32` existed only on loopback inside the ephemeral namespace and was
  served by the owned TLS canary; it never left the host.
- No external target, programme endpoint, provider, credential, root KEK, VPS,
  persistent route, live worker launcher, or posture transition was used.
- Existing unrelated WSL clients were observed and left running. The shared
  distro/service was not terminated.

## Remaining gates

This closes only the full-service no-route Ubuntu host harness item. Durable
egress enforcement, OS-bound root KEK and recovery, hardened image conformance,
one verified programme review, sustained-operation evidence, explicit human
posture approval, and `PASSIVE_HTTP` all remain open.
