---
name: Bug report
about: Something behaves differently from what is documented
title: ''
labels: bug
---

<!--
STOP if this is a security issue in GreyTheory itself — especially a gate
bypass, a fail-open path, audit tampering, provenance laundering, or scope
inheritance. Do not open a public issue. See SECURITY.md.

Do not paste evidence, live target names, or programme-confidential material.
Use the .test fixtures for examples.
-->

**What happened**

**What should have happened**
Quote the doc or docstring that says so, if there is one.

**Reproduction**
Minimal case, ideally a failing test.

```python
```

**Environment**
- GreyTheory version:
- Python version:
- OS:

**Severity check**
- [ ] This produces an ALLOW where a DENY was correct
- [ ] This loses or corrupts audit or evidence data
- [ ] Neither of the above

If either of the first two is ticked, consider whether this belongs in SECURITY.md instead.
