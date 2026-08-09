# Contributing

Thanks for looking. This is a security control plane, so a few of the rules below are stricter than a typical project's — they exist because the failure modes are worse.

## Getting set up

```bash
pip install -e ".[dev]"
python -m pytest -q
```

Python 3.11+. No runtime dependencies, and that is a design constraint rather than a coincidence — see below.

## Non-negotiables

A pull request that breaks one of these will not be merged, however good the rest of it is.

**No runtime dependencies in `greytheory/`.** The thing that grants authority must have a small trust surface. Test-only dependencies are fine.

**No network code in `greytheory/`.** CI fails the build if a `socket`, `http`, `urllib`, `requests`, `httpx` or `aiohttp` import appears there. When lanes eventually need network access they will live in a separate package that can only act through a `Decision`.

**Fail closed.** Absence, ambiguity, staleness and error all resolve to denial. If you add a code path where an exception, a missing value or an unrecognised input could result in permission, that is a bug even if no test catches it.

**Every artifact carries an authority reference.** Anything produced under an allow must cite the contract fingerprint that allowed it.

**No self-award.** The system records what a programme said. It never asserts that a finding is valid, accepted, rewarded or disclosed.

**Injected clocks.** Anything time-dependent takes a `clock` callable. Staleness and expiry must be testable rather than flaky.

## Tests

Every behavioural change needs a test, and denial paths need them more than allow paths — an allow that should have been a denial is the failure that matters here.

Name tests for the behaviour, not the method: `test_out_of_scope_beats_in_scope_on_overlap`, not `test_classify_2`. If a test encodes a security property, say so in a comment so the next person does not "simplify" it away.

The fixtures in `fixtures/programmes/` use the reserved `.test` TLD (RFC 6761) and the `192.0.2.0/24` documentation range (RFC 5737). Keep it that way — no fixture may name a host that could resolve.

## Comments

Comment the *why*, not the *what*. The codebase leans on this: a
`ValidatorRegistry` receipt is single-use and assertion-bound because a caller
must never be able to launder model inference into proof by asserting that its
own check could have failed. If a rule prevents a specific mistake, name the
mistake.

## Reporting a security issue

Do not open a public issue. See [SECURITY.md](SECURITY.md).

## Scope of contributions

This project does not accept:

- exploit code, payloads, or scanner signatures;
- anything that performs network reconnaissance or target interaction;
- integrations that hold, transmit or validate credentials;
- features that would let the system submit reports, contact programmes, or publish findings. Those are operator acts by design.

Contributions are accepted under [Apache-2.0](LICENSE), per section 5 of the licence.
