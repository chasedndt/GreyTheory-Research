# ADR-0019: Evaluate Windows CurrentUser DPAPI as the operator root-KEK provider

**Status:** Proposed — candidate host proof passes; operator approval pending

**Date:** 2026-09-04

## Context

The passive-capture key store already keeps each X25519 recipient private key
wrapped by an external 32-byte root key-encryption key (KEK). The repository
must not persist that KEK in plaintext, and the Ubuntu worker must never
receive it. Before any passive posture can be considered, the Windows operator
host needs a concrete OS-backed provider plus a tested recovery story.

Windows Data Protection API (DPAPI) can bind protected data to the current
Windows profile without introducing a network service or placing a credential
inside the trust kernel. That is useful evidence, but a profile-bound encrypted
record is not by itself an independent disaster-recovery design.

## Candidate decision

Evaluate a broker-side `WindowsDpapiRootKekProvider` with these fixed rules:

1. generate exactly 32 random bytes on first provision and refuse replacement;
2. protect a strict versioned payload with CurrentUser DPAPI,
   `CRYPTPROTECT_UI_FORBIDDEN`, a fixed GreyTheory purpose entropy value, and a
   fixed description;
3. refuse provider records inside any Git worktree and audit every provision
   and lease against an actor and authorisation reference;
4. expose the root only through a short-lived mutable lease whose owned buffer
   is overwritten on close;
5. use the lease only to open the existing operator-side capture-key store;
   the Ubuntu worker receives the public capture recipient, never the root KEK
   or a recipient private key; and
6. do not wire this provider into a launcher, posture switch, or worker until
   the remaining acceptance gates are independently approved.

This is a proposed candidate, not an accepted posture decision.

## Accepted evidence about the candidate

On 2026-09-04, the bounded Windows host harness proved:

- real CurrentUser DPAPI provision and unprotect on the operator host;
- no raw or hexadecimal root KEK in the retained private acceptance tree;
- zeroing of the lease-owned mutable buffer after close;
- capture-recipient provisioning and encrypted-capture decryption after a
  provider/store reopen;
- recovery from copied protected provider and wrapped-key records under the
  same Windows profile;
- refusal of a tampered protected record; and
- a valid audit chain.

The durable record is:
`E:\Projects\GreyTheory\acceptance\windows-dpapi-root-kek-20260904-095757-20740\acceptance.json`.

## Open decision gates

- The inherited evidence-directory ACL currently grants `Users` read/execute
  and `Authenticated Users` modify access. DPAPI still protects the root key,
  but an approved application-data ACL and tamper/backup policy have not been
  accepted.
- Copy recovery has been proven only inside the same Windows account/profile.
  Cross-profile or bare-machine disaster recovery is not implemented or
  accepted.
- Python can overwrite the lease-owned buffer; it cannot guarantee erasure of
  every temporary immutable copy made by the interpreter or OS crypto API.
- Provider records are capped at 64 KiB and initial publication is exclusive,
  so an oversized or concurrently pre-created record fails closed.
- The operator has not selected this as the approved root-key provider or
  approved the required profile/system backup procedure.
- Durable egress, hardened Ubuntu image, broker transport authentication,
  programme review, sustained operation, and explicit posture approval remain
  independent gates.

## Consequences

- The repository now has a concrete and host-tested Windows provider candidate
  instead of a placeholder external-KEK requirement.
- The candidate reduces plaintext-at-rest exposure without moving decryption
  authority into the worker.
- Loss of the Windows profile or its DPAPI material can still make retained
  captures unrecoverable; same-profile copy proof must not be advertised as
  disaster recovery.
- Operating posture remains `LOCAL_FIXTURE`; `PASSIVE_HTTP` remains unavailable.
