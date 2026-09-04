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

### Later clean retry

After commit `ced2b8b`, a retry began with no WSL clients present. WSL failed
before `unshare` started with
`Wsl/Service/CreateInstance/CreateVm/0x800705b4`; its own timeout expired. The
wrapper returned nonzero and left no GreyTheory-owned WSL client. Windows
PowerShell 5.1 was also shown to return an empty `Process.ExitCode` unless the
native process handle is acquired before waiting, so the wrapper now retains
that handle and its static contract asserts the behavior.

```text
PowerShell parse: PASS
tests/test_ubuntu_worker_host_acceptance.py: 5 passed in 5.09s
python -m pytest -q: 665 passed in 187.20s (0:03:07)
```

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

## 2026-08-27 resumed acceptance and host diagnosis

The first resumed run reached the full worker path and exposed a fixture timing
defect: the owned TLS canary stopped accepting after 10 seconds even though the
signed broker action permits a bounded 30-second duration. The canary accept and
join ceilings now outlive that action window. The wrapper also stages the exact
checkout Python sources into its owned native-Linux temporary directory before
dropping privileges, so clean fork-server startup does not spend the action
budget repeatedly importing from the Windows DrvFS mount. The staged source is
removed by the existing owned-runtime cleanup and does not replace the checkout.

```text
python -m pytest -q tests\test_ubuntu_worker_host_acceptance.py tests\test_passive_worker_service.py
18 passed in 27.78s
```

Host acceptance is still **not complete**. After the fixture fix, one run reached
the worker but the resolver process could not start within the signed 30-second
action budget. Later cold starts again failed before `unshare` with
`Wsl/Service/CreateInstance/CreateVm/0x800705b4`, including after a no-client,
no-running-distro `wsl --shutdown` reset. No complete acceptance JSON exists.

The Ubuntu and Docker WSL distributions both live on the external Micron
CT1000X9SSD9 at `E:`. Windows recorded 89 `disk` event ID 11 controller errors
for `\Device\Harddisk2\DR2` during the preceding seven days, including repeated
errors on 2026-08-26 and two after midnight on 2026-08-27. The repeated VM
creation timeouts, 50-90 second WSL command starts, and those controller events
make the external storage path the current host-level risk. No filesystem repair,
distro migration, service disablement, or device reset was attempted.

`PASSIVE_HTTP` remains unavailable. The next safe action is to stabilise or
replace the E: device connection and protect its data, then rerun the full
acceptance and require the complete JSON record before changing capability truth.
