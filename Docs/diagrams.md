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

    GV[Scope Watch<br/>roadmap · information-only] -.-> SRC
    GV -.-> HYP
    GV x--x P2

    style P1 fill:#1f2937,stroke:#f59e0b,stroke-width:3px,color:#f9fafb
    style P2 fill:#111827,stroke:#6b7280,color:#f9fafb
    style P3 fill:#111827,stroke:#6b7280,color:#f9fafb
    style BLK fill:#7f1d1d,stroke:#ef4444,color:#fff
    style GATE fill:#78350f,stroke:#f59e0b,color:#fff
    style OP fill:#065f46,stroke:#10b981,color:#fff
```

Scope Watch is dashed because it does not exist yet (roadmap Milestone 8). The crossed link to Plane 2 is its boundary made visible: external intelligence informs what we *look at* and what we *ask*, never what we *touch*.

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
    A2 -->|yes| AP{Above approval<br/>threshold?}
    AP -->|no| OK[ALLOW<br/>+ authority_ref]
    AP -->|yes| APC{Approval valid?}
    APC -->|missing / not found /<br/>denied / unbound /<br/>expired / already spent| D12[DENY<br/>approval_*]
    APC -->|granted, bound,<br/>fresh, unspent| OK

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
    D12 --> LOG

    style OK fill:#065f46,stroke:#10b981,color:#fff
    style LOG fill:#1e3a8a,stroke:#60a5fa,color:#fff
```

Seventeen ways to be denied, one way to be allowed. That ratio is the design.

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
    OBS[observed<br/>a tool saw it] --> REG{Registered validator<br/>runs on exact bytes}
    INF[inferred<br/>a model or human believes it] --> REG
    REG -->|supported receipt<br/>matches assertion| USE{Receipt issued here<br/>and unused?}
    REG -->|refuted or invalid| REJ[CheckError<br/>promotion refused]
    USE -->|yes, consume once| CHK[checked<br/>proven]
    USE -->|forged, changed,<br/>mismatched or replayed| REJ

    CHK --> RPT[eligible for<br/>report_ready]
    OBS -.->|never alone| RPT
    INF -.->|never alone| RPT

    style CHK fill:#065f46,stroke:#10b981,color:#fff
    style REJ fill:#7f1d1d,stroke:#ef4444,color:#fff
```

A check that cannot fail proves nothing. Promotion therefore consumes a
successful, matching `CheckReceipt` issued by a registered validator whose
declared outcomes include failure. Caller-created, modified, refuted,
mismatched, and replayed receipts are refused.

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

---

## 7. Approvals — bound, expiring, single-use

Implemented in [`greytheory/authority/approvals.py`](../greytheory/authority/approvals.py). Scope says *what may be touched*; an approval says *that this specific act was consented to, once, recently*. Neither substitutes for the other.

```mermaid
flowchart TD
    REQ[Request above the<br/>approval threshold] --> S{Store configured?}
    S -->|no| E1[DENY approval_required]
    S -->|yes| P{approval_id<br/>presented?}
    P -->|no| E2[DENY approval_required]
    P -->|yes| L{Record found?}
    L -->|no| E3[DENY approval_not_found]
    L -->|yes| G{Decision is<br/>APPROVE?}
    G -->|no| E4[DENY approval_denied]
    G -->|yes| B{Covers this<br/>action AND<br/>this target?}
    B -->|no| E5[DENY approval_not_binding]
    B -->|yes| X{Within the<br/>expiry window?}
    X -->|no| E6[DENY approval_expired]
    X -->|yes| C{Already spent?}
    C -->|yes| E7[DENY approval_already_consumed]
    C -->|no| OK[ALLOW<br/>approval consumed]

    C -.->|checked against| AUD[(audit.jsonl<br/>prior allows)]

    style OK fill:#065f46,stroke:#10b981,color:#fff
    style AUD fill:#1e3a8a,stroke:#60a5fa,color:#fff
