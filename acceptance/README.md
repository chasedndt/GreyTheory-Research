# Host acceptance

These checks exercise operating-system behavior that syscall-injected unit
tests cannot prove. They do not enable `PASSIVE_HTTP`, launch a worker service,
or contact a target.

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
