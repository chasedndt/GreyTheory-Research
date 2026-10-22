# GreyTheory handover — host change, current state, and a diagram brief

Prepared 2026-09-09. Author: Claude. Owner: ChaseInTech.
Audience: Codex / GPT-6 Astra, and the operator.

Supersedes nothing. Read alongside
[2026-09-08](2026-09-08-claude-to-codex-return-handover.md) for the detail of
what was built; this document covers **what is about to change on the machine**,
**why that is not merely a reboot**, and **what Codex is asked to draw**.

---

## Part 1 — Where the system stands

### 1.1 What GreyTheory is

A standalone, local-first, human-governed security research operating system.
Product line: *From scope to proof*. Everything runs on one Windows machine, in
one worktree, with no server and no account. Two postures govern it, and they
are deliberately separate axes:

| Axis | Meaning | Current value |
| --- | --- | --- |
| **Execution posture** | What the system may touch of a programme's assets | `LOCAL_FIXTURE` — synthetic only |
| **Collector posture** | What the system may read about programmes | `OPERATOR_ACCOUNT` — public directories and the operator's own account |

They did not move together and no record is allowed to imply they did.

### 1.2 Implemented and green

**Test position: 1,090 Python pass / 4 skip (Windows symlinks), 135 UI, 4 Sites,
production build passes.**

**Learning product**
- 24 lessons, one file each under `workbench_ui/src/lessons/` plus a registry.
  Each carries concept, traditional lens, AI-native lens, worked example, what
  proof looks like, and three checks (`recognise`, `decide`, `prove`) with
  progressive hints.
- Programme-driven topic selection — `greytheory/learning/programme_curriculum.py`
  maps compiled programme scope to catalogue cards through six reviewable rules.
  Ranking is surface-diverse so one broad rule cannot crowd out a whole surface.
- Participation, ranks, share card, rotation limit, coach guidance. Every rank
  travels with the criterion that earned it; the card refuses handles or topics
  carrying certification claims, findings, CVEs, URLs, hostnames, or IPs.

**Platform integration (ADR-0029, all three tiers approved 2026-09-08)**
- Tier 1 public directory reads: HTTPS only, GET only, redirects refused, no
  credential. One live read performed — `hackerone.com/security`, HTTP 200,
  digest `0ba341758c1d1973a0535cccedf3bf22da2d7670303a708b0a67242f88a03d2c`.
- Tier 2 operator account reads: session or DPAPI-encrypted credentials, token
  in an `Authorization` header and nowhere else, dedicated `/api/v1/credentials`
  route that shares every admission check but never enters the command bus.
- Tier 3 submission: payload-digest-bound approval, kill switch engaged by
  default, every claim must be `checked` and receipt-backed. **Never fired.**

**Artifact pipeline (Milestone 9, offline half)**
- `acceptance/assemble-greytheory-vhdx.sh` — has now run twice successfully.
- Two independent builds produce different raw images that normalise to one
  digest: `44fa454be4222724cfbdbc81cf48e44e6abcb4b81fc87dc346f9b372e492e9cd`,
  via `acceptance/normalise-assembly.py`.
- Payload SquashFS pinned at
  `15438d9ac0c0ad2a66ffef8c4c616522d719c644f7df1c7261ca8461782c65d1`.

### 1.3 The blocker that is not the host change

A 107-agent adversarial audit on 2026-09-09 confirmed **12 defects** (34
candidates, 22 refuted by three-lens verification). Seven are HIGH, and **six of
those sit on the acceptance gate itself** — `acceptance/vhdx_boot_spec.py`, the
code that decides whether a built artifact may be called accepted.

The four that matter most:

1. **`network_interfaces` defaults to `()`** — a *passing* value. "Nobody
   enumerated the interfaces" is indistinguishable from "there are none". Every
   other field on `BootReport` fails closed; this one fails open.
2. **`accept_artifact()` trusts any dict** carrying a truthy
   `satisfies_runtime_specification`. No schema check, no requirement that a VM
   or an observer be named. `accept_artifact({...: True}, {...: True})` returns
   `artifact_accepted: True`.
3. **Extra mounts are never rejected.** A guest presenting a persistent ext4
   filesystem alongside the six required mounts passes — the exact condition the
   disposable-worker design exists to rule out.
4. **Nothing binds the boot record to the assembled artifact.** A boot report
   from image A can accept an assembly record for image B.

Plus, on the builder: `kernel_command_line` is still reported from the builder's
own shell variable rather than read back from the `grub.cfg` it wrote — the
circular-proof defect fixed once already, surviving in one field.