```

Single-use is enforced against the audit log rather than a second ledger — the log already records every allow, so it already knows what has been spent. Only *allows* consume: a denied attempt on the wrong target does not silently void a legitimate approval.

### Where approvals come from

```mermaid
flowchart LR
    subgraph GT["GreyTheory (Apache-2.0, standalone)"]
        PROTO[ApprovalStore<br/>protocol]
        LOCAL[LocalApprovalStore<br/>self-sufficient default]
        ADAPT[ChaseOSApprovalStore<br/>adapter]
        GATE{{Gate}}
    end

    OSRIL[(ChaseOS OSRIL<br/>&lt;vault&gt;/runtime/osril/approvals/<br/>*.response.json)]

    LOCAL --> PROTO
    ADAPT --> PROTO
    PROTO --> GATE
    OSRIL -.->|filesystem contract,<br/>not a Python import| ADAPT

    style GT fill:#111827,stroke:#f59e0b,color:#f9fafb
    style OSRIL fill:#374151,stroke:#6b7280,color:#f9fafb
    style GATE fill:#78350f,stroke:#f59e0b,color:#fff
```

GreyTheory requires nothing external to run. Where an approval system already exists it reads from that one instead of keeping a parallel set of records — approvals recorded in one place and invisible to another are worse than either alone.

---

## 8. Evidence — raw stays, redacted travels

Implemented in [`greytheory/evidence.py`](../greytheory/evidence.py), policy in [`evidence-policy.md`](evidence-policy.md).

```mermaid
flowchart TD
    CAP[Capture] --> AUTH{authority_ref<br/>present?}
    AUTH -->|no| R1[Refused — I2]
    AUTH -->|yes| DUP{Artifact id<br/>already exists?}
    DUP -->|yes| R2[Refused —<br/>raw is written once]
    DUP -->|no| RAW[(raw/&lt;finding&gt;/&lt;id&gt;<br/>sha256 recorded<br/>sensitive = true)]

    RAW --> RED[Operator redacts]
    RED --> SAME{Byte-identical<br/>to raw?}
    SAME -->|yes| R3[Refused —<br/>nothing was redacted]
    SAME -->|no| REDACTED[(redacted/&lt;finding&gt;/&lt;id&gt;<br/>sha256 recorded)]

    REDACTED --> EXP{Export requested}
    RAW -.->|never| EXP
    EXP --> ALL{Every artifact<br/>redacted?}
    ALL -->|no| R4[Refused —<br/>export is all-or-nothing]
    ALL -->|yes| VER{Hashes still<br/>match disk?}
    VER -->|no| R5[Refused —<br/>integrity check failed]
    VER -->|yes| PKG[Export package<br/>redacted paths only]

    style RAW fill:#7f1d1d,stroke:#ef4444,color:#fff
    style REDACTED fill:#065f46,stroke:#10b981,color:#fff
    style PKG fill:#065f46,stroke:#10b981,color:#fff
    style R1 fill:#374151,stroke:#6b7280,color:#f9fafb
    style R2 fill:#374151,stroke:#6b7280,color:#f9fafb
    style R3 fill:#374151,stroke:#6b7280,color:#f9fafb
    style R4 fill:#374151,stroke:#6b7280,color:#f9fafb
    style R5 fill:#374151,stroke:#6b7280,color:#f9fafb
```

Red is private and never leaves. Green is the only thing that may be shared.

### Where the vault lives

```mermaid
flowchart TD
    START[Resolve evidence root] --> E1{explicit<br/>argument?}
    E1 -->|yes| USE[Use it]
    E1 -->|no| E2{GREYTHEORY_<br/>EVIDENCE_ROOT?}
    E2 -->|yes| USE
    E2 -->|no| E3{CHASEOS_<br/>VAULT_ROOT?}
    E3 -->|yes| CH[&lt;vault&gt;/07_LOGS/<br/>greytheory-evidence]
    E3 -->|no| DEF[Platform user-data dir<br/>standalone default]
    CH --> GUARD
    DEF --> GUARD
    USE --> GUARD{Inside a git<br/>working tree?}
    GUARD -->|yes| REFUSE[VaultLocationError<br/>refuse to initialise]
    GUARD -->|no| OPEN[Vault opens]

    style REFUSE fill:#7f1d1d,stroke:#ef4444,color:#fff
    style OPEN fill:#065f46,stroke:#10b981,color:#fff
    style DEF fill:#065f46,stroke:#10b981,color:#fff
