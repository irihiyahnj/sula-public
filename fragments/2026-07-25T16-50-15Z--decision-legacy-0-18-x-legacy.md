---
id: 2026-07-25T16-50-15Z--decision-legacy-0-18-x-legacy
time: 2026-07-25T16:50:15Z
kind: decision
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1]
tags: [v1-1, legacy, archive]
summary: 把 legacy 0.18.x 全部移入 legacy/，仓库形状与论点一致
---
一个宣称 no kernel directory / no cache-as-truth 的项目，根目录却摆着 scripts/sula.py（928KB）、.sula/、STATUS.md、docs/change-records/，说服力打折，也让新会话在读到 AGENTS.md 之前先撞上错误的操作模型（E1/E2/B4 原地保留）。

用 git mv（保留历史、可回滚）把全部 legacy 0.18.x 表面移入 legacy/：scripts/、.sula/、tests/、registry/、site/、templates/、examples/、schema/、STATUS.md、CHANGELOG.md、CHANGE-RECORDS.md、VERSION、Caddyfile、Dockerfile、PUBLIC-EXPORT.md，以及除 sula-vector-convention.md 外的所有 docs/。根目录现在只剩 vector：AGENTS.md + 宿主指针 + README + docs/convention + tools/ + fragments/ + legacy/。

legacy 测试从 legacy/tests 仍 132/132 通过；CI 的 legacy job 指向 legacy/tests。migrate.py 操作的是其它项目的根，未受影响。
