# ADR-0009 — Provider and fetcher boundaries keep the core offline

**Status:** Accepted · 2026-08-09
**Relates to:** Milestones 7 and 8.

## Context

Both milestones introduce a component whose obvious implementation makes a
network call: the model gateway talks to a provider, and Scope Watch fetches a
programme page.

The core package has never contained network code, and CI fails the build if a
network import appears in `greytheory/`. That constraint could have been
weakened twice in one session.

## Decision

**Neither component owns its I/O.** Both take a protocol and ship only an
offline implementation:

| Component | Protocol | Shipped in core | Real implementation |
|---|---|---|---|
| Model gateway | `ModelProvider` | `EchoProvider`, deterministic | Outside `greytheory/` |
| Scope Watch | `SourceFetcher` | `LocalSourceFetcher` | Outside, after posture raise |

Everything valuable is on this side of the boundary: classification, citation
checking, provenance, budgets, auditing, change detection, review invalidation.
The part that crosses the network is small, replaceable, and separately
governed.

`ScopeWatch` additionally refuses any fetcher declaring `network = True` unless
explicitly enabled, mirroring how the lane runner refuses network lanes.

## Consequences

Milestone 7 is complete. Milestone 8 is complete *offline*; its network fetcher
is deferred to the posture decision and the roadmap says so rather than
claiming the milestone whole.

The gateway's guarantees are provable without a key, a bill, or a network — the
eight-case evaluation suite runs against a stub.

## Supporting decisions

**Classification is enforced at assembly, not at send.** A request cannot exist
unless every fragment already passed the provider and role ceilings, so there
is no window in which an unclassified string is appended to a checked prompt.

**A remote provider can never be approved for `RAW_RESTRICTED`.** Enforced in
`ProviderPolicy.__post_init__`, not by configuration discipline.

**An unresolvable citation is refused, not flagged.** A model citing context
that was never supplied has invented a source. This is the cheapest reliable
fabrication detector available and it costs one set difference.

**Prompts are audited by digest, never by content.** The audit log must be
readable without re-exposing whatever sensitive fragment was in the prompt.

**`UNREACHABLE` is not `UNCHANGED`.** A source nobody could read has not been
shown to be the same. It needs attention but does not invalidate review on its
own, because "could not read it" is not "it changed".

**Negative fixtures in the eval suite assert that detectors fire.** Without
them a suite cannot distinguish a working harness from a well-behaved model,
and a permanently red suite is one nobody reads.
