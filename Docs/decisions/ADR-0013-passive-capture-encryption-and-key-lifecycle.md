# ADR-0013 - Encrypt passive captures before a network worker exists

**Status:** Accepted - 2026-08-25

**Relates to:** Milestone 9, ADR-0009, and ADR-0011.

## Context

ADR-0011 made an encrypted-envelope digest mandatory in a completed passive
receipt but deliberately shipped neither capture encryption nor key handling.
Adding a resolver or HTTP client before closing that gap would allow a future
lower-trust worker to hold raw target bytes without a proven confidentiality
boundary. A digest proves integrity, not confidentiality.

The worker must not receive the operator's decryption key. Rotation must not
make old immutable evidence unreadable, and key state must not be stored in a
Git worktree. At the same time, repository code cannot truthfully claim that
Windows DPAPI, a Linux secret service, a hardware module, backup, or host
hardening is accepted when none has been selected or tested.

## Decision

Implement an offline encryption and recipient-key lifecycle inside
`greytheory_broker`, still with no network or process adapter:

- provision only an X25519 public recipient to a future lower-trust worker;
- generate an ephemeral X25519 key for every capture, derive a unique 256-bit
  key with HKDF-SHA256 salted by the signed ticket digest, and encrypt with
  ChaCha20-Poly1305;
- authenticate the schema, algorithm, ticket digest, recipient key ID,
  plaintext digest, byte count, and creation time as associated data;
- make the broker guard accept only the typed envelope and derive completed
  receipt digests and byte counts from it, refusing wrong-ticket or
  wrong-recipient envelopes;
- keep recipient private keys operator-side, wrap each with AES-256-GCM under
  a purpose-derived subkey from an externally supplied 32-byte root KEK, and
  authenticate the complete manifest with a separately derived subkey;
- require a hash-chained audit log plus actor and authority reference for
  provision, rotation, revocation, and decryption; persist transition actors
  and authority references in the authenticated key record, and retain retired
  or revoked private keys only so previously captured immutable evidence
  remains decryptable;
- refuse key storage inside Git, write atomically, use restrictive filesystem
  modes where the host supports them, and never persist the root KEK.

The root KEK is an injection boundary, not a completed secret-management
claim. No default, environment-variable fallback, command-line flag, or test
key is provided for operational use.

## Consequences

The future worker can encrypt response bytes with public material while being
unable to decrypt stored captures or mint passive tickets. Ciphertext
tampering, metadata tampering, the wrong private key, the wrong ticket, the
wrong recipient, a corrupted manifest, and a wrong root KEK fail closed.
Rotation retires the previous active recipient and preserves evidence
recovery; revocation removes a recipient from future active use. Successful
decryption appends the ticket, envelope, and plaintext digests to the audit
chain without recording plaintext.

Encryption does not change classification: the envelope remains
`RAW_RESTRICTED`. The key store is designed for one governed local operator;
multi-process key administration, an approved OS secret-provider binding,
backup/recovery acceptance, hardware binding, remote attestation, worker
transport, DNS/HTTP conformance, VM/VPS acceptance, and target contact remain
unimplemented. The capability stays `PARTIAL`, the worker stays `UNAVAILABLE`,
and the operating posture stays `LOCAL_FIXTURE`.
