---
id: 2026-07-25T19-15-46Z--verification-fact-shell-2026-07-25T19-11-42Z--goal-b8
time: 2026-07-25T19:15:46Z
kind: verification-fact
refs: [2026-07-25T19-11-42Z--goal-b8]
passed: true
tags: [skill, verifier-shell]
---
shell verifier: `python3 -m unittest tools.sula_vector.tests.test_sula_vector && python3 tools/sula_vector/render.py . --view doctor`

```
[sula] doctor OK — 390 fragments, 0 problems
...............................................................................
----------------------------------------------------------------------
Ran 79 tests in 4.705s

OK
```
