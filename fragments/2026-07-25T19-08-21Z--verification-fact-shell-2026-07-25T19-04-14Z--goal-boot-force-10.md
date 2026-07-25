---
id: 2026-07-25T19-08-21Z--verification-fact-shell-2026-07-25T19-04-14Z--goal-boot-force-10
time: 2026-07-25T19:08:21Z
kind: verification-fact
refs: [2026-07-25T19-04-14Z--goal-boot-force-10]
passed: true
tags: [skill, verifier-shell]
---
shell verifier: `python3 -m unittest tools.sula_vector.tests.test_sula_vector && python3 tools/sula_vector/render.py . --view doctor`

```
[sula] doctor OK — 384 fragments, 0 problems
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 4.161s

OK
```