```

The guard is a wall rather than a convention. A `.gitignore` entry can be defeated by a `git add -f` or a tired evening, and raw evidence once committed and pushed is unrecoverable — it survives in the reflog, in forks, in caches.

---

## 9. Validation gates B–F

Implemented in [`greytheory/validation.py`](../greytheory/validation.py), policy in [`validation-policy.md`](validation-policy.md).

```mermaid
flowchart TB
    F[Finding + evidence + draft] --> B

    subgraph ATT["Attested — require a recorded human statement"]
        B[B · Reproducibility<br/>attestation + a 'checked' claim]
        C[C · Impact<br/>attestation + a 'checked' claim]
        E[E · Duplicate risk<br/>attestation, certainty claims rejected]
    end

    subgraph DET["Deterministic — re-derived from artifacts every run"]
        D[D · Evidence<br/>rehashed from disk, all redacted, exportable]
        FQ[F · Report quality<br/>sections present, finished, severity reasoned]
    end

    B --> R{All five pass?}
    C --> R
    E --> R
    D --> R
    FQ --> R

    R -->|no| BLOCK[Blocked<br/>FAIL = someone looked, it did not hold<br/>NOT_ASSESSED = nobody looked]
    R -->|yes| G{{Gate G — the operator}}
    G -->|decides to send| SUB[Submitted]
    G -->|decides not to| ARCH[Archive or<br/>keep as a lesson]

    style DET fill:#1f2937,stroke:#60a5fa,color:#f9fafb
    style ATT fill:#1f2937,stroke:#f59e0b,color:#f9fafb
    style G fill:#065f46,stroke:#10b981,color:#fff
    style BLOCK fill:#7f1d1d,stroke:#ef4444,color:#fff
```

Passing every gate does not submit anything and does not advance the finding. It makes the finding *eligible* for Gate G, which is the operator's and is not automatable.

---

## 10. The whole path

```mermaid
flowchart LR
    A[Programme rules] --> B[Compile]
    B --> C[Human review]
    C --> D{{Gate}}
    D --> E[Approval]
    E --> F[Collector]
    F --> G[(Evidence vault)]
    G --> H[Gates B-F]
    H --> I[Report draft]
    I --> J{{Gate G · operator}}
    J --> K[Programme]
    K --> L[(Ledgers + lessons)]
    D -.->|deny| L
    H -.->|blocked| L

    style D fill:#78350f,stroke:#f59e0b,color:#fff
    style J fill:#065f46,stroke:#10b981,color:#fff
    style L fill:#1e3a8a,stroke:#60a5fa,color:#fff
```

Every arrow is a place the system can refuse. The dotted lines matter as much as the solid ones — a denial and a blocked validation are both recorded as lessons rather than discarded.

---

## 11. Programme registry — scope over time

Implemented in [`greytheory/registry.py`](../greytheory/registry.py). The compiler answers "what do these rules mean today"; the registry answers "what changed since you last looked, and does your permission still hold".

```mermaid
flowchart TD
    SRC[Programme source text] --> REG[register]
    REG --> H{Source hash vs<br/>previous version}
    H -->|first registration| V1[v1 · PENDING_REVIEW]
    H -->|unchanged| CARRY[New version ·<br/>review carried forward]
    H -->|changed| FRESH[New version ·<br/>REVIEW INVALIDATED]

    CARRY --> D
    FRESH --> D[Diff vs previous]
    V1 --> STORE
    D --> N{Narrowing?}
    N -->|yes| WARN[Permission shrank —<br/>re-examine work already<br/>done on removed assets]
    N -->|no| STORE[(v N .json<br/>+ source/v N .txt)]
    WARN --> STORE

    STORE --> ATT[needs_attention]
    ATT --> B[blocked]
    ATT --> A[awaiting_review]
    ATT --> S[stale]

    style FRESH fill:#78350f,stroke:#f59e0b,color:#fff
    style WARN fill:#7f1d1d,stroke:#ef4444,color:#fff
    style CARRY fill:#065f46,stroke:#10b981,color:#fff
