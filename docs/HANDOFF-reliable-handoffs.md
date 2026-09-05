# Sula Vector 可靠交接优化：接手说明

用户要求由成本较低的模型继续执行，完成后交原模型复核。本文件是交接材料，项目判断仍以 fragments 渲染为准。

## 工作区

- 目录：`/Users/jing/dev/Project/projectdev/sula-vector`
- 当前分支：`codex/reliable-handoffs`
- 本轮未提交、未合并、未发布。请直接接续此工作区，不要新建一个不含当前修改的 checkout。
- 开始时已经有未提交的 README、CONTRIBUTING、SECURITY、PR 模板、migrate/note/render/test_sula_vector.py 修复，以及 2026-08-15/16 的未跟踪片段。它们已保留，不得当作本轮垃圾清除。
- 先记 UTC session_start，运行 `python3 tools/sula_vector/render.py . --for-agent`，遵守 AGENTS.md。片段只追加，使用 note.py。

## 已实施

1. `append.py`：所有内置写入器共用完整文件 staging + fsync + hard-link 原子不可覆盖发布。随机后缀避免重名，微秒时间区分同秒记录；不支持原语的文件系统明确失败。迁移保留固定旧 ID，但不覆盖已有片段。
2. `render.py`：约定 1.2 接受旧秒级和新微秒文件名；规范化排序。解释关系必须连接真实判断/方向和 witness；无效关系不能清除缺口。历史有效解释在判断被替代后仍保留意义。
3. 所有有状态视图先解析完整证据再筛选；`--until` 表示历史截点，`--since` 仅筛展示对象。修复 kind=goal 后完成状态反转。
4. `capture.py`：全尺寸流式 SHA-256，忽略目录提前剪枝；读失败或读中修改会失败。路径使用 JSON 转义，支持空白、引号和控制字符。移除旧的大于 50 MiB 只比大小逻辑。
5. 捕获新增父记录、分叉/缺祖先检测；同步完整后才可 `witness --reconcile` 写完整快照。没有执行远端同步。首轮新捕获会刷新旧短摘要，可能列出很多内容实际未变的路径。
6. `verifier-shell.py`：验证结果绑定输入内容摘要；默认全部捕获文件，`note --verify-path` 可重复指定范围。验证修改自身输入会失败；后续捕获变更使旧通过状态 stale；旧无绑定记录显示 unbound。并列矛盾结果不随机选一个通过。
7. `skills/finish.py`：capture → doctor → 再扫描确认本次观测期间无漂移。结构检查通过不等于任务验收通过。Kiro stop 模板改用 finish；git hook 仍捕获且不再吞掉失败提示。未安装或激活本机新 hook。
8. `--for-agent --focus`：完整 boot 后可按任务读取；保留原则、显式 scope=global 判断、开放方向和风险，展开选中理由。不会沿批量 witness.explained_by 把所有无关判断拉回来。
9. `review_after`/`review_when`：按记录时间/业务条件提示复核，不隐式退休判断。
10. 分发清单纳入 append/capture/finish 以及此前遗漏的 migrate.py，复制项目后更新器能独立启动。CI 改为发现全部测试，并加入交接场景脚本。

## 已完成的检查

- 最近一次：`python3 -m unittest discover -s tools/sula_vector/tests`，154/154 PASS。
- 三个受控交接场景全部通过；见 `docs/handoff-check-results.json`。
- 场景包括有效 Python 文件、文本文档、50 MiB+1 的媒体体量二进制；完整项目复制到另一临时目录后启动输出一致，更新工具可启动，同尺寸改动会使旧验证过期。
- 场景聚焦阅读字节减少约 79.9%–80.8%。这是构造样例的字节对照，不是 token 计量、真人时间收益、视频画质验收或真实跨设备同步验证。
- `git diff --check` 通过；交接记录追加前 doctor 为 450 fragments / 0 problems。
- 做过 py_compile；最后一次小修后仍需把编译检查纳入最终验收。

## 剩余工作：限定在收尾，不重写架构

1. **文档一致性**：`docs/sula-vector-convention.md` 顶部仍写 1.1，底部与实现已为 1.2，需统一。README 仍有 `ls` 保证时间排序的旧说法，新旧秒精度混合不能这样保证。README / convention / install.py 中部分 Kiro stop 描述仍写 witness，应与 finish 实现一致。
2. **历史数据标识**：README 433 fragments、113 tests、约 5200 行等旧表，应明确标为 v1.2.0 发布时快照，或链接当前自动测试/场景报告，避免当作本次实测。不要随意改写历史发布说明和历史片段。
3. **集中检查本轮 diff**：重点核对原子写入确实覆盖所有内置 fragment 写入器、迁移后模块可导入、筛选不丢解释/关闭关系、父捕获异常不隐式选分支、验证范围包含用户声明输入、聚焦视图不会隐藏全局风险。已有回归用例，不必从头重复审计或扩展新功能；发现具体错误再增加对应测试。
4. **验收**：执行下列命令；有失败先修复原因。场景报告若重生成有差异，记录真实结果。
5. **收尾记录**：判断用 note.py，文件变化由 witness/finish 捕获。若未解释捕获出现，显式 `--explains <witness-id>` 补为什么。输出本接手会话的完整 changes-summary 标记。
6. **交原模型复核**：完成后给出变更摘要、执行的验证及结果、已知限制和 git 状态。不合并、不发布、不更新其他采用项目。

```bash
python3 -m py_compile tools/sula_vector/*.py tools/sula_vector/skills/*.py tools/sula_vector/hooks/*.py tools/sula_vector/tests/*.py
python3 -m unittest discover -s tools/sula_vector/tests
python3 tools/sula_vector/tests/handoff_scenarios.py --output docs/handoff-check-results.json
python3 tools/sula_vector/render.py tools/sula_vector/example --view doctor
python3 tools/sula_vector/render.py . --for-agent > /tmp/sula-boot-a.txt
python3 tools/sula_vector/render.py . --for-agent > /tmp/sula-boot-b.txt
cmp /tmp/sula-boot-a.txt /tmp/sula-boot-b.txt
python3 tools/sula_vector/skills/finish.py --project-root .
git diff --check
python3 tools/sula_vector/render.py . --view changes-summary --since <session_start>
```

完成检查与 doctor 的成功不能声称这次改动已经经人工最终复核。用户保留让原模型做最后检查的安排。
