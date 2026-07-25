---
id: 2026-07-25T19-35-04Z--decision-migrate-total-total-written
time: 2026-07-25T19:35:04Z
kind: decision
tags: [migrate, honesty, defect]
summary: migrate 的 total 标签把工具文件算成片段，已改为 total written
---
migrate.py 打印 'total fragments : 18'，而它实际写入 0 个片段——那 18 是 13 个工具文件加 5 个宿主指针的和。刷新 cn6 时我差点把 cn6 自己 6 月的未跟踪片段当成 migrate 的产出，靠比对 mtime（最近 5 分钟内 0 个文件被改）才排除。

一个以「不说谎」为核心价值的工具，其汇总行不能把类别不同的东西加在一起再贴上其中一类的名字。改为 'total written'，一个词，不加新逻辑。