```

The rule that carries the module: **changed source invalidates the human review**, however thoroughly the previous version was verified. Review attaches to the text a person actually read, not to the programme in the abstract. Identical source carries the review forward, because re-reading unchanged text is friction with no safety value.

`needs_attention()` is the registry's real output. A list of programmes is inert; a list of reasons the permissions might not hold any more is what prevents scope amnesia.

---

## 12. The ledger — every hour, not just the productive ones

Implemented in [`greytheory/ledger.py`](../greytheory/ledger.py). Invariant I6 made structural.

```mermaid
flowchart TB
    subgraph IN["Recorded"]
        S[Sessions<br/>study · lab · research · hunt<br/>report · triage · retest]
        T[Triage outcomes<br/>canonical + platform wording]
        P[Payouts<br/>gross · fees · share · tax]
        X[Expenses]
    end

    S --> H[Total tracked hours]
    P --> N[Net before tax]
    X --> N
    H --> R[Effective hourly<br/>= net ÷ ALL hours]
    N --> R

    T --> V[valid rate · duplicate rate<br/>over closed outcomes only]

    R --> F{forecast requested}
    V --> F
    F -->|below thresholds| REFUSE[InsufficientData<br/>names exactly what is missing<br/>'Until then, plan on zero.']
    F -->|100h · 20 sessions ·<br/>5 submissions ·<br/>5 closed outcomes| DIST[Monthly distribution<br/>median · quartiles ·<br/>P zero-month ·<br/>income concentration]

    style REFUSE fill:#7f1d1d,stroke:#ef4444,color:#fff
    style R fill:#78350f,stroke:#f59e0b,color:#fff
    style DIST fill:#065f46,stroke:#10b981,color:#fff
```

Two things this shape prevents. **The rate has no other version** — there is no parameter to divide by only the hours that produced something, because that is exactly how bug bounty starts looking like a good hourly rate. And **months with no payout stay in the distribution**; dropping them is how a zero-income month becomes invisible and the median starts describing a fantasy.

Income concentration is reported because when one payout dominates, the median is describing luck rather than a rate.

---

## 13. Vulnerability cards and the skill graph

Implemented in [`greytheory/learning/`](../greytheory/learning/). Reference
knowledge ships with the package; personal mastery state does not.

```mermaid
flowchart LR
    CAT[(12-card catalogue<br/>versioned reference data)]
    CARD[VulnerabilityCard<br/>hypothesis template<br/>minimum evidence<br/>review + revisions]
    FIX[LocalTrainingFixture<br/>positive · vulnerable · negative]
    RECEIPT[FixtureRunReceipt<br/>fixture + runner digests]
    GRAPH[SkillGraph<br/>acyclic prerequisites]
    DIMS[Six independent dimensions<br/>explain · recognise · test<br/>prove · remediate · transfer]
    HUMAN[Explicit human assessment<br/>evidence · rationale · review date]
    TEST[Test-fixture assessment]
    STORE[(Private MasteryStore<br/>integrity + catalogue digest)]
    NONE[No real-vulnerability proof<br/>No automatic mastery]

    CAT --> CARD
    CARD --> FIX
    CARD --> GRAPH
    FIX --> RECEIPT
    RECEIPT --> NONE
    GRAPH --> DIMS
    HUMAN --> STORE
    TEST -->|visible, non-crediting| STORE
    STORE --> DIMS

    style NONE fill:#7f1d1d,stroke:#ef4444,color:#fff
    style HUMAN fill:#065f46,stroke:#10b981,color:#fff
    style STORE fill:#1e3a8a,stroke:#60a5fa,color:#fff
