---
id: 2026-08-15T06-09-08Z--decision-fleet
time: 2026-08-15T06:09:08Z
kind: decision
refs: [2026-07-25T22-46-45Z--correction-fleet]
tags: [fleet, container, adoption, removal]
summary: 医院容器层向量已移除：容器不是项目根
---
操作者裁定：按年份/院名分的容器目录本身不该被跟踪。这补上了 correction-fleet 当时挂起的那个决定——那条片段记的是「误建的容器级向量，未删（删除需你确认）」。

移除的是容器层的 Sula 存在，不是任何项目真相。该层自己的两条 annotation 就写着「本层不承载任何项目真相，不要在这里追加判断」，并指向真正的项目向量。10 个片段的构成是 5 条原则副本 + 1 条自动迁移决定 + 基线见证 + 1 次见证 + 那两条自陈误建的 annotation，没有任何独有判断——容器是误建这个发现本身已经记在 canonical 的 correction-fleet 里。

该层不是 git 仓库，直接删除不可恢复，所以先打包再删：全部 71 个条目（fragments/、tools/、AGENTS.md、CLAUDE.md、CODEX.md、GEMINI.md、.kiro/、.cursor/、.github/）归档为该目录下的 .sula-vector-removed-2026-08-15.tgz，136K，随时可还原。归档为单个 tgz 而非子目录，是为了它不会再被「同时含 fragments/ 与 tools/sula_vector/render.py」的发现规则命中。

未触碰：2026/ 下的两个真实项目（昆明同仁医院 1434 片段、昆明新根源 26 片段，各自自带工具，移除后复验完好）、容器层的三份客户文档、.codex。

判定标准重申一次，它已经错过两次：项目根是真相文件所在的那一层。容器目录（按年份、按客户、按类别分的目录）不是项目根，给它建向量会产生两棵树重叠的向量，证据重复且无人知道该读哪一个。
