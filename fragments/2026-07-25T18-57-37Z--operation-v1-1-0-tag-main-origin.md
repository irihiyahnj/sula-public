---
id: 2026-07-25T18-57-37Z--operation-v1-1-0-tag-main-origin
time: 2026-07-25T18:57:37Z
kind: operation
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1, 2026-07-25T18-49-08Z--decision-tag-v-sula-vector-v]
tags: [v1-1, release]
summary: v1.1.0 已打 tag 并推送，main 与 origin 同步
commit: 7c4eb2575adc0293806287e346be5fe01c906c6e
---
v1.1 的发布事实：tag v1.1.0 指向 7c4eb2575adc0293806287e346be5fe01c906c6e；main 与 origin/main 完全同步（rev-list --left-right --count 为 0 0）。构成这次发布的 4 个 commit：f047aea（v1.1 主体）、bf7c708（让 witness 忽略只含片段的 commit，掐断 post-commit 自循环）、7c4eb25（补捕上一条）、247a627（tag 命名决定）。

为什么这条由手写而非 witness 捕获：witness 的视野里没有 tag，且按 bf7c708 的设计忽略只含 fragments/ 的 commit。tag 与 push 结构上落在机械捕获之外，因此需要判断者显式记账，否则发布这件事在向量里不存在。
