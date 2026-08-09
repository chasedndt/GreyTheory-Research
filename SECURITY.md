# Security Policy

## What this repository is

GreyTheory is a human-governed Security Research Operating System whose trust kernel is a security research control plane. It decides whether research activity is authorised, records what happened, and refuses actions that fall outside a verified scope contract.

It contains no exploit code, no scanner, and no network client. The core package has no runtime dependencies and does not open sockets — enforced in CI by the `no-network-in-core` job.

## Reporting a vulnerability in GreyTheory itself

Open a [security advisory](https://github.com/) on this repository, or contact the maintainer privately. Please do not open a public issue for a vulnerability report.

Findings of particular interest, because they undermine the system's whole purpose:

- **Gate bypass** — any input that produces `ALLOW` when it should produce a denial.
- **Fail-open behaviour** — any path where absence, ambiguity or error results in permission rather than refusal.
- **Audit tampering** — any way to modify, reorder or remove an audit record while `verify()` still passes.
- **Provenance laundering** — any route by which an `inferred` claim reaches `checked` without a falsifiable check.
- **Self-award** — any way to enter a programme-outcome state without programme evidence.
- **Scope inheritance** — any case where a derived asset is treated as in scope because of what it was discovered through.

A working test that demonstrates the bypass is worth more than a description of it.

## What this project will not do

These are structural commitments, not preferences:

- It does not test, scan, or interact with systems it has not been authorised against.
- It does not hold, validate, or transmit credentials.
- It does not submit reports, contact programmes, or disclose findings. Those are operator acts.
- It does not assert that a finding is valid, accepted, or rewarded. Only a programme produces those states.

## Responsible use

This tooling is intended for authorised security research only: bug bounty and vulnerability disclosure programmes, contracted engagements, systems you own, and deliberately vulnerable local labs.

Nothing in this repository grants authority to test anything. A domain name is not authorisation, a public security page is not authorisation, and a compiled scope contract is not authorisation until a human has reviewed it against the programme's actual published rules.

The current operating posture is local-only. See [`Docs/scope-policy.md`](Docs/scope-policy.md).
