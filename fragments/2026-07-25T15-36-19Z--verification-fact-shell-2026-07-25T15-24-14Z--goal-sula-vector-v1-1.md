---
id: 2026-07-25T15-36-19Z--verification-fact-shell-2026-07-25T15-24-14Z--goal-sula-vector-v1-1
time: 2026-07-25T15:36:19Z
kind: verification-fact
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1]
passed: true
tags: [skill, verifier-shell]
---
shell verifier: `python3 -m unittest tools.sula_vector.tests.test_sula_vector && python3 tools/sula_vector/render.py . --view doctor`

```
[sula] doctor OK — 372 fragments, 0 problems
.................................................................
----------------------------------------------------------------------
Ran 65 tests in 4.202s

OK
```
