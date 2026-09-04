# Codex activity — GreyTheory Ubuntu exact-egress candidate

## Scope

Continue the existing GreyTheory goal by advancing the passive-pilot host
boundary without enabling a live network posture.

## Actions

- Reconciled the clean E: worktree, branch, free space, missing canonical
  mini-vault files, active goal, and installed Ubuntu 24.04.4 primitives.
- Confirmed nftables was not installed and Landlock ABI 3 could not enforce
  network ports.
- Staged exact Ubuntu nftables packages under E: with repository-held hashes,
  then reconstructed the executed tool in an owned temporary root.
- Added default-drop input/forward/output policy with one exact synthetic
  address/port and a named denial counter.
- Added three bounded negative connection probes and active route/firewall
  mutation refusal after capability drop.
- Re-ran the complete resolver, broker recheck, direct TLS, encrypted capture,
  signed receipt, replay completion, and worker cleanup path under that policy.
- Updated capability truth, transition docs, ADRs, roadmap, tests, Mermaid
  architecture, and acceptance instructions.
- Captured and inspected desktop/mobile Settings evidence, then repaired the
  mobile footer overlay exposed by that audit.

## Guardrails retained

The exact-egress proof is namespace-lifetime only and its JSON records
`hardened_worker_image_accepted=false`. `LOCAL_FIXTURE` remains the ceiling; no
external packet, programme, VPS, key-provider activation, launcher, or posture
route was used.

## Verification

698 repository tests, 23 UI tests, 4 Sites tests, production build, PowerShell
parsing, shell syntax, one accepted Ubuntu host record, and desktop/mobile
rendered QA pass.

## Handoff

Build the reproducible read-only Ubuntu worker image next and make exact policy
admission mandatory before the unprivileged worker starts. Keep the DPAPI
approval/recovery, programme review, sustained operation, and human posture
gates independent.
