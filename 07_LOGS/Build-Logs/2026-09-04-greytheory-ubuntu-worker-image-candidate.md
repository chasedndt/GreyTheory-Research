# GreyTheory Ubuntu worker-image candidate - build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, GreyTheory had an accepted full-service no-route Ubuntu
fixture and an accepted namespace-lifetime exact-egress candidate, but no image
construction or image-runtime admission path. This increment implements the
next candidate without enabling it:

- exact Ubuntu Base 24.04.4 archive identity and SHA-256;
- pinned Canonical CD-image and 2018 archive signing fingerprints;
- signed `InRelease` -> SHA-256-bound `Packages.xz` -> exact `.deb` provenance
  for 18 locked Python/TLS runtime packages;
- two independent ext4-backed constructions that must yield byte-identical,
  timestamp-normalised, read-only SquashFS images;
- release builds sourced only from committed Git runtime inputs;
- clean-HEAD build manifests that keep runtime/posture flags false;
- private mount/network namespace runtime admission with a read-only root,
  bounded tmpfs mounts, exactly six device nodes, read-only procfs, UID/GID
  65534, no supplementary groups, zero effective/bounding capabilities, and
  no-new-privileges;
- mandatory default-drop nftables admission, three denied egress probes, and
  denied route/firewall mutation; and
- fail-closed composition of the full encrypted worker, signed receipt, replay,
  and terminal child evidence.
- reconciliation of the stale open-questions register with the implemented
  React/Vite, authenticated numeric-loopback workbench boundary.

The runtime wrapper cannot accept a development or dirty-tree image. WSL2 is
only the current construction and owned-fixture environment. The candidate
still records `hardened_worker_image_accepted=false` and
`reboot_vm_conformance_accepted=false`.

## Supply-chain proof completed outside the blocked WSL process path

The downloaded Noble, Noble Updates, and Noble Security `InRelease` files were
verified under fingerprint
`F6ECB3762474EDA9D21B7022871920D1991BC93C`. Their signed Release payloads bind
the exact `main/binary-amd64/Packages.xz` files, and the new verifier matched all
18 locked packages by name, version, architecture, archive path, and SHA-256.
The base-image path also requires the repository-pinned digest to appear in the
CD-image-key-signed checksum set.

## Runtime blocker and safety response

During a discarded prototype, a recursive bind of the live WSL `/dev` was not
recursively unmounted before temporary-root cleanup. That removed ephemeral
device nodes from the running Ubuntu devtmpfs. The unsafe prototype was never
committed and every current staging/build/runtime script statically refuses a
host `/dev` bind. The current Ubuntu instance cannot create a new process:

```text
wsl.exe -d Ubuntu -- /bin/echo ubuntu-ok
exit=1
stdout/stderr empty
```

Windows readback confirms `/dev/null`, `/dev/zero`, `/dev/full`, `/dev/random`,
`/dev/urandom`, `/dev/tty`, and `/dev/ptmx` are absent. Existing user-owned WSL
processes were not terminated. A controlled `wsl --terminate Ubuntu` should
regenerate devtmpfs, but that disruptive action requires explicit operator
approval before the image build/runtime can be attempted.

Two reproducible scratch download roots and one build scratch root remain under
`E:\Projects\GreyTheory`. They are not source and have ample storage headroom,
but must not be recursively removed until WSL restarts and exact mount absence
is reverified.

## Verification

```text
python -m pytest -q tests/test_ubuntu_worker_host_acceptance.py
20 passed

python -m pytest -q
707 passed in 26.73s

python -m py_compile
3 image/provenance modules passed

Git Bash bash -n
stage/build/runtime shell entrypoints passed

PowerShell parser
stage/build/runtime wrappers passed

actual signed archive metadata
3 suites verified; 18/18 locked packages matched
```

There is no image artifact, image build record, or image-runtime acceptance
record yet. UI code was untouched; the prior 23 UI tests, 4 Sites tests,
production build, and rendered QA remain the UI baseline rather than new proof.

## Sources used

- [Ubuntu archive integrity verification](https://documentation.ubuntu.com/security/software-integrity/archive-verification/)
- [Ubuntu image integrity verification](https://documentation.ubuntu.com/security/software-integrity/image-verification/)
- [APT archive authentication](https://manpages.ubuntu.com/manpages/jammy/man8/apt-secure.8.html)

## Untouched boundaries

- No target, programme, account, credential, provider, VPS, or external security
  action was used.
- No WSL package was installed and no Ubuntu distribution was terminated.
- No posture, approval, key-provider, launcher, scheduler, or live-action route
  was enabled.
- The primary C: checkout and canonical vault were not modified.

## Next safe action

After explicit approval, terminate and restart only the Ubuntu WSL distribution,
verify device restoration and scratch-root mount safety, build the clean-commit
image, run image acceptance, and repair any observed host defect. Do not close
the hardened-image milestone until the emitted JSON and later local-VM reboot
conformance both pass.