```

This shape prevents three silent promotions: a taxonomy mapping becoming
evidence, a synthetic lab becoming a real finding, and task completion becoming
mastery. Only a named, evidence-bound human assessment credits one dimension;
the other five remain unchanged.

---

## 14. Transparent hypothesis ranking boundary

Implemented in [`greytheory/hypothesis/`](../greytheory/hypothesis/). Ranking
orders existing theories for human planning; it cannot plan or execute them.

```mermaid
flowchart LR
    H[Existing Hypothesis<br/>draft · scoped · planned]
    C[Verified ScopeContract<br/>current fingerprint]
    W[ResearchWorkspace<br/>evidence + budgets + effects]
    A[Explicit assessments<br/>likelihood · impact · duplicate risk<br/>skill value · novelty]
    P[Versioned RankingPolicy<br/>nine factors · directions · weights]
    E[Deterministic ranker<br/>explain every contribution]
    SR[Scope-review partition<br/>fail closed]
    Q[Private ResearchQueue<br/>unproven · integrity bound]
    OP[Human selects next planning work]
    NO[No action request<br/>No receipt · No finding<br/>No execution authority]

    H --> E
    C --> E
    W --> E
    A --> E
    P --> E
    E -->|scope basis incomplete| SR
    E -->|scope basis current| Q
    SR --> Q
    Q --> OP
    Q --> NO

    style SR fill:#78350f,stroke:#f59e0b,color:#fff
    style Q fill:#1e3a8a,stroke:#60a5fa,color:#fff
    style NO fill:#7f1d1d,stroke:#ef4444,color:#fff
    style OP fill:#065f46,stroke:#10b981,color:#fff
```

The four record-derived factors are scope confidence, evidence quantity, test
cost, and side-effect risk. The five explicit factors must identify their source
and uncertainty. The resulting number is an ordinal queue score only: it cannot
be reinterpreted as likelihood of a vulnerability, severity, proof, or
permission to act.

---

## 15. AI-native learner loop

The learner-facing workbench begins with one next safe mission and makes every
transition inspectable. AI can explain and critique; it cannot execute, check
evidence, or award mastery.

```mermaid
flowchart LR
    TODAY["Today: one next safe mission"] --> LEARN["Learn: concept and boundaries"]
    LEARN --> PRACTISE["Practise: synthetic local fixture"]
    PRACTISE --> PROVE["Prove: evidence and receipt"]
    PROVE --> REFLECT["Reflect: limits and lesson"]
    REFLECT --> ASSESS["Assess: explicit human judgement"]
    ASSESS --> TRANSFER["Transfer: distinct local context"]
    TRANSFER --> TODAY

    AUTH["Authority envelope\nLOCAL_FIXTURE · no live targets"] --> TODAY
    AUTH --> PRACTISE
    AUTH --> PROVE
    COACH["AI coach\nexplain · question · critique"] -. advisory .-> LEARN
    COACH -. advisory .-> REFLECT
    COACH -. "cannot execute or award mastery" .-> ASSESS

    style AUTH fill:#78350f,stroke:#f59e0b,color:#fff
    style COACH fill:#1e3a8a,stroke:#60a5fa,color:#fff
    style ASSESS fill:#065f46,stroke:#10b981,color:#fff
