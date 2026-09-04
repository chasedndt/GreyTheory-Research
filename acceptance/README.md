# Host acceptance

These checks exercise operating-system behavior that syscall-injected unit
tests cannot prove. Some launch only the owned synthetic worker service; none
enables `PASSIVE_HTTP` or contacts a target.

## Whole-application keyboard acceptance

From PowerShell at the repository root:

```powershell
& .\acceptance\run-workbench-keyboard.ps1
```

The wrapper builds the current UI, launches only an owned Vite preview on a
numeric-loopback ephemeral port, and stops only that process. A Playwright
browser then proves first-Tab skip navigation, named focus transfer across all
13 panels, desktop/mobile navigation behavior, Cases tab-list arrow keys,
connection-dialog focus trapping and restoration, the local-only Readiness
packet preview, absence of positive `tabindex`, and a clean browser console.
It writes a machine-readable record under `E:\Projects\GreyTheory\acceptance`
and current-run screenshots under the GreyTheory visual-QA home.

Playwright must be available in `workbench_ui/node_modules`, through
`NODE_PATH`, or in the bundled Codex workspace runtime. This is UI acceptance
only: it does not prove screen-reader output, Windows packaging, Ubuntu worker
behavior, live-programme authority, external target access, or deployment.

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
and SHA-256. Four lock-bound install groups satisfy Python's `Pre-Depends`
chain without disabling dependency checks. During configuration, the ext4 root
remains `nodev`; an owned 1-MiB `nosuid,noexec` tmpfs supplies only the six
required device nodes and is unmounted before image creation. The host `/dev`
is never bound. The build installs nothing into the shared WSL distribution. It
constructs two independent ext4-backed roots, copies only the committed worker
inputs for a release build, strips package-management entrypoints and set-id
bits, removes `ldconfig`'s optional filesystem-specific auxiliary cache while
retaining `/etc/ld.so.cache`, normalises timestamps, emits two SquashFS images,
and refuses unless they are byte-identical. A bounded canonical root-manifest
diff identifies content differences when that identity gate refuses a build.

Runtime acceptance requires a clean HEAD-bound image. Inside a private mount
and network namespace it mounts that SquashFS `ro,nodev,nosuid`, creates only
bounded `/tmp`, `/run`, and `/dev` tmpfs mounts, creates an exact six-device
allowlist, mounts read-only procfs, applies the existing default-drop nftables
policy, proves route/firewall mutation denial, then runs the owned canary as
UID/GID 65534 with zero capabilities and no-new-privileges. The image itself
admits the mount, environment, identity, device, immutable-path, egress, and
full receipt/replay evidence before the outer composer can accept it.

**Current proof state:** implementation, static contracts, signed-metadata
package matching, 21 focused tests, the 714-test repository suite, a clean
two-build-identical release image, and WSL2 image-runtime admission pass. The
runtime record proves the read-only image/mount contract, exact device and
environment sets, UID/GID 65534 with no capabilities or new privileges,
default-drop exact egress, three bypass denials, refused route/firewall
mutation, encrypted capture, signed receipt, completed replay, and cleanup. It
also explicitly records `hardened_worker_image_accepted=false`,
`reboot_vm_conformance_accepted=false`, and `LOCAL_FIXTURE`. WSL2 remains the
construction/fixture host; isolated local-VM reboot conformance, accepted broker
transport, key-provider approval/recovery, programme review, sustained
operation, VPS acceptance, and human posture approval remain separate open
gates.

## Authenticated worker-session protocol foundation

The future VM carrier now has an executable network-free protocol contract in
`greytheory_worker_transport`. Its six focused tests prove pinned mutual
Ed25519 identities, a signed two-hello transcript, fresh X25519 and
HKDF-SHA-256 directional keys, ChaCha20-Poly1305 encrypted frames, exact
resolve/head sequencing, expiry, tamper/replay/reflection refusal, the fixed
frame ceiling, and lossless existing worker-record round trips.

This is not a host acceptance harness. The package imports no carrier or
listener and cannot launch a worker or contact a target. Its in-memory replay
guard is only suitable for a test or one-shot process. A future acceptance
harness must provision distinct broker/worker transport identities outside the
image, use a local-only VM carrier, persist replay state across reboot, bind the
peer to the admitted VM, and pass negative cold-boot/reboot tests plus security
review. `PASSIVE_HTTP` remains unavailable.
