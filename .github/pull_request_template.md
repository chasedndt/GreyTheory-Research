<!--
Do not include evidence, live target names, or programme-confidential material.
-->

**What this changes**

**Why**

---

**Checks**

- [ ] `python -m pytest -q` passes
- [ ] New behaviour has tests; denial paths are covered as well as allow paths
- [ ] No new runtime dependency in `greytheory/`
- [ ] No network import in `greytheory/`
- [ ] Anything time-dependent takes an injected clock

**If this touches the Authority Plane**

- [ ] No new path where absence, ambiguity, staleness or an exception could result in permission
- [ ] Every new artifact carries an authority reference
- [ ] Every new gate outcome is audited before it returns
- [ ] No new way for the system to assert a programme outcome it was not told

**If this touches evidence**

- [ ] Raw evidence still cannot leave the vault
- [ ] Export remains all-or-nothing
- [ ] The repository guard is intact

**Docs**

- [ ] Capability register in `Docs/definition.md` updated if a component changed status
- [ ] `CHANGELOG.md` updated
- [ ] Diagrams updated if a flow changed
