# GreyTheory passive capture encryption - 2026-08-25

## Repository truth

- Starting commit: `42b5b15d8b416ed5b4ba4bfb8f16d8f07eb36ebb`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- E: had 687.01 GiB free during final verification.
- Canonical ChaseOS remained read-only and reported no working-tree changes at
  final verification.

## Repo-truth delta

The dark passive broker required an encrypted-envelope digest in receipts but
did not encrypt captures, hold a recipient lifecycle, or prevent callers from
supplying arbitrary capture digest metadata. A future worker could not yet
return confidential, ticket-bound evidence.

## Change

- Added typed X25519/HKDF-SHA256/ChaCha20-Poly1305 envelopes. Each capture uses
  an ephemeral key and authenticates ticket, recipient, plaintext digest, byte
  count, schema, algorithm, and creation time.
- Added an operator-side key store outside Git. X25519 private keys are wrapped
  with AES-256-GCM under a purpose-derived subkey from an external 32-byte root
  KEK; a different derived key authenticates the complete manifest. The root
  KEK is never persisted.
- Added mandatory hash-chain audit integration and actor/authority-bound
  provision, rotation, revocation, and decryption. Terminal transitions retain
  their actor and authority in the authenticated record; successful decryption
  audits only ticket/envelope/plaintext digests. Rotation retires the prior
  active key while retained private material can still decrypt immutable old
  evidence.
- Changed the broker guard to accept only a typed envelope bound to the signed
  ticket and its `evidence_key_ref`; receipt size and digests are derived from
  the envelope rather than caller assertions.

## Safety boundary

- There is still no resolver, HTTP/process adapter, worker transport, worker
  image, target request, environment-variable KEK fallback, or posture route.
- The repository does not implement or claim an approved Windows/Linux secret
  provider, hardware binding, backup/recovery acceptance, VM/VPS acceptance,
  or remote attestation.
- Ciphertext remains `RAW_RESTRICTED`; encryption does not reclassify evidence.
- No deployment, push, merge, secret use, target contact, canonical write, or
  posture change occurred.

## Verification

- Focused passive broker, encryption, and capability suite:
  `29 passed in 4.96s`.
- Full repository suite with pytest temp and bytecode paths rooted on E::
  `597 passed in 67.99s`.
- `python -m compileall -q greytheory greytheory_app greytheory_local
  greytheory_broker` passed with `PYTHONPYCACHEPREFIX` rooted on E:.
- Relative Markdown links passed for all 17 changed/new documentation files;
  `git diff --check` passed.
- Tests cover round-trip decryption, envelope/metadata tamper rejection,
  wrong-ticket and wrong-recipient stops, strict plaintext/timestamp input,
  external-KEK absence, wrong-KEK rejection, rotation, revocation, old-evidence
  recovery, authority audit binding, and Git-worktree refusal.

## Remaining

- Select and accept an OS secret provider for the external root KEK, including
  backup/recovery and host-level access acceptance.
- Implement the isolated DNS/HTTP adapter conformance boundary without enabling
  posture, then build and accept the unprivileged Ubuntu worker locally.
- Operator selection and implementation of visual direction 1, 2, or 3.
