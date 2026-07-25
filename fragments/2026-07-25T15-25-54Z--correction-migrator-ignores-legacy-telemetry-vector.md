---
id: 2026-07-25T15-25-54Z--correction-migrator-ignores-legacy-telemetry-vector
time: 2026-07-25T15:25:54Z
kind: correction
refs: [2026-06-14T14-00-00Z--correction-clean-worktree-must-also-exclude-events-indexes-jobs]
tags: [integrity]
summary: 确认 migrator-ignores-legacy-telemetry 决定从未迁入 vector
broken_ref: 2026-06-06T07-46-12Z--decision-migrator-ignores-legacy-telemetry-to-end-check-self-invalidation
correct_ref: none
---
同上：legacy change-record 未迁入。登记为已确认缺失，而不是留一个永久悬空的引用。
