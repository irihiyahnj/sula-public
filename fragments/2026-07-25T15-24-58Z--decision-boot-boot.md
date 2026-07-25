---
id: 2026-07-25T15-24-58Z--decision-boot-boot
time: 2026-07-25T15:24:58Z
kind: decision
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1]
tags: [v1-1, boot]
supersedes: [2026-05-23T09-03-40Z--decision-update-check-at-boot-not-cron]
summary: boot 回到两步：更新不再发生在 boot
---
boot 曾是四步，其中第二步在模型读到任何上下文之前联网改动自身工具。B6 说多出来的都是泄漏。

改为：boot 只有两步（记 session_start、跑 render --for-agent），离线且确定。工具更新降级为显式的操作者动作（migrate.py 或 update-from-canonical.sh），项目自己决定何时更新。
