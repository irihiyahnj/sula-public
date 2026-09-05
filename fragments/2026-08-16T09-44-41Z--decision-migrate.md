---
id: 2026-08-16T09-44-41Z--decision-migrate
time: 2026-08-16T09:44:41Z
kind: decision
refs: [2026-08-16T09-32-53Z--intent-sula-vector]
tags: [migrate, host-pointers, review-fixes]
summary: 宿主指针更新不再覆盖自定义内容
---
migrate.py 的 install_host_pointers 此前只要目标文件与模板不同就整体重写，会把项目写在 CLAUDE.md / CODEX.md / GEMINI.md / Cursor / Copilot 指针里的自有规则静默删掉。这与 AGENTS.md 更新器对非工具编写区域“留下并报告”的边界不一致。
现在：已存在且非空的指针文件若与模板不同，跳过并计数上报，不覆盖；空文件仍视为缺失并写入模板。README 更新说明这一行为。新增测试验证自定义 CLAUDE.md 被保留、空文件被填充、幂等返回 (0,0)。
