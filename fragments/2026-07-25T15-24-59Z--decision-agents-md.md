---
id: 2026-07-25T15-24-59Z--decision-agents-md
time: 2026-07-25T15:24:59Z
kind: decision
refs: [2026-07-25T15-24-14Z--goal-sula-vector-v1-1]
tags: [v1-1, continuity]
summary: 五个宿主入口必须收敛到 AGENTS.md
---
CLAUDE.md、CODEX.md、GEMINI.md、.cursor/rules/project.mdc、.github/copilot-instructions.md 此前仍宣称 legacy 最高规则并把工作路由到 scripts/sula.py，与 Tier A 直接冲突——「切换成本 0」是声明而非属性。

改为：五个文件都退化成指向 AGENTS.md 的薄指针，并由 migrate.py 的 install_host_pointers 统一投影到每个采用项目，内容相等即幂等。顺带修掉 install_agents_template 的一个真 bug：priority notice 里字面引用了 sentinel，导致幂等检查误判、协议正文永不追加。
