---
id: 2026-08-15T04-42-58Z--correction-migrate
time: 2026-08-15T04:42:58Z
kind: correction
refs: [2026-05-23T06-22-58Z--correction-agents-md-legacy-vs-vector-ambiguity, 2026-05-23T06-22-58Z--decision-update-mechanism-is-migrate-py]
tags: [migrate, fleet, rollout]
explains: [2026-08-15T04-33-26Z--witness]
summary: 更新路径本身先坏了：migrate 三个缺陷会把旧协议推给整个舰队
governs: tools/sula_vector/migrate.py
---
准备舰队 rollout 时在临时项目上排练，发现 migrate.py 交付不了这次发布。三个缺陷同一个根因：**更新路径只报告它拷了什么，不保证结果可用。**

一、协议永不刷新。已带 sula-vector 哨兵的项目走到 already-vector 分支就原样返回。后果是每个舰队项目都会保留 v1.1 协议文本——包括本轮已被证伪的「omission is inherited, not forgotten」——却在跑 v1.2 的工具。agent 读到的指令与它执行的工具不一致，正是 correction-agents-md-legacy-vs-vector-ambiguity 记录过的那次 B6 违反。改为从哨兵到文件尾整段从 canonical 重写；哨兵以上项目自己写的内容不动；那一段若不像本工具写的协议（缺 PROTOCOL_HEADING）则不覆盖并如实报告 protocol-foreign-left-alone——静默删掉项目自己的文字是更坏的失败。

二、两份工具文件清单漂移。auto-update-from-canonical.py 用自己那份清单算聚合哈希，而那份已经丢了 note.py 与 skills/witness.py。后果是只改这两个文件的发布会对每个项目报「已是最新」。清单收敛到 migrate.py 一处，技能改为 import。这是退休整类缺陷而不是修这一个实例。

三、只报拷贝数，不报可用性。migrate 现在打印 doctor 摘要——这件事重要，因为舰队里有项目带着 v1.0 时代手写片段的 785 个既有问题，门在那里本来就是关着的，操作者必须一眼看到。

六个新测试盯住这三处，其中 test_stale_protocol_is_refreshed 与 test_installed_tooling_matches_the_updater_hash_list 是缺陷本身的复现。
