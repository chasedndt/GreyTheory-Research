# ADR-0006 — Evidence-Bound Mastery and Synthetic Fixture Separation

- Date: 2026-08-09
- Status: ACCEPTED; IMPLEMENTED / VERIFIED OFFLINE 2026-08-09

## Context

Milestone 5 requires local vulnerability fixtures and six-dimensional mastery
tracking. Two silent promotions would undermine GreyTheory's evidence model:
treating a synthetic fixture as proof about a real target, and treating lab
completion as proof that a researcher has mastered a skill.

## Decision

Vulnerability cards are immutable, versioned reference knowledge. Framework
mappings classify them and never constitute evidence. Every built-in card has
one distinct synthetic local fixture with a positive control, deliberately
vulnerable case, and negative control. Its `FixtureRunReceipt` binds fixture and
runner digests and always states that it proves no real vulnerability and
credits no mastery.

Mastery is personal runtime state separate from the card. `explain`,
`recognise`, `test`, `prove`, `remediate`, and `transfer` are assessed
independently. A record requires a named assessor, exact card/dimension, level,
evidence references, rationale, time, and review date. Only a human assessment
credits mastery. A `test_fixture` assessment remains inspectable but
non-crediting. Model output cannot be recorded as a human assessor.

Personal mastery data is integrity-bound to one catalogue digest and refused
inside a Git working tree by default.

## Consequences

- Completing all 12 fixtures leaves all 72 credited mastery states at
  `not_assessed` until explicit human evidence is recorded.
- Fixture evidence cannot satisfy finding validation or be presented as a
  real-session example.
- A card revision may cite a labelled fixture proposal, as IDOR/BOLA v1.0.0
  does, without converting it into human or live-target evidence.
- Future training modes and models must consume these contracts rather than
  inventing a parallel completion or scoring system.