**Consequence for sequencing.** The host change is approved and will be applied.
But rebooting to create a VM whose eight negative tests feed a validator that can
pass for the wrong reasons buys nothing. The gate is fixed first — offline, no
host change, no service interruption — and then the reboot is worth taking.

---

## Part 2 — The host change package

This is what the operator approved on 2026-09-09.

### 2.1 The five changes

| # | Change | Reversible by | Reboot |
| --- | --- | --- | --- |
| 1 | Enable Windows **Hyper-V** optional feature | Disabling the feature | **Yes** |
| 2 | Enable the **Hyper-V PowerShell module** | Disabling it | No |
| 3 | Write one **VSOCK service GUID** registry key | Deleting that key | No |
| 4 | Create VM `GreyTheory-Research-Worker` | Removing the VM | No |
| 5 | Attach the built boot VHDX to it | Detaching | No |

### 2.2 Exactly what gets created

```text
VM name               GreyTheory-Research-Worker
Generation            2
Guest                 Ubuntu 24.04 LTS amd64
Processors            2
Memory                2 GiB fixed (dynamic memory disabled)
Automatic checkpoints disabled
Secure Boot           enabled, MicrosoftUEFICertificateAuthority template
Network adapters      0
Runtime root          E:\Projects\GreyTheory\runtime\hyperv\GreyTheory-Research-Worker
Service GUID          00004754-facb-11e6-bd58-64006a7986d3
VSOCK port            18260
Frame ceiling         196608 bytes
VM ID                 captured after creation; never wildcarded, never guessed
```

The registry key, in full:

```text
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Virtualization\GuestCommunicationServices\
  00004754-facb-11e6-bd58-64006a7986d3
    ElementName = "GreyTheory research worker VSOCK"
```

### 2.3 Why this is not "just a reboot"

The operator granted standing authorisation for reboots and WSL restarts. That
is a real and useful grant, and it is **narrower than this package**. The
distinction is worth stating plainly because conflating them is how an agent
ends up reconfiguring a machine on an inferred permission.

**A reboot is a transient act.** It stops running processes and starts them
again. Nothing about the machine is different afterwards. Its entire blast
radius is "things that were running are no longer running".

**This package is a persistent change to what the machine is.** Specifically:

1. **It installs a hypervisor underneath the running operating system.**
   Enabling Hyper-V does not add an application. It makes Windows itself boot as
   a guest of the Hyper-V hypervisor, which takes ownership of the hardware
   virtualisation extensions (`VT-x`/`AMD-V`) from that point on. The Windows
   the operator uses after the reboot is running in a partition, not on bare
   metal. That is why the reboot is required — you cannot slide a hypervisor
   under a running kernel.

2. **It takes exclusive ownership of a hardware resource.** Only one hypervisor
   can own the virtualisation extensions. Any other hypervisor on the machine
   must go through Hyper-V's platform APIs or lose hardware acceleration. This
   is the one consequence with real potential to disrupt other work, and it does
   not go away when you reboot again — it persists until the feature is disabled.

3. **It opens a new communication channel class on the host.** The registry key
   registers a guest-communication service so a VSOCK port inside a VM can reach
   a host-side listener. VSOCK carries no IP addressing; it is addressed by the
   VM's own UUID. This is why the VM can have **zero network adapters** and still
   be reachable — and it is a channel type that did not exist on this machine
   before.

4. **It creates persistent objects.** A VM definition and an attached virtual
   disk survive reboots, appear in Hyper-V Manager, and consume disk. A reboot
   creates nothing.

Put simply: **a reboot changes what is running; this changes what the machine
is.** Both were approved, but they were approved as separate things, and the
record should show that.

### 2.4 What changes on the operator's system, concretely

**Stops on the reboot and does not come back by itself:**

| Service | Where | Action |
| --- | --- | --- |
| **Hermes gateway** | WSL Ubuntu | **I relaunch it** |
| **Discord role-buttons bot** | WSL Ubuntu | **I relaunch it** |

**Restarts on its own, no action needed:**

- WSL2 Ubuntu — comes back with the host
- Docker Desktop — already uses the WSL2 backend, which already runs on the
  Windows hypervisor platform

**Needs checking before approval was given, and is worth restating:**

- **VirtualBox and VMware** lose hardware acceleration while Hyper-V is enabled,
  unless they are on versions using the Windows Hypervisor Platform API. If
  either is in use for anything that matters, say so before the reboot.

**Not affected:**

