# Agent Activity Log

A record of what each agent session did, **why it deviated from the roadmap where it did**, and what the next agent should not undo.

Read this before changing anything that looks arbitrary. Several guards in this codebase are deliberately stricter than they need to be, and the reasoning is here rather than in the code.

---

## 2026-08-09 — Claude · Claim roles and submission-time scope recheck

### What was built

- `greytheory/claims.py` — seven claim roles, `RoleBinding`, the claim-evidence matrix.
- `greytheory/validators.py` — four reusable validators settling the checked roles from artifacts already held.
- `greytheory/findings.py` — `report_ready` now requires role coverage; `submitted` now requires a `ScopeRecheck`.
- `greytheory/vertical_slice.py` — binds all seven roles with no additional fixture interaction.
- `tests/test_claim_roles.py` — 29 tests. Suite: 447 → 476.

Full reasoning in [ADR-0008](decisions/ADR-0008-claim-roles-and-submission-scope-recheck.md).

### Why this instead of Milestone 7

**The roadmap said Milestone 7 was the model gateway. I did not build that.** This is a deliberate deviation and the operator approved it.

The reasoning:

1. **Two open holes were cheaper to close than the next milestone was to open.** The productisation review identified both in §20. Neither was addressed by Milestones 1–6, and both are in the trust kernel — the part everything else assumes is correct.

2. **The `report_ready` guard was the weaker of the two and the more embarrassing.** Milestone 4 had already proved a finding could reach report-ready. It reached it on one checked claim. Building a model gateway on top of a guard that weak would have meant adding AI capability above a foundation that could not distinguish a proven vulnerability from a proven HTTP 200.

3. **The model gateway gates nothing.** It can be built offline at any time and nothing waits on it. The two guards, by contrast, are load-bearing for every finding that will ever pass through the system.

### The other roadmap change I would make, and did not

**Milestone 7 (model gateway) and Milestone 8 (Scope Watch) should swap.**

Scope Watch is the *safer* first network component — it fetches public policy pages, not targets — and it exercises the network worker, the execution broker and change detection under the lowest available operational risk. The review itself argues this in Milestone 8 ("why first: it touches public policy sources rather than targets") and then places it second anyway.

I have not made this change because reordering the roadmap is the operator's call, not an agent's. It is recorded here so the next session does not have to rediscover it.

### What the next agent should not undo

**Do not relax the seven-role guard back to a count.** A count of checked claims can be satisfied by proving almost nothing, and that is what it was before. If the guard is inconvenient, the finding is probably not ready.

**Do not make `impact` a checked role.** Whether a proven behaviour matters is a judgement about the product, its users and the programme's view. A validator adjudicating it would manufacture exactly the false certainty this project exists to prevent.

**Do not make `reproduction` a checked role either** — this is the one that looks wrong and is not. It is checkable in principle, but only by acting on the target twice. Requiring a receipt would push every finding in the system into doubling its interaction, against invariant I4. Gate B in `validation.py` already treats reproducibility as attested-plus-evidence; the two mechanisms must agree.

**Do not downgrade the scope recheck to a warning.** A warning at submission time is read by someone who has already decided to submit.

**Do not let the role validators perform any interaction.** They settle their questions from bytes already stored. That constraint is what keeps the stricter guard compatible with minimum-impact proof. A validator that fetches something has broken the design.

**Do not treat an empty evidence manifest as verified.** `EvidenceIntegrityValidator` returns `invalid_input` on an empty set on purpose. "Nothing to check" is not "everything verified" — the same rule the dashboard follows for absent data.

### Still open from the review

Verified absent from the codebase (grepped, zero hits) as of this session:

| Gap | Note |
|---|---|
| `ApprovalProvider` protocol | **ADR-0003 exists; the code does not.** The clearest next piece of trust-kernel work. |
| Signed audit checkpoints | The hash chain detects alteration from a known start, but a writer with full access can rewrite and recompute the whole chain. Needs an operator key, therefore a dependency outside the core. |
| Evidence tombstones | Write-once raw evidence conflicts with the duty to delete accidentally captured third-party data. Needs hard deletion plus an immutable record that something was deleted and why. |
| Taint labels for target content | Target-controlled text can attempt to influence the model. Not yet formally distinguished from operator content. |
| Plugin conformance suite | No adapter is tested against denial, rate and scope fixtures. |
| Model gateway | Milestone 7 as written. |

### Verification

```
447 tests before this session's changes, all passing
476 tests after
no network import in greytheory/ (CI-enforced)
```

The twelve failures encountered mid-change were all callers satisfying the old weak guard, including the Milestone 4 vertical slice. Each was updated rather than exempted.

---

## Template for future entries

```markdown
## YYYY-MM-DD — <agent> · <one-line summary>

### What was built
### Why this instead of what the roadmap said
### What the next agent should not undo
### Still open
### Verification
```
