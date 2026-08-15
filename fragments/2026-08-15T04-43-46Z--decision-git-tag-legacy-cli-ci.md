---
id: 2026-08-15T04-43-46Z--decision-git-tag-legacy-cli-ci
time: 2026-08-15T04:43:46Z
kind: decision
refs: [2026-07-25T16-50-15Z--decision-legacy-0-18-x-legacy, 2026-05-23T05-07-39Z--decision-migrated-to-sula-vector]
tags: [ci, legacy, rollback, d5]
summary: 回滚改为基于 git tag，legacy CLI 测试从 CI 移除
governs: legacy/tests
---
实测数据：legacy/tests 单个用例约 55 秒（第一条 59.2s，第二条 113.5s 累计），6111 行测试上百个用例，全套一小时以上。它 fork 那个 945KB 的 CLI 并为每个用例新建 git 仓库。不是挂死，是量级不对。

一道跑不完的检查提供的保证是零。它在 GitHub 默认限制下要么超时要么长期红着，而长期红的 CI 会训练所有人忽略 CI——这比没有检查更糟。

核实过删除的影响面：tools/sula_vector/ 不 import legacy 的任何东西；migrate.py 读 legacy 的**数据**（docs/change-records/、.sula/*.json、STATUS.md）靠解析文件，从不执行 legacy 代码，且该能力由 TestMigrateIdempotence 用合成目录覆盖；install_tooling 从不拷贝 legacy/。所以对任何会交付出去的功能是零影响。

真正失去的是「归档的 0.18.x CLI 还跑得起来」这个自动证据，它只服务回滚。所以把回滚承诺改成书面实情：**回滚基于 git tag（git checkout <tag>），不再由代码测试背书。** 迁移时保留的 .sula/、STATUS.md、docs/change-records/ 数据不受影响，只是读它们的那段代码不再有测试。

这条不是「删掉一个碍事的检查」，是把一个隐性损失变成显性的：不写下来，这个保证就会在一次 commit message 里消失。governs 指向 legacy/tests，将来那个目录若被移除，这条判断会自己浮出来要求复核。

同轮补上一道真检查：CI 增加 example 向量的 doctor，它此前从不被验证。
