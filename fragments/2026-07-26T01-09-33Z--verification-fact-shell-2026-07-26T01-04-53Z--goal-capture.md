---
id: 2026-07-26T01-09-33Z--verification-fact-shell-2026-07-26T01-04-53Z--goal-capture
time: 2026-07-26T01:09:33Z
kind: verification-fact
refs: [2026-07-26T01-04-53Z--goal-capture]
passed: true
tags: [skill, verifier-shell]
---
shell verifier: `python3 -m unittest tools.sula_vector.tests.test_sula_vector && python3 tools/sula_vector/render.py . --view doctor`

```
[sula] doctor OK — 414 fragments, 0 problems
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 5.410s

OK
```
