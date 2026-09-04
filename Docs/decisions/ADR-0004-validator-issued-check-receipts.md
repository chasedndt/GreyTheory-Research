# ADR-0004 — Validator-Issued Check Receipts

- Date: 2026-08-09
- Status: ACCEPTED; IMPLEMENTED / VERIFIED OFFLINE 2026-08-09

## Decision

A claim may eventually become `checked` only by consuming a successful `CheckReceipt` issued by a registered deterministic validator. The receipt records validator/version, input hashes, assertion, possible and actual outcomes, time, runner digest, and authority reference.

## Consequences

The caller-supplied `could_have_failed=True` path has been removed.
`ValidatorRegistry` hashes exact byte inputs and validator source, records the
declared and actual outcomes, and consumes a successful matching receipt only
once. The local two-account acceptance test proves the supported, refuted,
forged/modified, and replay-denial paths. Persistence and trust across separate
processes are not claimed; the current registry is an in-process local control.
