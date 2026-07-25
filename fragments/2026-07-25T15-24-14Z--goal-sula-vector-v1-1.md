---
id: 2026-07-25T15-24-14Z--goal-sula-vector-v1-1
time: 2026-07-25T15:24:14Z
kind: goal
refs: [2026-07-25T11-00-12Z--assessment-vector-audit-capture-fidelity-and-reader-resolution]
tags: [v1-1, convergence]
summary: 落地 Sula Vector v1.1：捕获成为不变量，错误不可表达
done_when: vector test suite passes; render --view doctor exits 0; note.py + witness.py + hooks/install.py exist and are covered by tests; five host entrypoints point at AGENTS.md; convention documents v1.1
verifier_ref: shell: python3 -m unittest tools.sula_vector.tests.test_sula_vector && python3 tools/sula_vector/render.py . --view doctor
---
把审计里的两个约束（捕获保真度、读取端解析）在正确的层解决，而不是继续在提示词层打补丁。

范围：运行时捕获（witness + hooks/install）、派生身份与 loud 解析、三格投影（judgment / evidence / direction）、supersedes 与 closes、doctor 视图、五个宿主入口收敛、convention v1.1。
