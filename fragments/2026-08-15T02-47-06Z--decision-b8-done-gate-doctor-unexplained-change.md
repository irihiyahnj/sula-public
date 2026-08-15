---
id: 2026-08-15T02-47-06Z--decision-b8-done-gate-doctor-unexplained-change
time: 2026-08-15T02:47:06Z
kind: decision
refs: [2026-08-15T02-46-41Z--correction-b8, 2026-05-23T05-50-10Z--decision-trust-is-reader-side]
tags: [b8, e8, doctor, d5]
supersedes: [2026-07-25T19-15-35Z--decision-b8]
summary: B8 缺席接入 done-gate：doctor 计入 unexplained-change
governs: tools/sula_vector/render.py
---
推翻 decision-b8「遗漏用永久可见执行，不用拒绝执行」。操作者本轮明确授权全部实施。

原论据：缺一个判断不是结构畸形；强制追加会把琐碎改动也逼出一个片段，即用 C7 买 E8。这个论据在窗口制下成立——那时缺口集合是猜的，冤枉一次就是白追加一次。

前提已经变了。配对成为显式事实之后：
- 缺口集合精确，不再有猜错的可能
- 存在单动作出口：--explains 可以声明「纯机械变更，无判断可记」——这本身是一条判断，不是 churn
- 于是 doctor 计入 unexplained-change 不再用 C7 买 E8，两者同时成立

放置位置的理由：doctor 已经在报 goal-without-verifier，那也不是畸形文件而是 B9 违反。B8 与 B9 同为 Tier B 不变量，同为只有作者能供给的东西，应当落在同一道门上。

拒绝的对象也要说准：doctor 不拦执行，它拦「宣称完成」（D5）。改了文件而没留下为什么的一轮，本来就没做完。

一次性代价：11 条历史 witness 从未被显式认领，接入后 doctor 从 0 problems 变成 11。单独一条片段结清，见同轮的 annotation。
