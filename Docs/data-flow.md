# Data Flow

How a programme's published rules become an artifact you can defend, and where each step is enforced.

## End to end

```mermaid
flowchart TD
    A[Programme rules<br/>read by a human] --> B[Programme record<br/>local JSON]
    B --> C[Scope Compiler]
    C --> D{Ambiguity?}
    D -->|yes| E[BLOCKED<br/>grants nothing]
    E -.->|fix source,<br/>recompile| B
    D -->|no| F[PENDING_REVIEW]
    F --> G{Human review}
    G -->|approved| H[(VERIFIED contract<br/>+ fingerprint)]
    H --> I{{Gate}}

    J[Hypothesis] --> RANK[Transparent ranking<br/>nine explained factors]
    ASSESS[Operator/test-fixture assessments<br/>rationale + provenance + uncertainty] --> RANK
    RANK --> QUEUE[Private research queue<br/>unproven · no authority]
    QUEUE --> I
    I -->|DENY + reason| K[Postmortem<br/>lesson recorded]
    I -->|ALLOW + authority_ref| L[Lane collector]
    L --> M[RawSignal<br/>tagged 'observed']
    M --> N[Registered deterministic validator]
    N -->|declared failure path<br/>+ successful CheckReceipt| O[Claim tagged 'checked']
    N -->|refuted, mismatched,<br/>forged, or replayed| P[Refused]
    O --> Q[(Evidence vault<br/>raw + redacted)]
    Q --> R[Validation gates B-F]
    R -->|fail| K
    R -->|pass| S[report_ready]
    S --> T{Operator<br/>approval}
    T -->|submit| U[Programme]
    U --> V[Triage outcome<br/>recorded, never asserted]
    V --> W[(Ledgers + lessons)]
    K --> W
    W --> Y[Card update proposal]
    Y -->|explicit revision provenance| Z[(Vulnerability catalogue)]
    Z --> AA[Skill graph<br/>six dimensions]
    W --> AB{Human mastery<br/>assessment?}
    AB -->|evidence + rationale<br/>+ review date| AC[(Private MasteryStore)]
    AB -->|fixture/model/completion only| AD[No mastery credit]

    I -.-> X[(audit.jsonl)]
    C -.-> X
    G -.-> X

    style E fill:#7f1d1d,stroke:#ef4444,color:#fff
    style P fill:#7f1d1d,stroke:#ef4444,color:#fff
    style I fill:#78350f,stroke:#f59e0b,color:#fff
    style T fill:#065f46,stroke:#10b981,color:#fff
    style X fill:#1e3a8a,stroke:#60a5fa,color:#fff
    style AD fill:#7f1d1d,stroke:#ef4444,color:#fff
```

Solid lines carry artifacts. Dotted lines to `audit.jsonl` carry the record of what happened — including every denial, which is the part most systems throw away.

## What crosses each boundary

| Boundary | Carries | Never carries |
|---|---|---|
| Programme rules → record | Scope, exclusions, prohibited techniques, rate limits, timestamps | Assumptions about anything the rules did not say |
| Record → contract | Parsed patterns, source hash, ambiguity list | A grant of authority — that requires a human |
| Contract → gate | Fingerprint, granted level, prohibitions, freshness | The action itself |
| Gate → lane | A `Decision` with `authority_ref` | Credentials, or permission to widen scope |
| Lane → vault | Raw signals, tagged `observed` | Conclusions. A lane may not promote past `contextual` |
| Vault → report | Redacted evidence, `checked` claims, provenance summary | Raw artifacts, third-party data, secrets |
| Report → programme | What the operator approved, verbatim | Anything the operator has not personally read |
| Programme → ledger | The outcome the programme actually stated | Our own opinion of what it should have been |
| Lesson → card proposal | Evidence references, checked-claim reference, explicit source kind | Automatic catalogue mutation or a real-session claim |
| Human assessment → mastery store | One card, one dimension, named evidence, rationale, time, review date | Lab-completion credit, model judgement, credentials, or raw evidence |
| Hypothesis + ranking inputs → research queue | Contract/workspace binding, nine explained ordinal factors, unproven theory, assumptions, stops | Probability, severity, proof, finding status, action request, execution authority, or model judgement |

## Two flows that do not exist

**No lane-to-target path that bypasses the gate.** There is no code path in `greytheory/` that opens a socket, and CI fails the build if a network import appears there. When lanes are built they will live outside this package and will take a `Decision` as a required argument.

**No intelligence-to-Plane-2 path.** When Scope Watch is built (roadmap Milestone 8) it will flow into the programme record and hypothesis queue only. It will not reach a collector, influence a gate decision, or become canonical scope without human review.

## Data retention

| Class | Where | Retention |
|---|---|---|
| Programme records, contracts | Repository | Versioned indefinitely; contracts are re-verified, not edited |
| Audit log | Local, gitignored | Indefinite. Never edited, never rotated silently |
| Raw evidence | Private, outside the repository (O3 unresolved) | Minimum necessary; deleted after disclosure closes |
| Redacted evidence | Separate from raw | As long as the finding is open |
| Vulnerability catalogue | Package reference data | Versioned with source and revision provenance |
| Personal mastery assessments | Private learning root outside Git | Retained until operator policy changes; review dates make staleness visible |
| Ranked research queues | Private research root outside Git | Integrity-bound decision-support snapshots; operator-controlled retention |
| Third-party data | Never retained | Stop condition, not a retention policy |
