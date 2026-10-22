# After the host-change reboot

For whoever resumes — Claude, Codex, or the operator — after the reboot that
follows `acceptance/apply-host-change-packet.ps1`. Written before the reboot so
nothing depends on remembering.

## 0. Where the host change actually stands (2026-09-11 to 2026-09-14)

**2026-09-14 — measured, and the repair has NOT been done.** The operator
believed the machine had been restarted and repaired. It had not, and the
evidence is unambiguous:

| Check | Value | Meaning |
| --- | --- | --- |
| `LastBootUpTime` | 2026-09-11 22:03 | no boot since the 09-11 reboot |
| UBR | 9278 | KB5124008 (9445) never installed |
| `Get-Service vmms` | absent | Hyper-V role still not present |
| `HypervisorPresent` | True | WSL2/Docker hypervisor, as before |
| CBS `RebootPending` | False | nothing staged and waiting |

WSL, Hermes, the role-buttons bot, OpenClaw and Docker are all healthy. So the
component store is still in the scavenged state described below, the VM is
still blocked, and the *only* remaining route is the in-place repair
(Settings > System > Recovery > "Fix problems using Windows Update" >
Reinstall now). **An agent cannot trigger that**; it reinstalls the OS in
place, which is outside what an agent may do even with standing reboot
authorisation. It must be clicked by the operator.

Nothing on the host has been changed by any failed attempt.

---

The first elevated apply of items 1-3 **changed nothing**: DISM refused item 1
with `0x80073712` (component store corrupt) before the registry key was
reached. `DISM /CheckHealth` then reported "The component store is repairable"
- real CBS corruption, not the pending reboot. Records:
`E:\Projects\GreyTheory\acceptance\host-change\{apply-stdout.log,cbs-diagnosis.log}`.

**21:55, 2026-09-11 — rebooted under standing authorisation, before any
repair completed.** `restore-health.ps1` was accepted at UAC but never got past
its header line: no `dism.exe` process ever appeared, `TiWorker` sat at 362 MB
and 0 CPU, and the log did not change for an hour. A hung `TrustedInstaller`
session also explains the original `0x80073712` and the empty `ScanHealth`.
Docker Desktop crashed a second time in the same window. A reboot was already
pending (CBS `RebootPending`), so it was taken.

**2026-09-12 00:29 — after the reboot, the store is clean and the feature
still refuses.** `DISM /CheckHealth`: "No component store corruption
detected." A full `RestoreHealth` (2 h 16 min, exit 0) changed nothing.
`Enable-WindowsOptionalFeature Microsoft-Hyper-V` still returns "The component
store has been corrupted" (0x80073712). So the fault is in the Hyper-V feature
package itself on this build (image 10.0.26200.9278, an insider line, while the
DISM tool is 10.0.26100), not in the store at large - most likely a missing
or removed payload that Windows Update cannot supply for this build. Record:
`host-change-20260912-002843.json` (failed at item 1; registry key untouched;
host unchanged). Next diagnostic: CBS.log for the package it failed to resolve;
then `/Source:` from matching install media, or a cumulative update.

**2026-09-12 — root cause and the approved fix.** CBS.log shows the enable
staging package versions `.8875`, `.9168` (Hyper-V en-GB language pack) and
`.8972` (HyperV PowerShell WOW64) that are registered in CBS but whose
manifests no longer exist in WinSxS (present: `.1`, `.8457`, `.9278`,
`.9444`). Superseded intermediate LCU packages, scavenged. Not repairable
from Windows Update's store-level view. Fix: install the pending
**KB5124008 (26200.9445)**, which supersedes them. Operator approved
2026-09-12; `install-kb5124008.ps1` does it via the WU API and logs to
`install-kb5124008.log`; reboot follows; then re-run the apply.

