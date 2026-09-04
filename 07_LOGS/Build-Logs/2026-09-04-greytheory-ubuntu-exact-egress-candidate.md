# GreyTheory Ubuntu exact-egress candidate — build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, the complete Ubuntu worker passed only in a namespace
with no default route. That proved full-service behavior without networking,
but not the future state in which one authorised destination is allowed and all
other destinations are denied by the operating system.

The current Ubuntu 24.04.4 WSL2 host had no installed nftables userspace and
reported Landlock ABI 3, which cannot restrict network ports. This increment:

- pins five Ubuntu Noble nftables/userspace package files by version and
  SHA-256 and stages them only under the governed E: tool cache;
- reconstructs the executed nftables binary from those packages in every
  owned temporary acceptance root, with no WSL system install;
- creates fresh user, mount, and network namespaces with default-drop input,
  forward, and output chains;
- permits only loopback TCP to the owned synthetic `8.8.8.8:443` canary;
- routes `1.1.1.1` only as a local decoy so a denied address proves the
  firewall, rather than merely proving no route exists;
- accounts for wrong-port, decoy-address, and IPv6 probes in a named deny
  counter; and
- proves UID/GID 65534, zero capabilities, and no-new-privileges cannot add a
  route or flush the policy before the complete encrypted worker path runs.

The Netfilter project's documentation confirms that hooked base chains see the
relevant traffic, `policy drop` discards unmatched packets, and named counters
record matched packets. OCI guidance also requires read-only rootfs and
explicit non-root runtime configuration for the later image gate; this
increment does not claim those image properties.

## Accepted proof

```text
distribution=Ubuntu 24.04.4 LTS
kernel=6.6.114.1-microsoft-standard-WSL2
posture=LOCAL_FIXTURE
external_network_contact=false
programme_contacted=false
passive_http_enabled=false
hardened_worker_image_accepted=false
egress_engine=nftables
default_input=drop
default_forward=drop
default_output=drop
allowed=lo/ipv4/8.8.8.8/tcp/443
denied_probe_packets=3
route_mutation_denied=true
firewall_mutation_denied=true
effective_uid=65534
effective_gid=65534
effective_capabilities=0
bounding_capabilities=0
no_new_privileges=true
capture_encrypted=true
receipt_signature_verified=true
replay_state=completed
child_alive=false
exitcode=0
```

Accepted record:
`E:\Projects\GreyTheory\acceptance\ubuntu-egress-policy-20260904-105113-24804\acceptance.json`.

Error log: same directory, `acceptance-error.log`, zero bytes.

## Visual correction found during QA

The updated Settings copy rendered correctly, but the first 390-pixel capture
showed the fixed footer crossing the Passive Pilot card and hiding its status.
At mobile widths the footer now follows the document instead of overlaying
panels. Desktop behavior remains fixed, and both widths have no horizontal
overflow or console errors.

Visual evidence:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-04-ubuntu-egress-capability-truth`.

## Verification

```text
acceptance/stage-ubuntu-nftables.ps1
5/5 package SHA-256 checks passed

acceptance/run-ubuntu-egress-policy.ps1
accepted; 3 denied packets; full worker receipt/replay passed

python -m pytest -q
698 passed in 17.17s

npm test
23 UI tests passed; 4 Sites tests passed

npm run build
production build passed; 90 modules transformed

PowerShell parser + bash -n
both PowerShell wrappers and both shell entrypoints passed
```

One earlier full-suite attempt, run concurrently with WSL syntax checks, saw a
Windows `WinError 10053` in an existing loopback transport test. The exact test
then passed in isolation and the final non-concurrent 698-test run passed; no
source change was made to hide or weaken that check.

## Sources used for boundary design

- [Linux network namespaces](https://www.kernel.org/pub/linux/docs/man-pages/book/man-pages-6.9.pdf)
- [Linux Landlock network controls](https://cdn.kernel.org/doc/html/latest/userspace-api/landlock.html)
- [Netfilter base chains and default policy](https://wiki.nftables.org/wiki-nftables/index.php/Configuring_chains)
- [Netfilter named counters](https://wiki.nftables.org/wiki-nftables/index.php/Counters)
- [OCI runtime configuration](https://github.com/opencontainers/runtime-spec/blob/main/config.md)

## Untouched boundaries

- The public-looking canary and decoy addresses existed only on loopback inside
  the owned namespace; no packet contacted them externally.
- The root KEK and capture private key did not enter the worker.
- The primary C: checkout and incomplete canonical mini-vault were not changed.
- No WSL package was installed; no target, programme, account, provider,
  credential, VPS, launcher, scheduler, or posture transition was used.

## Remaining gate

This accepts only an OS-enforced policy for the owned namespace lifetime. The
roadmap item for durable egress remains open until a reproducible read-only
Ubuntu worker image makes policy application/admission unavoidable and passes
reboot/VM conformance and negative bypass testing.
