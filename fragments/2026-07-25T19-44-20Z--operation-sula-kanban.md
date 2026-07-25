---
id: 2026-07-25T19-44-20Z--operation-sula-kanban
time: 2026-07-25T19:44:20Z
kind: operation
refs: [2026-07-25T19-35-03Z--operation-v1-1-2-cn6-v1-0-v1-1-2]
tags: [fleet, adoption]
summary: 四个项目接入 Sula：kanban、钱王炽、医院、三月四月五月
---
本设备舰队从 1 个项目扩到 5 个。四个新接入项目均非 git 仓库（iCloud 文件夹底座）：

- kanban（projectdev/kanban，149 文件，订阅制看板 SaaS）：原有 67 行 AGENTS.md 被保留，Sula 协议以 sentinel 追加至 206 行。基线 111 文件。注意：接入期间 web/src/design/components.css 与 web/test/lists.test.tsx 在实时变动，witness 每轮都会捕获——那是真实变更，不是噪音。
- 钱王炽（Project/钱王炽，2363 文件，云南双茶联名合作提案）：基线 2377 文件。它原有 _READ_FIRST_项目交接.md 与项目现状基线文档，那正是 Sula 要替代的东西。
- 医院（Project/医院，2673 文件）：基线 1418 文件。
- 三月四月五月（Project/三月四月五月，681 文件，双语视觉播客）：基线 695 文件。

每个项目均：v1.1.2 工具、5 条 Tier A–E 原则、AGENTS.md + 5 个宿主指针、Kiro agentStop 钩子、witness 基线已建。四个 doctor 全部 exit 0。非 git 底座无 post-commit 钩子，install.py 打印了 30 分钟 cron 行，尚未安装——这台设备没有任何 cron，捕获目前依赖 Kiro 回合结束触发。

四个项目的 fragments/ 目前只有原则与基线，没有任何判断。接入给出的是容器与护栏，不是内容；把各自的交接文档与现状基线转成片段需要对内容做判断，未做。
