# Architecture Diagrams

Rendered by GitHub natively. Every diagram here reflects code that exists in `greytheory/` unless a node is explicitly marked *aspirational*.

---

## 1. The three planes

Authority is the root. Signal and Judgement both hang off it, and neither can reach a target except through the gate.

```mermaid
flowchart TB
    subgraph P1["PLANE 1 — AUTHORITY (root, fail-closed)"]
        direction LR
        SRC[Programme source] --> COMP[Scope Compiler]
        COMP --> REV{Human review}
        REV -->|clean| CT[(ScopeContract<br/>VERIFIED)]
        REV -->|ambiguous| BLK[BLOCKED<br/>grants nothing]
        CT --> GATE{{Gate}}
        GATE --> AUD[(Append-only<br/>hash-chained audit)]
        KS[Kill switch] --> GATE
        POST[Posture ceiling] --> GATE
    end

    subgraph P2["PLANE 2 — SIGNAL (pluggable collectors)"]
        L1[Lane 1 · Known-Vuln]
        L2[Lane 2 · Exposure]
        L3[Lane 3 · Web Vuln]
        L4[Lane 4 · AI-App]
    end

    subgraph P3["PLANE 3 — JUDGEMENT (the operator loop)"]
        HYP[Hypothesis queue]
        SESS[Hunt session]
        VAULT[(Evidence vault)]
        GATES[Validation gates A-F]
        REPORT[Report studio]
        LEDGER[(Triage + earnings ledger)]
    end

    GATE -->|allow| P2
    GATE -.->|deny + reason| P3
    P2 -->|RawSignal| VAULT
    HYP --> SESS --> GATE
    VAULT --> GATES --> REPORT --> OP{{Operator decides}}
    OP --> LEDGER

    GV[Grapevine AI<br/>information-only] --> SRC
    GV --> HYP
    GV x--x P2

    style P1 fill:#1f2937,stroke:#f59e0b,stroke-width:3px,color:#f9fafb
    style P2 fill:#111827,stroke:#6b7280,color:#f9fafb
    style P3 fill:#111827,stroke:#6b7280,color:#f9fafb
    style BLK fill:#7f1d1d,stroke:#ef4444,color:#fff
    style GATE fill:#78350f,stroke:#f59e0b,color:#fff
    style OP fill:#065f46,stroke:#10b981,color:#fff
```

The crossed link from Grapevine to Plane 2 is the integration contract made visible: intelligence informs what we *look at* and what we *ask*, never what we *touch*.

---

## 2. Gate decision flow

Implemented in [`greytheory/authority/gate.py`](../greytheory/authority/gate.py). Every path — including every denial — writes an audit record before returning.

```mermaid
flowchart TD
    REQ[AccessRequest] --> KS{Kill switch<br/>engaged?}
    KS -->|yes| D1[DENY<br/>kill_switch_engaged]
    KS -->|no| C{Contract<br/>supplied?}
    C -->|no| D2[DENY<br/>no_contract]
    C -->|yes| B{Status<br/>BLOCKED?}
    B -->|yes| D3[DENY<br/>contract_blocked]
    B -->|no| V{VERIFIED and<br/>human_reviewed?}
    V -->|no| D4[DENY<br/>contract_not_verified]
    V -->|yes| S{Within trust<br/>window?}
    S -->|no| D5[DENY<br/>contract_stale]
    S -->|yes| T{Technique<br/>prohibited?}
    T -->|yes| D6[DENY<br/>technique_prohibited]
    T -->|no| CL{Classify asset}
    CL -->|out of scope| D7[DENY<br/>asset_out_of_scope]
    CL -->|unresolved,<br/>derived| D8[DENY<br/>derived_asset_not_inherited]
    CL -->|unresolved| D9[DENY<br/>asset_unresolved]
    CL -->|in scope| A1{Within contract<br/>authority?}
    A1 -->|no| D10[DENY<br/>authority_level_exceeded]
    A1 -->|yes| A2{Within posture<br/>ceiling?}
    A2 -->|no| D11[DENY<br/>posture_ceiling_exceeded]
    A2 -->|yes| OK[ALLOW<br/>+ authority_ref]

    OK --> LOG[(audit.jsonl)]
    D1 --> LOG
    D2 --> LOG
    D3 --> LOG
    D4 --> LOG
    D5 --> LOG
    D6 --> LOG
    D7 --> LOG
    D8 --> LOG
    D9 --> LOG
    D10 --> LOG
    D11 --> LOG

    style OK fill:#065f46,stroke:#10b981,color:#fff
    style LOG fill:#1e3a8a,stroke:#60a5fa,color:#fff
```

