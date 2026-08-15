---
id: 2026-08-15T04-43-20Z--decision-migrate
time: 2026-08-15T04:43:20Z
kind: decision
refs: [2026-08-15T04-42-58Z--correction-migrate, 2026-08-15T02-48-04Z--annotation-11]
tags: [migrate, b8, rollout, authorship]
summary: 结清历史捕获需要显式授权，不随更新自动发生
---
接入 v1.2 后每个项目的 doctor 会因为「旧规则下从未被显式认领的捕获」变成 exit 1。舰队有 6+ 个项目，逐个手写结清片段不现实，所以 migrate.py 提供 --settle-legacy-captures。

关键选择是**它不能默认发生**。那条片段是 annotation，落在 judgment 一格，声明「这批债务不可收回」。让工具在每次更新时自动追加，等于机器替人做判断——与本项目拒绝擅自 activate Kiro CLI agent 是同一条界线：替别人的项目写下一条判断，不是可以代做的事。

所以：默认只报告并打印那条命令；加 flag 才追加。片段里工具只陈述它能核实的东西——多少条捕获、其中多少条正文带 commit subject、多少条什么都没有——并写 author: migrate.py，让来源可辨。它明确说「claims the debt as uncollectible, not as answered」，不编造任何理由。

给知情者留了第二条路：自己用 note.py --explains 写claim。工具那条只是给「已经无人知道」的情况一个诚实的出口。