- No file in the repository, no data root, no credential store.
- No network configuration, no firewall rule, no Windows security setting.
- Nothing outside `E:\Projects\GreyTheory\runtime\hyperv\` is written.

### 2.5 What the package explicitly does not do

- **It does not raise the execution posture.** Posture stays `LOCAL_FIXTURE`.
  The worker touches no programme asset.
- **It does not enable network egress from the VM.** Zero adapters. Programme
  egress is a separate decision with its own review.
- **It does not contact any programme or submit anything.**
- **It does not grant the VM authority to act.** Carrier admission still
  requires a fresh signed observation pinned to the exact VM UUID and worker PID.

### 2.6 Rollback, in full

```powershell
Remove-VM -Name GreyTheory-Research-Worker -Force
Remove-Item "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Virtualization\GuestCommunicationServices\00004754-facb-11e6-bd58-64006a7986d3"
Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
```

Then reboot. The third command is the one that returns the virtualisation
extensions to whatever else wants them.

---

## Part 3 — Sequence from here

1. **Fix the seven HIGH audit findings** on the acceptance gate and the builder.
   Offline, no host change, no service interruption. This is in progress.
2. Re-run both suites; add regression tests that fail on the old behaviour.
3. Apply host-change package items 1–3, reboot, relaunch Hermes and the bot.
4. Create the VM, attach the normalised artifact.
5. Run the eight negative tests, feed the results through `validate_boot()`, and
   let `accept_artifact()` return something other than "awaiting boot evidence"
   for the first time.
6. Milestones 10–13.

---

## Part 4 — Diagram brief for Codex

**Request:** produce architecture diagrams for GreyTheory. Mermaid preferred, in
`Docs/diagrams/`, one file per diagram, each with a short prose caption stating
what the reader should take away.

The constraint that matters: **a diagram must not imply an authority the system
does not have.** If a box can reach a programme's asset, the diagram must show
the gate that stops it. Where a boundary is enforced in code, name the module on
the edge that crosses it.

### D1 — Posture model
The two axes as genuinely orthogonal: execution posture (`NONE` →
`LOCAL_FIXTURE` → `PASSIVE_HTTP` → …) against collector posture (`NONE` →
`PUBLIC_INTELLIGENCE` → `OPERATOR_ACCOUNT`). Mark today's position. Show that
moving right on one axis does not move the other. Source:
`greytheory_intelligence/posture.py`, `AuthorityLevel`.

### D2 — Command admission path
Browser → loopback transport → admission checks (Host, token, Origin,
Transfer-Encoding, Content-Type, body ceiling) → command bus → service. Show the
`/api/v1/credentials` route branching **after** the shared checks and **before**
`WorkbenchCommand.from_dict`, and say why: the bus digests whole commands for
idempotency and retains them, so a platform token must not enter it. Source:
`greytheory_local/transport.py`.

### D3 — The three integration tiers
Tier 1 public directory, tier 2 operator account, tier 3 submission. For each:
what crosses the boundary, what is refused, what authority it does and does not
confer. Mark tier 3's kill switch and payload-digest binding. Source:
`greytheory_intelligence/{directory_fetcher,account_reader,submission,authorisation}.py`.

### D4 — Artifact provenance chain
Canonical signed donor → assembly → observation record → offline validation →
FAT normalisation → VHDX conversion → container normalisation (ADR-0028) → VM →
boot evidence → `accept_artifact()`. **Show which digest is established at each
hop**, and mark clearly that signed components are *copied* and never rebuilt.
Source: `acceptance/`, ADR-0028.

### D5 — The acceptance gate
The two halves — offline structural and runtime boot — meeting at
`accept_artifact()`. This one has audit findings against it, so draw the
*intended* design and annotate where the current implementation falls short of
it. Useful precisely because the gap is the point.

### D6 — Learning loop
Programme scope → `programme_curriculum` rules → ranked topics → lesson →
checks → server-issued fixture receipt → participation → rank and card. Show
that participation derives from **server-issued receipts only**, because
hardcoded progression was a real governance defect here once.

### D7 — Carrier and worker lifecycle *(after the VM exists)*
VSOCK carrier, exact-UUID admission, one-use worker contract, cancellation and
reaping. Leave until there is a real VM to draw.

---

## Part 5 — Review questions carried forward

1. Is collector posture genuinely separable from execution posture, or does
   `OPERATOR_ACCOUNT` create a path toward target interaction not yet seen?
2. Does the credentials route's bypass of the command bus lose any admission
   check that route provides?
3. Is DPAPI same-profile protection adequate for platform tokens?
4. Does payload-digest binding prevent an edited submission, including
   whitespace-only and unicode-normalisation edits?
5. After the gate fixes: can any field on `BootReport` still be self-asserted by
   the thing under test rather than by an independent observer?
6. Do the eight negative tests collectively miss a failure mode of this design?
