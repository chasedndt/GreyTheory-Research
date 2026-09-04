# Host acceptance

These checks exercise operating-system behavior that syscall-injected unit
tests cannot prove. Some launch only the owned synthetic worker service; none
enables `PASSIVE_HTTP` or contacts a target.

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

## Windows current-user install lifecycle acceptance

From PowerShell at the repository root:

```powershell
& .\acceptance\run-windows-user-install.ps1
```

The harness builds one release wheel, installs it into a user-owned virtual
environment, creates and inspects a Start Menu-shaped `.lnk`, launches the
resolved shortcut target, persists a bounded learning journey through the real
same-origin command transport, and proves that journey survives application
restart, same-wheel upgrade, and replaceable-runtime recovery. Recovery moves
the old runtime aside inside the unique E: acceptance directory and leaves the
private data root untouched. The installed shortcut opens the numeric-loopback
dashboard in the user's default browser; the harness suppresses that UI side
effect while exercising the same installed target and arguments.

For a normal current-user installation, run:

```powershell
& .\scripts\install-windows-user.ps1
```

This is a user-mode research-preview installer, not an MSI or signed release.
It does not require administrator access, place secrets in the shortcut or
manifest, or enable target networking. The acceptance still does not prove a
different Windows account, uninstall, signing, Ubuntu, VPS, or `PASSIVE_HTTP`.

## Windows DPAPI root-KEK candidate acceptance

From PowerShell at the repository root:

```powershell
& .\acceptance\run-windows-dpapi-root-kek.ps1
```

This provisions a random 32-byte operator root KEK under Windows CurrentUser
DPAPI with UI forbidden, opens the existing capture-recipient key store through
a short-lived zeroing lease, and proves encrypted-capture decryption after
restart and protected-record backup/restore inside the same Windows profile.
It also refuses a tampered DPAPI record, verifies the audit chain, scans its
private acceptance root for plaintext key leakage, and writes a durable JSON
record under E:.

This is a candidate-provider host proof, not posture approval. DPAPI is bound
to the Windows account/profile; a copied encrypted record is not independent
disaster recovery. Cross-profile recovery, operator approval, operational ACL
review, and an approved profile/system backup procedure remain open. The root
KEK never enters the Ubuntu worker. The accepted 2026-09-04 evidence root
inherited `Users` read/execute and `Authenticated Users` modify access, so ACL
hardening is explicitly not accepted even though DPAPI protects the root-key
payload from those identities.

Accepted candidate record:
`E:\Projects\GreyTheory\acceptance\windows-dpapi-root-kek-20260904-095757-20740\acceptance.json`.

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

The accepted chain is one successful production system resolution,
broker validation of the complete answer, one exact worker TLS `HEAD`, encrypted
capture round trip, signed receipt verification, exact-once replay completion,
and terminal worker cleanup. The worker child receives no broker or private-key
authority.

**Current proof state:** accepted on Ubuntu 24.04.4 WSL2 on 2026-09-04. The
remaining host defect was Windows CRLF checkout of the Linux entrypoint; shell
scripts are now repository-enforced LF. The wrapper retains an exact 120-second
Windows-side ceiling, cleans only its own WSL descendants, validates every
local-only invariant, and writes the complete JSON output plus a separate error
log to a unique E: directory. The accepted worker ran as UID/GID 65534 with no
effective or bounding capabilities, no-new-privileges, only loopback, and no
default route. Capture encryption/round trip, signed receipt, completed replay,
and terminal cleanup all passed.

Accepted record:
`E:\Projects\GreyTheory\acceptance\ubuntu-worker-service-20260904-092741-23640\acceptance.json`.

This remains an owned no-route local acceptance fixture. It does not prove
durable egress, a hardened image, an approved OS-bound root-KEK provider and
independent recovery, authorised programme operation, VPS suitability, or
posture approval, and it does not enable `PASSIVE_HTTP`. The separate Windows
DPAPI candidate harness proves only same-profile key recovery.

## Ubuntu 24.04 namespace-lifetime exact-egress candidate

Stage the exact userspace dependency under E: without installing it into the
shared Ubuntu distribution, then run the owned acceptance:

```powershell
& .\acceptance\stage-ubuntu-nftables.ps1
& .\acceptance\run-ubuntu-egress-policy.ps1
```

The stage step downloads pinned Ubuntu Noble `nftables` packages and their
small userspace dependency set to
`E:\Projects\GreyTheory\toolcache\nftables-ubuntu-24.04-amd64`, checks the five
repository-held SHA-256 values, and extracts a convenience copy. Every
acceptance run checks those package hashes again and reconstructs the executed
binary under its own `/tmp/greytheory-egress.*` root, so the WSL distribution
is not modified and a stale extracted binary is not trusted.

Inside a fresh user/network/mount namespace, the fixture policy defaults
input, forward, and output to drop and accepts only TCP to the owned synthetic
`8.8.8.8:443` canary on loopback. The harness routes `1.1.1.1` to loopback only
as a decoy, then proves that the wrong port, decoy address, and IPv6 loopback
all hit the counted deny rule. UID/GID 65534 with zero capabilities and
no-new-privileges cannot add a route or flush the policy. The full worker path
must still complete its exact request, encrypted capture, signed receipt,
replay transition, and cleanup.

Accepted record:
`E:\Projects\GreyTheory\acceptance\ubuntu-egress-policy-20260904-105113-24804\acceptance.json`.

This proves an OS-enforced exact-egress candidate only for the owned namespace
lifetime. `hardened_worker_image_accepted` remains false: read-only rootfs,
image identity/provenance, mandatory policy admission, reboot/VM conformance,
broker transport authentication, key-provider approval/recovery, programme
review, sustained operation, VPS acceptance, and human posture approval remain
open. No external packet or target action occurred.

## Ubuntu 24.04 read-only worker-image candidate

The source-implemented next gate has two separate steps:

```powershell
& .\acceptance\build-ubuntu-worker-image.ps1
& .\acceptance\run-ubuntu-worker-image.ps1
```

Staging downloads the exact Ubuntu Base 24.04.4 archive, verifies Canonical's
signed image checksums under the pinned CD-image key, and verifies every locked
`.deb` through the Ubuntu archive chain: pinned 2018 archive key -> signed
`InRelease` -> hashed `Packages.xz` -> exact package/version/architecture/path
and SHA-256. The build installs nothing into the shared WSL distribution. It
constructs two independent ext4-backed roots, copies only the committed worker
inputs for a release build, strips package-management entrypoints and set-id
bits, normalises timestamps, emits two SquashFS images, and refuses unless they
are byte-identical.

Runtime acceptance requires a clean HEAD-bound image. Inside a private mount
and network namespace it mounts that SquashFS `ro,nodev,nosuid`, creates only
bounded `/tmp`, `/run`, and `/dev` tmpfs mounts, creates an exact six-device
allowlist, mounts read-only procfs, applies the existing default-drop nftables
policy, proves route/firewall mutation denial, then runs the owned canary as
UID/GID 65534 with zero capabilities and no-new-privileges. The image itself
admits the mount, environment, identity, device, immutable-path, egress, and
full receipt/replay evidence before the outer composer can accept it.

**Current proof state:** implementation, static contracts, signed-metadata
package matching, 20 focused tests, and the 707-test repository suite pass. No
image build or image-runtime acceptance record has completed yet, so
`image_runtime_accepted` is not a
current capability and `hardened_worker_image_accepted` remains false. WSL2 is
only the construction/fixture host; isolated local-VM reboot conformance,
broker transport authentication, key-provider approval/recovery, programme
review, sustained operation, VPS acceptance, and human posture approval remain
separate open gates.
