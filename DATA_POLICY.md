# GreyTheory Data Policy

> **Status:** CANONICAL policy; implementation is PARTIAL.
>
> **Effective:** 2026-08-09

## Data classes

| Class | Examples | Default model policy |
|---|---|---|
| `PUBLIC` | Published programme rules and public advisories | Remote processing allowed when configured |
| `PROGRAMME_SENSITIVE` | Private programme notes or scope | Explicit provider/deployment policy required |
| `TARGET_SENSITIVE` | Redacted responses and architecture | Local or explicitly approved provider preferred |
| `RAW_RESTRICTED` | Tokens, personal data, raw captures | Never sent remotely by default |

Model inputs must use credential handles, identity handles, hashes, and redacted summaries wherever possible.

## Storage

- Integrity-digested JSON snapshots are the current store for structured research workspaces and sessions; SQLite remains the planned index once object contracts and query patterns stabilise.
- Content-addressed files remain the store for evidence, programme source snapshots, report versions, and tool outputs.
- The append-only audit chain records authority-relevant events.
- Raw evidence and research workspace data must remain outside every Git working tree; both stores refuse repository paths by default.
- Passive capture ciphertext remains `RAW_RESTRICTED`: encryption does not
  reclassify it. The offline key store refuses Git paths, persists only
  authenticated KEK-wrapped X25519 private keys, and never persists its
  caller-supplied root KEK.
- Only redacted evidence is exportable, and export remains all-or-nothing.

## Evidence deletion

Write-once protects integrity but must not force retention of accidentally captured third-party data. A future controlled deletion path must remove the sensitive bytes and append an immutable tombstone containing the former hash, reason, operator, time, and programme-notification reference when applicable.

Until that path exists, capture must stop immediately when third-party data appears and the operator must follow the programme's handling instructions. No automated workflow may copy or retain additional data to strengthen a proof.

## Retention and external processing

Retention is per programme and workspace policy. Remote model use is never implied by model availability. Provider, model/version, prompt template, data classes, token/cost totals, output hashes, and inference provenance must be recorded by the future model gateway.