```

---

## 16. Pilot launch and worker transition

The learner pilot starts on the Windows operator workstation. Ubuntu becomes an
isolated worker only after local acceptance; a VPS is a later availability
choice, not a shortcut around host, key, egress, receipt, or posture gates.

```mermaid
flowchart LR
    WIN["Windows operator workstation\nWorkbench + local service + offline core"]
    FIX["Controlled local fixtures\nLOCAL_FIXTURE"]
    VM["Ubuntu 24.04 local VM\nacceptance only"]
    VPS["Ubuntu VPS\nscheduled passive availability"]
    LIVE["PASSIVE_HTTP\none ticket · one target · one receipt"]

    WIN --> FIX
    FIX -->|"learner pilot accepted"| VM
    VM -->|"host, egress, key and receipt gates pass"| VPS
    VPS -->|"explicit posture approval"| LIVE
    LIVE -. "receipt + encrypted capture" .-> WIN

    style FIX fill:#065f46,stroke:#10b981,color:#fff
    style VM fill:#1e3a8a,stroke:#60a5fa,color:#fff
    style VPS fill:#78350f,stroke:#f59e0b,color:#fff
    style LIVE fill:#7f1d1d,stroke:#ef4444,color:#fff
```
## 17. Case-pack learner loop and live-programme boundary

```mermaid
flowchart LR
    Goal["Learner goal"] --> Planner["Inspectable recommendation"]
    Planner --> Pack["Versioned case pack"]
    Pack --> Learn["Learn"]
    Learn --> Practise["Practise in LOCAL_FIXTURE"]
    Practise --> Receipt["Immutable synthetic receipt"]
    Receipt --> Prove["Prove with limitations"]
    Prove --> Reflect["Reflect"]
    Reflect --> Assess["Human assessment"]
    Assess --> Transfer["Independent transfer"]
    Pack -. "dark compatibility fields" .-> Live["Future programme adapter"]
    Live -. "requires all five gates" .-> Worker["Ubuntu passive worker"]
```

## 18. Five-gate transition to a passive pilot

```mermaid
flowchart TB
    Current["LOCAL_FIXTURE research preview"] --> W["1. Windows installed acceptance"]
    W --> U["2. Ubuntu full-worker acceptance"]
    U --> E["3. Durable egress and key-provider acceptance"]
    E --> P["4. One verified programme review"]
    P --> H["5. Explicit human posture approval"]
    H --> Pilot["PASSIVE_HTTP pilot: one programme, one action type"]
    VPS["Optional VPS deployment"] -. "only after local image acceptance" .-> Pilot
```

## 19. Interactive topic progression

```mermaid
flowchart LR
    Topic["Selected topic"] --> Note["Topic-owned focused note"]
    Note --> Lens["Traditional + AI lenses"]
    Lens --> L1["1 · Beginner orientation"]
    L1 --> L2["2 · Foundation mapping"]
    L2 --> L3["3 · Applied local controls"]
    L3 --> L4["4 · Independent transfer"]
    L3 --> Receipt["Synthetic evidence receipt"]
    Receipt --> Review["Human assessment"]
    Click["Trajectory click"] -. "previews path only" .-> L4
    Click -. "cannot award" .-> Review

    style Topic fill:#1e3a8a,stroke:#60a5fa,color:#fff
    style Receipt fill:#065f46,stroke:#10b981,color:#fff
    style Review fill:#78350f,stroke:#f59e0b,color:#fff
```

## 20. Public intelligence boundary

```mermaid
flowchart LR
    UI["Workbench Intelligence panel"] --> Plan["CONTRACT_ONLY request plan"]
    Plan --> Validate["CVE or versioned package validation"]
    Validate --> Registry["OSV · CISA KEV · EPSS · NVD · GitHub Advisories"]
    Registry -. "future accepted worker" .-> Fetch["Read-only fetch + bounded cache"]
    Fetch --> Source["Immutable source + retrieval evidence"]
    Source --> Offline["Offline enrichment and learning"]
    Offline -. "never becomes" .-> Proof["Live finding proof"]
    Target["Hostname · target · scan · exploit input"] --> Deny["Fail closed"]
    Account["HackerOne / Bugcrowd credentials"] -. "server-side gate only" .-> Fetch

    style Plan fill:#1e3a8a,stroke:#60a5fa,color:#fff
    style Source fill:#065f46,stroke:#10b981,color:#fff
    style Deny fill:#7f1d1d,stroke:#ef4444,color:#fff
    style Proof fill:#7f1d1d,stroke:#ef4444,color:#fff
```
