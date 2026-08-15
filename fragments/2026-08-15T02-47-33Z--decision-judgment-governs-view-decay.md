---
id: 2026-08-15T02-47-33Z--decision-judgment-governs-view-decay
time: 2026-08-15T02:47:33Z
kind: decision
refs: [2026-07-25T18-58-01Z--assessment-v1-1-open-edges, 2026-07-25T19-26-04Z--assessment-boot-96-force-60-v1-0-ga]
tags: [b9, judgment, decay, boot]
summary: judgment 补上机械终止信号：governs + view decay
governs: tools/sula_vector/render.py
---
三格里 judgment 是唯一两头都没有机械信号的一格：

  evidence   机械产生 witness    / 无需终止（证据只后退成过去）
  direction  人写               / 机械终止 verifier（B9 强制）
  judgment   人写               / 无

direction 有 B9 兜底：没有 verifier 的目标是愿望。judgment 没有对应物——一条判断可以永远在force而从不接触现实，唯一退休路径是有人手工记得去 supersede。boot 权重反转（103 条在force里 60 条讲的是已进 legacy/ 的系统）不是谁偷懒，是这个空格的必然结果，会在每个活得够久的向量上重演。

能补的一半是衰减信号，不是自动退休：判断用 governs 声明它治理的路径；witness 已经在机械地记录路径的出现与消失；当治理对象被见证移除且没有再出现时，boot 浮出「Judgments whose subject is gone」。机器不写任何为什么，只提出质疑——与 verifier 对 direction 做的事同构。

两条边界写进实现：
- 需要移除的正面证据。把「从未被见证」当作「已消失」会退休掉捕获历史覆盖不到的一切判断，正好是相反的失败。
- 不进 doctor。主体消失了，片段本身没有畸形，也不该拦住任何人宣称完成。

诚实的局限：过去的片段不可编辑（B1），60 条 legacy 判断永远不可能带上 governs。这个机制只对将来的判断有效，历史那批只能显式退休（同轮另一条片段）。