Eleven ways to be denied, one way to be allowed. That ratio is the design.

---

## 3. Contract compilation

The compiler cannot produce a contract that grants anything. Only a human can.

```mermaid
sequenceDiagram
    participant Op as Operator
    participant C as Scope Compiler
    participant H as sha256
    participant A as Audit log

    Op->>C: compile(programme record, raw source)
    C->>H: hash raw source
    H-->>C: sha256:...
    C->>C: parse scope patterns
    C->>C: detect overlaps, unparseable rules,<br/>missing rate limits, TBD markers,<br/>paused state, missing timestamp

    alt any ambiguity found
        C-->>Op: status = BLOCKED + reasons
        Note over Op,C: Cannot be reviewed into<br/>verification. Fix the source,<br/>recompile.
    else clean
        C-->>Op: status = PENDING_REVIEW
        Note over Op,C: Grants nothing yet.
        Op->>C: mark_reviewed(reviewer)
        C-->>Op: status = VERIFIED
    end

    C->>A: contract.compile record
```

---

## 4. Finding lifecycle

Implemented in [`greytheory/findings.py`](../greytheory/findings.py). The dashed boundary is invariant I5 — everything past it is recorded from a programme, never asserted by us.

```mermaid
stateDiagram-v2
    direction TB

    state "asserted by GreyTheory" as Internal {
        [*] --> informational
        informational --> contextual
        contextual --> candidate
        candidate --> validated
        validated --> report_ready
        report_ready --> candidate: demote<br/>(evidence weakened)
    }

    state "recorded from the programme" as External {
        submitted --> triaged
        triaged --> valid
        triaged --> duplicate
        triaged --> informative
        triaged --> not_applicable
        triaged --> out_of_scope
        valid --> rewarded
        valid --> no_reward
        rewarded --> fixed
        no_reward --> fixed
        fixed --> retested
        retested --> disclosed
        retested --> private_closed
        duplicate --> private_closed
        informative --> private_closed
        not_applicable --> private_closed
        out_of_scope --> private_closed
    }

    report_ready --> submitted: requires operator approval
    disclosed --> [*]
    private_closed --> [*]
```

Two guards sit on that boundary:

- `report_ready` requires at least one `checked` claim. Inference alone is not a report.
- Every state past `submitted` requires `programme_evidence` — a reference to what the programme actually said.

---

## 5. The provenance triple

```mermaid
flowchart LR
    OBS[observed<br/>a tool saw it] --> Q{Falsifiable<br/>check ran?}
    INF[inferred<br/>a model believes it] --> Q
    Q -->|yes, it could<br/>have failed| CHK[checked<br/>proven]
    Q -->|no| REJ[ProvenanceError<br/>promotion refused]

    CHK --> RPT[eligible for<br/>report_ready]
    OBS -.->|never alone| RPT
    INF -.->|never alone| RPT

    style CHK fill:#065f46,stroke:#10b981,color:#fff
    style REJ fill:#7f1d1d,stroke:#ef4444,color:#fff
```

A check that cannot fail proves nothing, so promotion demands `could_have_failed=True`. This is what stops model output from laundering itself into evidence.

---

## 6. Authority levels

Two independent caps apply to every request: what the contract grants, and what the current operating posture allows. The lower of the two wins.

```mermaid
flowchart LR
    subgraph Levels["AuthorityLevel (ordered)"]
        direction LR
        N[NONE<br/>0] --> LF[LOCAL_FIXTURE<br/>1] --> PH[PASSIVE_HTTP<br/>2] --> AU[AUTHENTICATED<br/>3] --> IN[INTRUSIVE<br/>4]
    end

    CEIL[Current posture ceiling:<br/>LOCAL_FIXTURE] -.->|caps everything<br/>above this| LF

    style LF fill:#065f46,stroke:#10b981,color:#fff
    style PH fill:#374151,stroke:#6b7280,color:#9ca3af
    style AU fill:#374151,stroke:#6b7280,color:#9ca3af
    style IN fill:#374151,stroke:#6b7280,color:#9ca3af
    style CEIL fill:#78350f,stroke:#f59e0b,color:#fff
```

Greyed levels are unreachable under the current posture regardless of what any contract says.
