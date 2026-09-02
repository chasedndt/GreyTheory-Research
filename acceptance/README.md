# Host acceptance

These checks exercise operating-system behavior that syscall-injected unit
tests cannot prove. They do not enable `PASSIVE_HTTP`, launch a worker service,
or contact a target.

## Windows packaged-workbench acceptance

From PowerShell at the repository root:

```powershell
& .\acceptance\run-windows-packaged-workbench.ps1
```

The harness builds a wheel in a unique E: directory, installs it into an empty
prefix, verifies the generated `greytheory-workbench` console launcher, launches
only that installed application on an ephemeral numeric-loopback port, loads the
bundled UI, checks `LOCAL_FIXTURE` health, authenticates a snapshot, stops only
the process it created, keeps the token only in the child process environment,
never echoes it, and restores the parent environment. Its JSON record contains
the wheel digest and private evidence paths.

This accepts wheel contents and isolated Windows launcher behavior. It does not
yet prove a separate Windows user account, shortcut or signed installer,
persisted-journey restart, upgrade, uninstall, recovery, Ubuntu worker, VPS, or
live-programme posture.

## Ubuntu 24.04 passive primitive acceptance

From PowerShell at the repository root:

```powershell
& .\acceptance\run-ubuntu-worker-host.ps1
```

The wrapper creates an ephemeral unprivileged user/network namespace in WSL2,
brings up only loopback, assigns `8.8.8.8/32` to loopback inside that isolated
namespace, and runs a self-owned TLS canary. The address looks globally
routable so the production `DirectHeadRequest` public-address constraint is
exercised, but the namespace has no default route and the address never leaves
the host.

The Python harness proves:

- Ubuntu 24.04 is the host shape;
- only loopback exists and no default route is present;
- the production transport connects to the exact numeric address without DNS;
- the explicit test CA and hostname are verified, and a mismatch is refused;
- a response header split across two server writes is captured exactly with no
  body, proxy, redirect, or leaked connection;
- a real spawned resolver child that blocks beyond its deadline is terminated
  and reaped; and
- posture remains `LOCAL_FIXTURE`; no worker service is assembled or enabled.

The certificate and private key in `acceptance/fixtures/` are public test-only
fixtures for `greytheory-canary.invalid`. They are not credentials and must
never be reused outside this isolated acceptance check.

This is host acceptance for the primitive layer only. It does not prove the
future Ubuntu image, OS-bound root KEK, broker transport, worker identity,
programme review, canary authorization, sustained operation, or operator
posture approval.

## Ubuntu 24.04 full worker-service acceptance harness

The direction-independent next harness is present at:

```powershell
& .\acceptance\run-ubuntu-worker-service.ps1
```

It uses WSL root only as the namespace bootstrap, then creates a fresh user,
mount, and network namespace; maps the Python process to UID/GID 65534; exposes
only loopback with no default route; overlays `/etc`
ephemerally to map `greytheory-canary.invalid` to the synthetic local
`8.8.8.8`; permits unprivileged port 443 only inside that namespace; then drops
all effective/bounding/inheritable/ambient capabilities and enables
no-new-privileges before Python starts.

The intended acceptance chain is one successful production system resolution,
broker validation of the complete answer, one exact worker TLS `HEAD`, encrypted
capture round trip, signed receipt verification, exact-once replay completion,
and terminal worker cleanup. The worker child receives no broker or private-key
authority.

**Current proof state:** the harness and static contracts are implemented and
the wrapper now owns a separate Linux script, an exact 120-second Windows-side
process ceiling, and leaf-to-parent cleanup of only its WSL clients. Recovered
runs exposed and fixed native quoting, WSL's nested `/etc/hosts` mount, the
resolver's absolute trailing-dot name, masked worker errors, and nested spawn
overhead. The outer worker now starts from a clean fork server and only that
scrubbed authority-free worker forks its cancellable resolver. No run has yet
emitted the required complete JSON record; unrelated Hermes WSL clients again
coincided with an unhealthy distro startup, and the shared distro/service was
not terminated. Do not describe the full worker service as host-accepted until
this command finishes with its JSON evidence.

A later clean retry began with no WSL clients present but failed inside WSL
before `unshare` started: `CreateVm/0x800705b4` reported that its own timeout
expired. The wrapper exited nonzero and left no GreyTheory-owned WSL client.
The wrapper retains the native process handle before waiting so Windows
PowerShell reports the real nonzero exit code rather than an empty value.

Even a successful run would remain an owned no-route local acceptance fixture.
It would not prove durable egress, a hardened image, OS-bound root KEK,
authorised programme operation, VPS suitability, or posture approval, and it
would not enable `PASSIVE_HTTP`.
