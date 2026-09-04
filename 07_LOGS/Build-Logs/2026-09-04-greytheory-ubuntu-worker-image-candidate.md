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

## Restart recovery and first build observation

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

Windows readback confirmed `/dev/null`, `/dev/zero`, `/dev/full`, `/dev/random`,
`/dev/urandom`, `/dev/tty`, and `/dev/ptmx` were absent. After explicit operator
approval, only the Ubuntu distribution was terminated. One bounded restart
probe briefly returned `Wsl/Service/CreateInstance/E_FAIL`; stopping only that
owned stuck probe allowed Ubuntu to start normally. All required device nodes
regenerated, and the pre-existing supervised user services returned healthy.

The three abandoned reproducible scratch roots have no mounts or loop-device
backing. Host command policy refused their exact recursive deletion, so they
remain isolated and untouched rather than being removed by a workaround.

The first release-build attempt then completed the Canonical signature checks
but stopped before construction because Linux Git interpreted this linked
worktree's Windows `C:/.../.git/worktrees/...` pointer as a relative path. The
build and runtime entrypoints now resolve that pointer with `wslpath`, bind
explicit `GIT_DIR`/`GIT_WORK_TREE`, and apply Windows checkout line-ending and
file-mode semantics. A focused regression test covers both entrypoints.

The next build reached the ext4-backed root and failed closed because an
alphabetical `.deb` glob presented `python3-minimal` before its configured
`python3.12-minimal` pre-dependency. Package-lock schema 2 now names four
complete install groups. The builder unpacks and configures each group in order;
no `--force-*` flag or dependency bypass is used.

The clean grouped-install retry then reached package configuration and exposed
the ext4 build mount's intentional `nodev` boundary: character nodes created
inside that filesystem could not service `/dev/null`. The builder now keeps the
outer ext4 root `nodev` and mounts an owned 1-MiB `nosuid,noexec` tmpfs only at
the staged `/dev`, creates the six required devices there, and unmounts it after
package configuration. It never binds or copies the host `/dev`; recursive
failure cleanup already owns the nested mount.

That retry completed both image roots and reached the byte-identity gate. The
gate correctly refused the pair, and the new canonical root-manifest diagnostic
isolated the only content difference to `/var/cache/ldconfig/aux-cache`. That
optional future-`ldconfig` acceleration cache embeds filesystem-specific state;
the hardening pass now removes it while retaining the runtime linker cache at
`/etc/ld.so.cache`. The two-build digest check remains mandatory.

A development-mode diagnostic build then produced two byte-identical
29,429,760-byte SquashFS images with SHA-256
`cd754ea9f2cbe3647fd95131f1ee1797dae18b7ffa57e6e208be74b595596834`.
Its manifest correctly records `dirty=true`, `runtime_accepted=false`, and
`hardened_worker_image_accepted=false`; it is not a clean release build or
runtime-acceptance record.

Clean commit `bceaa13a4a547311a9e10a1cf2ec134e88b15e38` then produced a
29,429,760-byte release SquashFS with SHA-256
`15438d9ac0c0ad2a66ffef8c4c616522d719c644f7df1c7261ca8461782c65d1`,
`dirty=false`, and two byte-identical independent builds. Runtime admission
verified its digest and signed supply chain, executed the contained worker, and
then exposed an outer-composer invocation defect: running the composer by file
path omitted the repository root from Python's import path. The harness now
invokes it as the `acceptance.compose_ubuntu_worker_image_acceptance` module;
the failed run emitted no acceptance record.

## Verification

```text
python -m pytest -q tests/test_ubuntu_worker_host_acceptance.py
21 passed

python -m pytest -q
708 passed in 24.91s

python -m py_compile
3 image/provenance modules passed

Git Bash bash -n
stage/build/runtime shell entrypoints passed

PowerShell parser
stage/build/runtime wrappers passed

actual signed archive metadata
3 suites verified; 18/18 locked packages matched
```

A clean reproducible release image now exists, but no image-runtime acceptance
record has passed yet. One dirty-tree development image also exists only as the
bounded reproducibility diagnostic described above. UI code was untouched; the
prior 23 UI tests, 4 Sites tests, production build, and rendered QA remain the
UI baseline rather than new proof.

## Sources used

- [Ubuntu archive integrity verification](https://documentation.ubuntu.com/security/software-integrity/archive-verification/)
- [Ubuntu image integrity verification](https://documentation.ubuntu.com/security/software-integrity/image-verification/)
- [APT archive authentication](https://manpages.ubuntu.com/manpages/jammy/man8/apt-secure.8.html)

## Untouched boundaries

- No target, programme, account, credential, provider, VPS, or external security
  action was used.
- No WSL package was installed; only the explicitly approved Ubuntu
  distribution restart occurred, and other distributions were untouched.
- No posture, approval, key-provider, launcher, scheduler, or live-action route
  was enabled.
- The primary C: checkout and canonical vault were not modified.

## Next safe action

Commit the linked-worktree compatibility fix, build the clean-commit image, run
image acceptance, and repair any observed host defect. Do not close the
hardened-image milestone until the emitted JSON and later local-VM reboot
conformance both pass.
