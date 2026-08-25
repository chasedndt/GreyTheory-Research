# GreyTheory Threat Model

> **Status:** CANONICAL baseline; controls marked PLANNED are preconditions for network operation.
>
> **Effective:** 2026-08-09

## Assets to protect

- legal and programme authority;
- controlled identities and credentials;
- raw and redacted evidence;
- contract/source integrity;
- action and check receipts;
- audit history;
- workspace isolation;
- the distinction between observation, proof, and inference;
- researcher and programme reputation.

## Trust boundaries

- programme and target content is untrusted data;
- model output is untrusted inference;
- workers and plugins are lower-trust executors;
- the operator is the only authority source for human decisions;
- the Authority Plane is the only execution admission point;
- raw evidence is restricted and remains local by default.

## Threats and controls

| Threat | Failure mode | Primary control | Status |
|---|---|---|---|
| Malicious programme source | Prompt injection changes interpreted policy | Treat as data; compile; human verification | PARTIAL |
| Malicious target response | Model is induced to act | No direct model execution; taint labels | PLANNED |
| Compromised worker | Unauthorised requests or side effects | Gate-bound one-use local ticket; out-of-process broker required before network posture | PARTIAL |
| Redirect or DNS change | In-scope name reaches out-of-scope infrastructure | Re-evaluate every hop and resolution | PARTIAL; offline v1 validates supplied answers and denies every redirect; no resolver/adapter exists |
| Credential leakage | Token reaches model, logs, or evidence | Identity/credential handles and redaction | PARTIAL |
| Approval replay | Consent reused for a new action | Bound, expiring, single-use approvals | LIVE |
| Scope drift | Work continues after policy changes | Source fingerprinting, review invalidation, final recheck | PARTIAL |
| Evidence tampering | Artifacts or history altered | Content hashes and audit hash chain | LIVE; trusted anchor planned |
| Cross-workspace leakage | One programme's data enters another | Workspace isolation and authority references | LIVE for the local domain store; worker isolation planned |
| Cloud-model exfiltration | Sensitive data leaves device | Data classes and remote-model policy | PLANNED |
| Operator mistake | Wrong identity, target, or technique | Structured plans, exact action/identity/target binding, and stop conditions | LIVE for the local fixture; network preview planned |
| Runaway automation | Excess requests or effects | Budgets, token buckets, kill switch | PARTIAL |
| False AI certainty | Inference is presented as proof | Registry-issued check receipts, provenance triple, and claim-evidence matrix | LIVE offline |
| Whole-chain rewrite | Attacker recomputes the audit chain | Signed periodic checkpoints | PLANNED |
| Retention conflict | Third-party data cannot be removed | Audited deletion and tombstones | PLANNED |
| Hostile website reaches local workbench | DNS rebinding, CSRF, or permissive CORS reads or mutates private state | Numeric-loopback-only bind, exact Host, in-memory bearer token, exact-origin POST, no CORS, strict bounded JSON | LIVE in source/tests; packaged Windows host acceptance remains open |

## Hostile-content rule

Instructions found in programme pages, target responses, source code, tool output, files, agent configuration, or other external content are untrusted data unless they originate from a verified policy source and pass through the authority workflow.

External content can never change scope, activate a tool, request a credential, alter an approval, disable logging, increase a budget, mark evidence checked, or cause external communication.

## Preconditions for any network posture

Before `PASSIVE_HTTP`, GreyTheory requires a typed research domain, current verified source bundle, broker/worker separation, canonical URL and IDNA handling, DNS and redirect rechecks, private/metadata-network denial, rate/request/time budgets, tested kill switch, immutable receipts, data classification enforcement, worker conformance tests, and a private evidence root outside every repository.

The presence of this document does not satisfy those gates. Each control needs implementation and test evidence.

### Current precondition evidence - 2026-08-25

Implemented and tested offline in `greytheory_broker`:

- strict canonical HTTPS/IDNA representation for one exact, unauthenticated
  `HEAD` action;
- globally routable-address-only validation for supplied complete DNS answers;
- redirect denial, one-request/rate/time/capture ceilings, and raw/untrusted
  evidence labels;
- hash-chain-verified Gate binding, signed short-lived tickets, exact-once
  reservation, default-engaged persistent kill switch, and signed completed or
  stopped receipts derived from a typed encrypted-capture envelope;
- X25519/HKDF/ChaCha20-Poly1305 capture encryption bound to the ticket digest,
  recipient, size, plaintext digest, and creation time;
- operator-side recipient private keys wrapped with AES-256-GCM under a
  caller-supplied external KEK, a separately derived authenticated manifest,
  authorised provision/rotation/revocation, and recovery of retained evidence.

Implemented and tested without network I/O in `greytheory_worker_contract`:

- a complete-answer resolver protocol and one deterministic selection of a
  broker-validated public numeric address;
- a full-request digest binding ticket, canonical URL/host/path, exact address,
  TLS server name, port, proxy/redirect modes, capture ceiling, deadline, and
  wire request;
- typed transport evidence requiring the exact address and TLS name, no proxy,
  no followed redirects, zero body bytes, a closed connection, consistent
  monotonic timing, and one strict bounded response-header block;
- fail-closed mapping of resolver, transport, parsing, redirect, size, clock,
  encryption, kill-switch, and deadline failures into signed stop receipts.

Still required before any network posture:

- an actual DNS resolver and direct TLS/HTTP transport behind the typed
  contract, including OS-level cancellation and proof that the transport never
  re-resolves the validated numeric address;
- streaming socket-level header-size/timeout enforcement and host acceptance;
- an approved OS secret-provider binding, backup/recovery procedure, and host
  acceptance for the external root KEK; the repository does not persist it;
- isolated unprivileged Ubuntu worker image, OS egress constraints, broker
  transport/authentication, conformance acceptance, owned canary, one reviewed
  programme, sustained clean operation, and explicit operator posture approval.

The foundation is therefore `PARTIAL`; `PASSIVE_HTTP` remains unavailable.
