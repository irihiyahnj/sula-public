---
id: 2026-07-25T15-24-56Z--decision-judgment-evidence-direction
time: 2026-07-25T15:24:56Z
kind: decision
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1]
tags: [v1-1, render]
summary: 三格投影：judgment / evidence / direction
---
kind 保持自由字符串（B3/E4 不变），但渲染时投影到三格：judgment 是为什么（方向），evidence 是发生了什么（位置），direction 是往哪去（去向）。--for-agent 的四段模糊投影因此变成三段，boot 上下文与 C6 的矢量隐喻对齐。

配套两个显式字段让 append-only 图可解析：supersedes（被取代的 judgment 从 boot 隐去，痕迹留在 --view effective）、closes（任何 kind 都能关闭一条 direction）。supersedes 只认显式声明，refs 永不隐含取代。
