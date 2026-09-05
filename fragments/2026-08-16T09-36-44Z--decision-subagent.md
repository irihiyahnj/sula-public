---
id: 2026-08-16T09-36-44Z--decision-subagent
time: 2026-08-16T09:36:44Z
kind: decision
refs: [2026-08-16T09-32-53Z--intent-sula-vector, 2026-08-16T09-33-07Z--turn-dispatch-2026-08-16T09-32-53Z--intent-sula-vector]
tags: [subagent, fallback, review-fixes]
summary: 子代理调度失败，主代理直接执行修复
---
通过 skills/llm-dispatcher.py 派出的 codex 子代理不可用：executor 返回 ERR，
错误为 `failed to initialize in-process app-server client: Operation not permitted (os error 1)`。
本机 claude 无可用 API 连接（SSL hostname mismatch），kiro-cli 要求浏览器登录。
因此不继续在 executor 上消耗：同一 intent 里的修复任务改由主代理直接执行，
验收标准不变（P1-1..P1-4 回归测试、doctor 0 problems、witness 配对、changes-summary）。
