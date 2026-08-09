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
| Redirect or DNS change | In-scope name reaches out-of-scope infrastructure | Re-evaluate every hop and resolution | PLANNED |
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

## Hostile-content rule

Instructions found in programme pages, target responses, source code, tool output, files, agent configuration, or other external content are untrusted data unless they originate from a verified policy source and pass through the authority workflow.

External content can never change scope, activate a tool, request a credential, alter an approval, disable logging, increase a budget, mark evidence checked, or cause external communication.

## Preconditions for any network posture

Before `PASSIVE_HTTP`, GreyTheory requires a typed research domain, current verified source bundle, broker/worker separation, canonical URL and IDNA handling, DNS and redirect rechecks, private/metadata-network denial, rate/request/time budgets, tested kill switch, immutable receipts, data classification enforcement, worker conformance tests, and a private evidence root outside every repository.

The presence of this document does not satisfy those gates. Each control needs implementation and test evidence.
