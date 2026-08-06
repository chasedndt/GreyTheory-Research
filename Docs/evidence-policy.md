# Evidence Policy

Resolves open question **O3** — where evidence lives, and what may leave.

## The decision

Raw evidence lives **outside every repository working tree**, in a location resolved in this order:

| # | Source | Path |
|---|---|---|
| 1 | Explicit `root` argument | as given |
| 2 | `GREYTHEORY_EVIDENCE_ROOT` | as given |
| 3 | `CHASEOS_VAULT_ROOT` | `<vault>/07_LOGS/greytheory-evidence/` |
| 4 | Platform user-data directory (default) | `%LOCALAPPDATA%\GreyTheory\evidence` on Windows; `$XDG_DATA_HOME/greytheory/evidence` or `~/.local/share/greytheory/evidence` elsewhere |

**Step 4 is the standalone default and it is deliberate.** GreyTheory is Apache-2.0 and must work fully for someone who has never heard of ChaseOS. Step 3 exists so a ChaseOS operator ends up with one vault instead of two — an integration, not a requirement.

### The repository guard

`EvidenceVault` **refuses to initialise inside a git working tree.** It walks up from the resolved root looking for `.git` and raises `VaultLocationError` if it finds one.

A `.gitignore` entry is a convention that a `git add -f`, a misconfigured tool, or a tired evening can defeat. Raw evidence committed and pushed is unrecoverable — it lives in the reflog, in forks, in caches. So this is a wall rather than a convention. `allow_in_repository=True` exists for throwaway test trees and nothing else.

## Structure

```
<evidence_root>/
├── raw/<finding_id>/<artifact_id>.<ext>        # private, written once, never modified
├── redacted/<finding_id>/<artifact_id>.<ext>   # the only thing that may be shared
└── manifests/<finding_id>.json                 # hashes, authority refs, metadata
```

Every artifact has a SHA-256 recorded at write time for both copies. `verify()` rehashes from disk and reports modification or deletion.

## Rules the vault enforces

| Rule | Why | Enforcement |
|---|---|---|
| Evidence requires an authority reference | Invariant I2. Evidence produced under no authority proves nothing about whether it should exist. | `store_raw` raises without one |
| Raw is written once | Overwriting silently destroys the original. There is no legitimate reason to rewrite a capture. | Duplicate artifact id raises |
| Sensitive until proven otherwise | `contains_sensitive_data` defaults to `True` and only a deliberate redaction clears it. | Default on the dataclass |
| A redacted copy must differ from the raw | Copying raw bytes into the redacted slot is the single most likely mistake, and it silently defeats the whole split. | Identical hash raises |
| Only redacted artifacts export | Raw never leaves. | `export_package` reads redacted paths only |
| All-or-nothing export | Partial export is how raw evidence escapes — an operator fills the gap by hand from the wrong directory. | Any unredacted artifact aborts the whole export |
| Integrity is checked at export | Exporting evidence that no longer matches its hash would put an unverifiable artifact in a report. | `export_package` runs `verify()` first |
| Identifiers are validated, not trusted | Ids become path segments. | Regex allowlist; `../` rejected |

## What the vault does *not* do

**It does not redact.** Only the operator knows which bytes are sensitive, and a regex that thinks it does is worse than nothing — it produces confident, incomplete redaction. What the vault enforces is that the act happened and that the result actually differs from the original.

**It does not decide retention.** See below.

## Retention

| Class | Retention |
|---|---|
| Raw evidence | Minimum necessary. Deleted once the finding closes — disclosed, or private-closed. |
| Redacted evidence | Retained while the finding is open; retained after disclosure if the finding is public. |
| Manifests | Retained indefinitely. They are hashes and metadata, not content, and they are what proves the evidence existed and was intact. |
| Third-party data | Never retained. This is a stop condition during testing, not a retention rule afterwards. |

If sensitive third-party data is captured accidentally, the sequence is: stop, record exactly what was accessed, notify the programme promptly, delete the raw capture, keep the manifest entry noting the deletion.

## Relationship to the audit log

Two different questions, deliberately separate:

- The **audit log** records *what was authorised and what happened*. Append-only, hash-chained, retained indefinitely.
- The **evidence vault** holds *what was captured*. Content-addressed, raw deleted on close.

Evidence writes are recorded in the audit log with their authority reference, so the log still shows an artifact existed even after the raw bytes are gone.
