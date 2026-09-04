# GreyTheory Threat Model

> **Status:** CANONICAL baseline; controls marked PLANNED are preconditions for network operation.
>
> **Effective:** 2026-08-26

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

Implemented in the dark `greytheory_worker` package, with no launcher,
scheduler, programme route, or enabled posture:

- blocking system resolution of the absolute DNS name in one specifically
  owned spawn child, using capped non-pickle JSON pipe output and exact
  terminate/kill cleanup at the total deadline;
- direct numeric-address TCP connect with no URL/proxy API or re-resolution,
  followed by TLS 1.2+ using an explicit CA bundle, canonical SNI and hostname
  verification, HTTP/1.1 ALPN, compression/renegotiation controls, and disabled
  TLS key logging;
- exact peer-address verification, total-deadline connect/handshake/write/read
  timeouts, one bounded header block, rejection of observed body bytes, and
  deterministic close on success, timeout, TLS failure, overflow, or mismatch.
- a capped, canonical-JSON, two-command owned-process channel: resolve once,
  return the complete answer for broker recheck, then accept one exact request
  only for that host and one address in the worker's own answer;
- parent-only ticket/receipt keys, replay ledger, kill-switch authority,
  capture private key, and research state; the child receives only its channel
  and explicit CA path;
- child environment scrubbing plus refusal unless the worker reports non-root
  UID/GID, no foreign supplementary groups, zero effective/bounding
  capabilities, and no-new-privileges.

Accepted on the operator's Ubuntu 24.04 WSL2 host without external contact:

- an ephemeral user/network namespace exposes only loopback and no default
  route, with a globally routable-looking address assigned locally solely to
  exercise the unchanged public-address request contract;
- the production direct transport proves numeric no-re-resolution, explicit
  test-CA and hostname enforcement, refusal of a hostname mismatch, two-write
  header streaming, zero body, and deterministic close against an owned canary;
- a real spawned resolver child deliberately blocks past its deadline and is
  terminated and reaped by the production resolver parent.

Accepted full-service local host harness:

- `acceptance/ubuntu_worker_service.py` and its PowerShell wrapper construct a
  no-default-route namespace, temporary synthetic hosts view, non-root
  capability-empty process, full resolver/broker recheck/direct TLS path,
  encrypted capture, exact-once ledger completion, and signed receipt against
  the owned canary;
- recovered runs exposed and fixed PowerShell/native quoting, WSL's nested
  `/etc/hosts` mount, the resolver's deliberate trailing-dot absolute name,
  masked worker exceptions, nested spawn overhead, and unbounded Windows-side
  client cleanup;
- the latest source uses WSL root only to create the namespace, maps Python to
  UID/GID 65534, starts the outer worker from a clean fork server, forks the
  cancellable resolver only inside the scrubbed authority-free worker, and
  bounds/stops only its owned Windows WSL clients on timeout;
- on 2026-09-04 the remaining Windows CRLF checkout defect was fixed by
  enforcing LF for shell entrypoints; the Ubuntu 24.04.4 run then emitted a
  complete durable JSON record with system resolution, broker recheck, exact
  synthetic request, encrypted capture, verified receipt, completed replay,
  non-root/zero-capability/no-new-privileges identity, and clean worker exit;
- the wrapper validates that record, retains separate stderr evidence, and did
  not terminate the shared distro or unrelated WSL clients.

Candidate Windows operator-key host proof:

- a real CurrentUser DPAPI provider generates and protects the external
  32-byte root KEK with UI forbidden, refuses Git storage and replacement, and
  audits bound provision/lease operations;
- a short-lived mutable lease opens the existing operator capture-key store and
  overwrites its owned buffer on close; the worker receives neither the root
  KEK nor recipient private keys;
- same-profile restart and protected-record copy recovery, encrypted-capture
  decryption, tamper refusal, plaintext-tree scanning, and audit-chain checks
  pass on Windows; and
- this is not provider approval: the observed evidence root inherits broad
  local ACLs, cross-profile/bare-machine recovery is absent, and Python cannot
  guarantee erasure of every interpreter or OS-level temporary copy.

Still required before any network posture:

- operator approval of the candidate OS secret-provider binding, hardened
  application-data ACLs, and an independent profile/system backup and recovery
  procedure for the external root KEK; the repository does not persist it;
- isolated unprivileged Ubuntu worker image, OS egress constraints, broker
  transport/authentication, conformance acceptance, owned canary, one reviewed
  programme, sustained clean operation, and explicit operator posture approval.

The foundation is therefore `PARTIAL`; `PASSIVE_HTTP` remains unavailable.
