---
id: 2026-07-25T18-58-01Z--assessment-v1-1-open-edges
time: 2026-07-25T18:58:01Z
kind: assessment
refs: [2026-07-25T15-37-50Z--snapshot-sula-vector-v1-1-boot-legacy, 2026-07-25T16-50-15Z--decision-legacy-0-18-x-legacy, 2026-07-25T18-57-37Z--operation-v1-1-0-tag-main-origin]
tags: [v1-1, handoff, audit]
summary: v1.1 交接快照的 open edges 已全部解决；判断一侧仍无机械捕获
---
接手核对：交接快照 2026-07-25T15-37-50Z 列的 open edges 现已逐条解决，快照本身当时为真、无需更正，只是没有任何片段指认它们已落地，读者必须从 witness 的 delta 里反推。逐条状态：

- legacy 0.18.x 归档：已由 decision 2026-07-25T16-50-15Z 落地。根目录现只剩 5 个宿主入口 + docs/ fragments/ tools/ legacy/ 与治理文件，快照所说「仍坐在仓库根目录」不再成立。
- VERSION 文件：不再在根目录，随归档移入 legacy/VERSION（内容仍为 0.18.15）。作为 legacy 制品，那是它的正确位置，不是残留。
- 「Nothing has been committed」：已全部提交、推送并打 tag，见 refs 中的 operation 片段。
- 非 git substrate 只有文件级 witness、无 sha：确认为设计上的保真度分层，不是缺陷。

同时核对当前健康度（本轮独立跑过）：66/66 tests OK；doctor exit 0，379 片段 0 问题；witness 手动运行输出 no change，即无未捕获的文件级证据。

残留的结构性缺口，明确记下以免被误当已解决：证据一侧（文件、commit）已机械化，git post-commit 与 Kiro agentStop 两个触发器均已安装并验证存在；判断一侧没有、也无法有机械捕获，仍依赖每个 agent 主动调 note.py。tag、push、以及只含 fragments/ 的 commit 同样在 witness 视野之外。因此 E8（判断只留在对话里）仍是这套系统唯一靠自觉守的边界。
