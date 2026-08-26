# GreyTheory Ubuntu service harness hardening

**Date:** 2026-08-26

**Branch:** `codex/2026-08-24-greytheory-workbench-foundation`

**Posture:** `LOCAL_FIXTURE`

## Repository-truth delta

The full worker-service harness briefly became runnable again and exposed real
fixture, wrapper, and startup defects. Those defects are now fixed in source and
covered by tests, but no run emitted the complete acceptance JSON. The full
worker therefore remains host-unaccepted and `PASSIVE_HTTP` remains unavailable.

## Changes

- Replaced a PowerShell-expanded inline Bash command with a checked-in Linux
  script so `$runtime_dir` cannot be lost across native argument parsing.
- Built an owned `/etc/hosts` fixture inside the isolated namespace, including
  the resolver's deliberate trailing-dot absolute hostname.
- Used WSL root only as the namespace bootstrap, then mapped Python to UID/GID
  65534 and dropped all capabilities with no-new-privileges before execution.
- Preserved worker failures instead of masking them with a later canary timeout.
- Started the outer Linux worker through a clean fork server rather than forking
  the broker or re-importing the full acceptance application.
- Forked the cancellable resolver only from the already scrubbed,
  authority-free worker, preserving cancellation within the signed action
  budget without exposing broker state.
- Added a 120-second Windows-side process ceiling and exact owned-WSL-client
  cleanup to the wrapper.

## Host attempts

Recovered attempts failed successively on inline-command expansion, WSL's
nested `/etc/hosts` mount, missing absolute-name fixture coverage, system DNS,
and worker startup duration. Each failure happened before target contact and
made the next defect observable. After the source fixes, shared Ubuntu startup
became unreliable again while unrelated Hermes WSL clients were active. Exact
GreyTheory-owned WSL clients from the timed-out run were stopped; the shared WSL
service, distro, Hermes clients, and unrelated Studio test processes were not
stopped.

No complete JSON record exists, so this is not host acceptance.

## Verification

```text
python -m pytest -q tests\test_passive_worker_service.py tests\test_passive_broker_foundation.py tests\test_passive_capture_encryption.py tests\test_passive_adapter_contract.py tests\test_passive_worker_primitives.py tests\test_ubuntu_worker_host_acceptance.py tests\test_capabilities.py
92 passed in 60.31s (0:01:00)
```

```text
python -m pytest -q
665 passed in 163.32s (0:02:43)
```

## Untouched boundaries

- No live target, programme, external network, VPS, credential, or root KEK was
  used.
- No posture, launcher, scheduler, service, or programme route was enabled.
- No canonical ChaseOS file was changed.
- No shared WSL service/distro restart and no unrelated process termination was
  performed.
- No push, merge, deployment, publication, signing, or spending occurred.

## Verification status

**VERIFIED:** wrapper/static contract, owned-client timeout cleanup in source,
process-context selection, authority separation, focused tests, and full suite.

**UNVERIFIED:** successful full Ubuntu service execution and its required JSON
evidence.

## Next safe action

Run `acceptance/run-ubuntu-worker-service.ps1` when the Ubuntu distribution has
a clean startup window with no unrelated Hermes operation. Require the complete
JSON record and keep `PASSIVE_HTTP` unavailable until that evidence exists.