**01:10 — the update install failed:** download succeeded, install returned
`ResultCode=4`, `0x80240022` (WU_E_ALL_UPDATES_FAILED), no reboot required.
No reboot was taken. See CBS.log for the underlying servicing error before
retrying; if it is the same `0x80073712`, the stale packages are blocking the
LCU that would supersede them, and the remaining routes are an in-place repair
install ("Fix problems using Windows Update" in Settings > Recovery) or
`DISM /RestoreHealth /Source:` from matching 26100 media. Both are operator
decisions.

**01:15, 2026-09-12 — operator approved an in-place repair.** Settings >
System > Recovery > "Fix problems using Windows Update" > Reinstall now.
Reinstalls build 26200.9445 keeping files, apps and settings; expect one or
two reboots and 30-60 minutes. Hermes, the role-buttons bot and OpenClaw
restart with the WSL distro; Docker Desktop restarts on login.

After the repair, in order: (a) section 1 below; (b) verify
`Get-Service vmms` is still absent and `dism /online /get-featureinfo
/featurename:Microsoft-Hyper-V` reads `Disabled` (not `Disabled with Payload
Removed`); (c) elevated `acceptance/apply-host-change-packet.ps1`; (d) reboot;
(e) sections 2-4.

**Resume here, in order:**

1. Section 1 below (WSL units back).
2. Elevated: `E:\Projects\GreyTheory\acceptance\host-change\restore-health.ps1`
   — check that `restore-health.log` now actually fills and ends with
   `sfc exit code`. If DISM still reports repairable/corrupt after it, stop and
   report; do not loop.
3. Elevated: `acceptance/apply-host-change-packet.ps1` (worktree). Expect
   `RestartNeeded=True` for Hyper-V; then `-Reboot`, or `shutdown /r`.
4. Second reboot -> Section 1 again -> Section 2 -> Sections 3 and 4.

The Claude session that wrote this ends with the reboot; its handover is
`Docs/handovers/2026-09-09-host-change-and-architecture-handover.md` plus the
2026-09-11 entries in `CHANGELOG.md`.

## 1. Bring the WSL services back

Hermes, the Discord role-buttons bot, and the OpenClaw gateway are **systemd
user services** inside WSL Ubuntu. They start on their own when the distro
starts; the distro starts on first use. So:

```powershell
wsl.exe -d Ubuntu -- systemctl --user list-units --type=service --no-pager
```

Expected `active running`:

- `hermes-gateway.service`
- `chaseos-community-role-buttons.service`
- `chaseos-openclaw-gateway.service`

If one is not, `systemctl --user restart <unit>` inside the distro. Never
`Stop-Process` broadly on the Windows side.

## 2. Confirm the role landed

```powershell
Get-Service vmms
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V | Select State
Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Virtualization\GuestCommunicationServices\00004754-facb-11e6-bd58-64006a7986d3'
```

All three must be true/`Enabled`/`Running`. The application record is under
`E:\Projects\GreyTheory\acceptance\host-change\host-change-*.json`.

## 3. Items 4 and 5 — the VM

Needs a `.vhdx` of the **normalised** build-3 image
(`assembly-20260909-140009`, normalised digest
`44fa454be4222724cfbdbc81cf48e44e6abcb4b81fc87dc346f9b372e492e9cd`). Convert
with `acceptance/convert-image-to-vhdx.ps1` (qemu-img in a throwaway container;
needs Docker Desktop running, not the Hyper-V role), then normalise the
container per ADR-0028 (`acceptance/vhdx_identity.py`), then:

```powershell
powershell -ExecutionPolicy Bypass -File acceptance/create-research-worker-vm.ps1 -Vhdx <normalised.vhdx>
```

It records the VM ID. That ID is the one the carrier admits; do not wildcard it.

## 4. The eight negative tests

`Docs/host-change-review-packet.md` section 6. Results feed
`acceptance/vhdx_boot_spec.validate_boot()` via a `BootReport` that names the
VM UUID, the observer, the booted payload digest, and sets
`interfaces_enumerated`. Only then does `accept_artifact()` have both halves.

Creating the VM is not booting it. Booting it is not accepting it. Keep the
three states apart in every record.
