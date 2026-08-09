# ADR-0004 — Validator-Issued Check Receipts

- Date: 2026-08-09
- Status: ACCEPTED; implementation PLANNED

## Decision

A claim may eventually become `checked` only by consuming a successful `CheckReceipt` issued by a registered deterministic validator. The receipt records validator/version, input hashes, assertion, possible and actual outcomes, time, runner digest, and authority reference.

## Consequences

The current caller-supplied `could_have_failed=True` path is a migration gap and must not be removed until all current callers and tests have a receipt-based replacement.

