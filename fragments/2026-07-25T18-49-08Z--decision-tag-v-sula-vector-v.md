---
id: 2026-07-25T18-49-08Z--decision-tag-v-sula-vector-v
time: 2026-07-25T18:49:08Z
kind: decision
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1]
tags: [v1-1, release, versioning]
summary: 版本 tag 统一为单一 v* 主线，sula-vector-v* 前缀停用
---
历史上有两套 tag 命名并存：legacy 用 v0.12.0~v0.18.15，早期 vector 用 sula-vector-v1.0.0~v1.0.4。两套命名让当前版本是什么需要先知道属于哪条线。

决定：只保留单一 v* 主线。v1.1.0 起所有发布用 v<major>.<minor>.<patch>，legacy 那条线在 v0.18.15 终止，sula-vector-v* 前缀停用（旧 tag 保留不删，append-only 的同种精神——历史不擦除）。

不补 sula-vector-v1.1.0 别名：别名会把刚消除的歧义重新引入。
