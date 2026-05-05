# Sula 0.17.0 白皮书：Agent 原生的通用项目操作系统

## 执行摘要

Sula 0.17.0 的目标不是把 Sula 变成某一种开发框架、自动化平台、数据库工具、内容生产工具或 agent 插件。

Sula 0.17.0 的目标是把 Sula 升级为一个 **agent-native universal project operating system**：

- 任何人类、Hermes agent、Codex、Claude、Cursor、自动化服务或未来 agent，只要接入一个 Sula 管理的项目，就能从任意入口恢复项目上下文。
- Sula 负责提供项目事实、规则、状态、任务、artifact、风险、决策、验证、交接和记录。
- 外部 agent 是请求方和协作者；Sula 是 Sula-managed operating state 的写入执行方、规则执行方和审计方。
- 项目自己的业务工作流保持外部独立：可以是 n8n、GitHub、Google Drive、Postgres、ERPNext、线下门店流程、医院新媒体运营流程，或任何现实服务流程。

0.17.0 的核心产品判断：

> Sula 不替代项目业务系统。Sula 提供跨项目、跨 agent、跨人类团队的统一项目接入协议和操作记录层。

这是一项维度级升级。Sula 从“人或 agent 进入项目目录后运行 CLI”升级为“agent 可以通过受控工具面恢复项目事实、遵守项目规则、请求受控动作、写回证据和交接”。

## 最高规则

0.17.0 不允许削弱 Sula 已有最高规则：

> Preserve the split between centrally managed operating-system files and project-owned business truth.

新的 MCP、agent 接入、任务机制、portfolio 管理、provider adapter、workflow adapter 都必须服从这个规则。

这意味着：

- Sula-managed operating files 由 Sula 写。
- Project-owned business truth 仍归项目所有。
- 外部 agent 不应直接绕过 Sula 修改 Sula 管理的状态、catalog、memory、handoff、workflow 或 orchestration records。
- 业务系统由业务系统执行；Sula 记录、审查、验证和交接。

## 背景和问题

Sula 已经具备很多关键能力：

- `.sula/memory-digest.md` 作为每个会话的启动上下文。
- `STATUS.md`、change records、release records、incident records 作为 durable project memory。
- `report`、`check`、`doctor`、`status`、`query`、`artifact`、`workflow`、`orchestration`、`portfolio` 等 CLI surface。
- machine-readable JSON 输出。
- profile、projection packs、managed templates。
- `generic-project`、`react-frontend-erpnext`、`sula-core` 等 profile。
- provider-backed artifact identity、Google Drive read-only refresh、import plan、materialize。
- workflow policy、agent behavior policy、orchestration task/run/closeout evidence。

这些能力已经让 Sula 成为一个项目操作系统雏形。当前缺口不是“没有能力”，而是：

- agent 仍需要自己知道该读哪个文件、跑哪个命令、遵守哪些边界。
- Hermes 或其他 agent 在生产场景中如果拥有文件系统权限，可能绕过 Sula 直接修改状态文件。
- 多项目管理时，项目事实、当前状态、handoff、任务和风险无法从一个稳定工具面统一读取。
- 非软件项目虽然可以通过 `generic-project` 管理，但缺少一个明确的 agent 接入协议说明它们如何被读取、记录、审查和交接。
- 项目代码规则、业务规则、文档规则、artifact 规则、workflow 规则存在于多个文件里，agent 接入时需要一个统一的 policy view。

0.17.0 的升级正是为了解决这些缺口。

## 0.17.0 产品定位

Sula 0.17.0 应该被定义为：

> 一个让任意人类或 agent 在任意接入点恢复项目上下文、遵守项目规则、审查当前状态、记录新事实和提交完成证据的通用项目操作系统。

它服务两类项目：

- 软件开发项目：代码、PR、CI、测试、发布、架构、bug、feature、provider integration。
- 现实服务项目：医院新媒体运营、连锁咖啡店管理、客户服务交付、视频生产、培训项目、销售资料维护、线下运营 SOP。

它不依赖项目底层执行方式：

- 项目可以用 n8n 编排。
- 项目可以有数据库。
- 项目可以用 Google Drive、Notion、GitHub、Linear、Feishu、Airtable。
- 项目可以完全是线下服务加文档记录。
- 项目可以没有 Git。

Sula 只要求项目能表达下列事实：

- identity
- current state
- rules
- artifacts
- tasks
- decisions
- risks
- evidence
- handoff
- external system references

## 必须保留的既有能力

0.17.0 是增量升级，不是重写。执行 AI 不得删除或弱化以下能力：

- Session lifecycle：会话开始读 `.sula/memory-digest.md`，提交前 `report`，再 `check`。
- Managed/project split：managed templates 与 project-owned truth 的边界。
- `generic-project` baseline：未知项目先用通用内核接入，再逐步专业化。
- Profile abstraction：优先 profile-level abstractions，不写死单项目规则。
- Projection packs：AI tooling、ops-core、document-design、profile docs 等投影机制。
- Machine-readable CLI outputs：外部工具应优先消费 JSON，不 scrape human text。
- Artifact identity：provider-backed artifact 必须保留 `provider_item_id`、`project_relative_path`、`family_key` 等身份模型。
- Workflow docs：spec、plan、review 等 source-first workflow artifacts。
- Orchestration safety：dry-run default、approval categories、risk ceiling、closeout evidence。
- Agent behavior policy：verification、success criteria、diff scope、assumption handling。
- Feedback bundles：项目内可复用改进仍应通过 feedback lifecycle 上游化。
- Dependency-light bootstrap：不得让第三方服务或 Python 3.11+ 成为核心必需依赖。

## 0.17.0 核心支柱

### 1. Agent 原生接入面

Sula 应提供一个 MCP-compatible tool surface，让 Hermes、Codex、Claude、Cursor 或其他 agent 能够通过工具调用读取和记录项目状态。

这不是给 agent 一个 shell。正确形态是：

```text
agent -> Sula MCP tool -> Sula core command/function -> validation -> write/check/audit -> JSON result
```

第一版优先提供 read-only 和低风险 record tools。高风险写操作必须通过 dry-run、approval 和 policy gate。

### 2. Sula 作为写入执行方

生产环境中，外部 agent 不应直接修改 Sula-managed files。

Sula 应成为以下写操作的受控入口：

- `STATUS.md` report updates
- `.sula/memory-digest.md` regeneration
- `.sula/artifacts/catalog.json`
- `.sula/state/current.md`
- `.sula/state/orchestration/*`
- `.sula/state/automation/*`
- workflow scaffold records
- orchestration intake/closeout records
- provider snapshot cache
- managed template sync outputs

外部 agent 可以提出意图，但写入由 Sula 验证后执行。

### 3. 通用项目模型

Sula 不能只服务软件项目。0.17.0 的项目对象模型应覆盖现实服务项目。

通用项目对象包括：

- project identity
- profile and workflow pack
- current health
- current focus
- blockers
- handoff
- tasks
- artifacts
- decisions
- risks
- incidents
- release/delivery records
- provider-backed references
- external workflow references
- responsible humans or teams
- verification evidence

这些对象应能表达：

- 医院新媒体运营服务
- 连锁咖啡店门店管理
- 客户服务交付
- 软件开发
- 内容生产
- 培训交付
- 咨询项目
- 内部运营项目

### 4. 规则作为一等 policy

接入后，agent 不应只得到状态摘要，还应得到项目规则视图。

Sula 应能汇总并返回：

- highest rule
- AGENTS/CODEX/CLAUDE/GEMINI instructions
- profile rules
- workflow policy
- agent behavior policy
- document design rules
- artifact routing rules
- code/path constraints for software projects
- approval categories
- forbidden operations
- required verification commands

对于软件项目，这意味着代码约束更强：

- 哪些路径是 API layer、state layer、app shell。
- 是否允许 custom backend。
- 是否允许 React Router。
- 什么测试和 typecheck 是必要验证。
- 哪些改动必须有 PR、CI、review thread closure。
- 禁止 drive-by refactor。

对于现实服务项目，这意味着业务记录约束更强：

- 哪些 artifact 是事实源。
- 哪些文档需要客户确认。
- 哪些交付物属于 proposal、report、schedule、training、process。
- 哪些 provider-native 文档是最新事实源。
- 哪些审批、handoff 或风险记录必须存在。

### 5. 任务和证据闭环

Sula 的任务机制应成为 agent 默认工作入口。

任务不只是 todo。任务对象应携带：

- title
- source
- owner
- priority
- blockers
- acceptance criteria
- validation requirements
- risk hints
- related artifacts
- closeout evidence

完成任务不能只说“完成”。必须提供证据：

- changed files
- artifact ids
- provider item links
- check results
- PR status
- CI status when applicable
- review comment status when applicable
- customer approval or service delivery evidence when applicable
- updated handoff

### 6. Portfolio 多项目控制面

0.17.0 应让 Sula 更适合管理多个项目。

Portfolio layer 应支持：

- list projects
- project health summary
- stale memory detection
- stale artifact detection
- open blockers
- active tasks
- pending runs
- provider freshness risks
- next action summary
- profile/provider/workflow grouping

Hermes 这类长期运行的管理 agent 应优先从 portfolio surface 进入，而不是直接进入某个目录后猜项目状态。

### 7. Adapter 是可选能力，不是核心依赖

Sula 可以记录 n8n、Postgres、GitHub、Google Drive、Notion、Linear、Slack 等外部系统，但不应依赖它们成为核心。

正确关系：

- n8n 是 workflow provider 或 external system reference。
- Postgres 是 project system 或 evidence source，不是 Sula 默认操作对象。
- GitHub 是 repo/PR/CI adapter。
- Google Drive 是 storage/provider adapter。
- Notion/Linear 是 future task/artifact provider adapter。

Sula 管理事实、记录、规则、证据和交接。外部系统执行自己的业务流程。

## MCP Surface 设计

### 设计原则

0.17.0 MCP surface 必须遵循：

- Workflow-first，不是 endpoint wrapper。
- High-signal output，不返回无边界大文本。
- Tool outputs 必须 JSON-friendly。
- 写操作必须走 Sula policy gates。
- 默认 read-only。
- 不提供任意 shell。
- 不提供任意文件写入。
- 不绕过 `report`、`check`、`doctor`、`sync`、`orchestration close` 等已有 Sula 生命周期。
- 不把 MCP server 变成 Sula 核心必需依赖；CLI 必须继续可独立工作。

### 第一版 read-only tools

建议第一批 MCP tools：

```text
sula.project.bootstrap
sula.project.status
sula.project.check
sula.project.doctor
sula.project.query
sula.project.memory_digest
sula.project.rules
sula.artifact.locate
sula.artifact.list
sula.workflow.assess
sula.orchestration.tasks
sula.orchestration.runs
sula.portfolio.list
sula.portfolio.status
```

这些 tools 应只读取或运行非破坏性检查。

### 第一版受控写 tools

建议第一批受控写 tools：

```text
sula.report.create
sula.workflow.scaffold
sula.orchestration.intake
sula.orchestration.close
sula.artifact.register
sula.artifact.materialize
sula.artifact.refresh
sula.sync.dry_run
```

这些 tools 必须：

- 读取项目 manifest 和 rules。
- 记录 event/audit。
- 返回 changed files 或 generated records。
- 必要时运行 `sula check`。
- 在写 Sula-managed files 时由 Sula 执行写入，不由外部 agent 直接写。

### 强审批 tools

以下 tools 不应默认启用：

```text
sula.sync.apply
sula.remove
sula.provider.write
sula.release.create
sula.git.tag
sula.git.push
sula.runner.shell_command
```

它们必须满足：

- explicit enablement
- dry-run preview
- approval token or human confirmation
- dirty worktree inspection
- policy gate pass
- audit event
- post-operation check

## 安全模型

### 权限等级

MCP tools 应按权限等级分类：

- `read`: 只读取状态或运行无副作用检查。
- `record`: 写 Sula operating records，例如 report、task intake。
- `generate`: 生成 project-owned source artifact 或 derived artifact。
- `sync`: 更新 managed projection files。
- `provider-write`: 写外部 provider-native item。
- `destructive`: 删除、重置、移除、覆盖。
- `release`: tag、push、release、publish。
- `runner`: 启动 agent runner 或 shell command。

默认允许 `read`。生产环境中 `record` 可以启用。其他等级必须显式启用。

### Project root allowlist

MCP server 必须只操作 allowlisted project roots。

任何 tool 调用都必须先解析：

- project root
- `.sula/project.toml`
- profile
- highest rule
- managed files
- project-owned truth boundaries

不在 allowlist 内的路径必须拒绝。

### 写入规则

外部 agent 不能直接写：

- `.sula/`
- `STATUS.md`
- change/release/incident records
- workflow records
- artifact catalog
- managed projection outputs

这些写入必须通过 Sula tool。

Project-owned business truth 可以由人或项目工作流维护。Sula 只在明确 artifact/workflow command 下创建、登记或 materialize。

### 审计记录

每个写操作必须记录：

- tool name
- caller identity if available
- project root
- requested intent
- policy decision
- files changed
- artifacts affected
- verification result
- timestamp

这些记录可以进入 existing event log、automation state 或 orchestration run records，不必为 MCP 重建一套独立历史。

## 通用项目适配示例

### 医院新媒体运营服务

项目事实：

- 客户医院名称、服务范围、交付周期。
- 内容日历、选题库、素材库、审批流程。
- 微信公众号、视频号、小红书、抖音等平台账号引用。
- 医疗合规风险、禁用表达、审批人。
- 周报、月报、运营复盘、素材交付物。

Sula 管理：

- 当前状态：本周内容进度、待审批、风险、下一步。
- Artifacts：内容日历、月报、素材清单、审批记录。
- Tasks：选题、拍摄、剪辑、发布、复盘。
- Rules：医疗内容合规、客户审批、素材命名、交付格式。
- Handoff：下一个 agent 或团队成员从哪里继续。

Sula 不做：

- 不直接登录平台发布内容，除非未来明确 adapter 且经过审批。
- 不替客户审批医疗内容。
- 不把平台内容当作 Sula-managed truth。

### 连锁咖啡店管理

项目事实：

- 门店列表、区域负责人、SOP、供应商、活动日历。
- 门店检查表、客诉记录、设备维护、员工培训。
- 促销计划、库存异常、经营周报。

Sula 管理：

- Current health：哪些门店有 blocker。
- Tasks：巡店、培训、物料补充、设备报修、活动上线。
- Artifacts：SOP、培训材料、检查表、周报。
- Risks：食品安全、库存、人员、设备、活动延迟。
- Evidence：照片、检查记录、负责人确认、供应商回执。

Sula 不做：

- 不直接改 POS 数据库。
- 不替门店执行实际排班。
- 不绕过现有管理系统。

### 软件开发项目

项目事实：

- 代码仓库、架构、测试命令、部署流程、PR、CI。
- 业务需求、设计、接口、数据库迁移计划。
- 发布记录、incident、runbook。

Sula 管理：

- Code rules：路径约束、禁止自定义后端、测试策略、routing policy。
- Tasks：feature、bug、refactor、migration。
- Evidence：changed files、tests、typecheck、CI、PR review status。
- Closeout：report、check、memory digest、handoff。

Sula 不做：

- 不默认直接改生产数据库。
- 不默认发布生产。
- 不把 coding agent 的临时计划当作业务真相。

### n8n、数据库、前端混合项目

项目事实：

- n8n workflow URLs、webhook references、runbook、失败记录。
- 数据库 schema docs、migration plan、backup/rollback checklist。
- 前端 build/test/smoke test。

Sula 管理：

- 外部系统作为 references 和 evidence sources。
- 任务和风险统一纳入 Sula。
- 验证结果写回 Sula。

Sula 不依赖：

- 不要求项目必须使用 n8n。
- 不要求项目必须暴露数据库凭据。
- 不要求前端必须是 React。

## Provider 和 Capability Registry

0.17.0 可以增加一个薄层 provider capability registry，但不应引入完整动态 schema discovery。

建议第一版 capability report：

```json
{
  "provider": "google-drive",
  "capabilities": [
    "fetch_item",
    "fetch_tasks",
    "refresh_metadata",
    "normalize_google_doc",
    "normalize_google_sheet"
  ],
  "write_capabilities": []
}
```

收益：

- `doctor` 能解释当前 provider 能做什么。
- `artifact refresh` 可以提前说明能力缺口。
- MCP `project.bootstrap` 可以告诉 agent 哪些 provider actions 可用。
- 未来 Notion、Linear、GitHub、Feishu 接入时有统一描述方式。

不做：

- 不把 Composio/Rube 作为 Sula 核心依赖。
- 不一次性导入大量 provider skills。
- 不设计过大的 dynamic schema execution layer。

## PR 和 CI Closeout 增强

0.17.0 应增强 `pull-request-url` verification adapter。

当前能力：

- 识别 PR URL。
- 可通过 GitHub API 或 fixture 检查 PR state、merged、review decision。
- 支持 `remote_verification_policy`。

新增目标：

- CI checks summary。
- failed/action_required/pending check state。
- unresolved review threads count。
- review comments requiring action。
- fixture-backed tests。

第一版不应默认抓完整 CI logs。结构化状态优先。CI log fetching 可以作为诊断 helper 或后续 tool。

收益：

- closeout 不再只是“有 PR 链接”。
- Sula 能区分“PR 存在”和“PR 可接受”。
- 任务完成证据更可信。

## 0.17.0 交付范围

### 必做

1. 新增 Sula MCP-compatible server entrypoint。
2. 暴露 read-only project/portfolio tools。
3. 暴露低风险 controlled record tools。
4. 将 project bootstrap/rules/policy view 做成稳定 JSON。
5. 让 Sula 自己执行 Sula-managed writes。
6. 为 MCP writes 记录 audit/event evidence。
7. 增强 PR closeout structured checks。
8. 新增 provider capability report 薄切片。
9. 更新 README、manifest reference、agent instructions、release docs。
10. 加 canary tests 覆盖 software project 和 non-software service project。

### 可执行任务包

0.17.0 应拆成可以独立验证、可以被 agent 接手的任务包，而不是一次性大改。

| 任务 | 产物 | 验收证据 |
|---|---|---|
| `mcp-readonly-surface` | dependency-light MCP-compatible server entrypoint；allowlisted project root resolver；read-only tools | JSON fixtures；no-write tests；`project.bootstrap`、`project.status`、`project.check` 返回稳定 envelope |
| `project-policy-view` | `project.bootstrap` 和 `project.rules` 的 consolidated policy payload | 软件项目和服务项目 fixture 都能返回 highest rule、handoff、approval classes、verification commands |
| `controlled-record-tools` | `report.create`、`workflow.scaffold`、`orchestration.intake`、`orchestration.close` write path | Sula 执行写入；返回 changed files；audit event 存在；dirty worktree 不覆盖用户改动 |
| `portfolio-control-surface` | `portfolio.list`、`portfolio.status` 项目汇总 | 多项目 fixture 能输出 health、blockers、stale memory/artifact、next actions |
| `provider-capability-report` | provider capability registry thin slice | Google Drive fixture 显示 read capabilities；缺失 write capability 时返回明确 gap |
| `pr-closeout-structured-checks` | PR/CI/review structured closeout evidence | GitHub fixture 覆盖 passing、failed、pending、review-action-required 状态 |
| `non-software-canary` | generic service project canary | 服务项目能完成 bootstrap、rules、status、task intake、artifact locate/register、report/check |
| `release-docs-and-rollout` | README、reference docs、manifest docs、change record、release record | `check`、`doctor --strict`、unit tests、all canaries pass |

每个任务包都必须能单独关闭：有 touched files、有验证命令、有 rollback 说明，并且不要求后续任务已经完成才能判断本任务是否正确。

### 应做

1. `portfolio.status` MCP tool。
2. `workflow.assess` and `orchestration.tasks` MCP tools。
3. `report.create` MCP write path 自动触发 digest/check option。
4. webapp testing 作为 frontend profile optional verification guidance。
5. batched migration workflow plan template。

### 不做

1. 不让 MCP 成为 CLI 的替代品。CLI 必须继续可用。
2. 不让 Hermes 或其他 agent 直接写 Sula-managed files。
3. 不引入 Composio/Rube 作为核心依赖。
4. 不默认操作生产数据库。
5. 不默认写 provider-native documents。
6. 不开放任意 shell command。
7. 不把软件项目规则套到现实服务项目上。

## 建议实现顺序

### Phase 1：Read-only MCP 管理面

实现：

- MCP server entrypoint。
- project root allowlist。
- `sula.project.bootstrap`
- `sula.project.status`
- `sula.project.check`
- `sula.project.query`
- `sula.artifact.locate`
- `sula.orchestration.tasks`
- `sula.portfolio.status`

验收：

- Hermes 可以连接 Sula MCP。
- Hermes 可以从任意 allowlisted project 获取 status/handoff/rules。
- 不发生文件写入。
- 所有 tools 返回 JSON。

### Phase 2：受控记录写入

实现：

- `sula.report.create`
- `sula.orchestration.intake`
- `sula.workflow.scaffold`
- `sula.artifact.register`
- audit/event record
- post-write optional `check`

验收：

- agent 不直接编辑 `STATUS.md`。
- Sula tool 写 report 后 memory digest 可更新。
- 写操作返回 changed files 和 verification evidence。
- dirty worktree 场景不覆盖用户改动。

### Phase 3：规则和 policy view

实现：

- `sula.project.rules`
- project bootstrap includes rules bundle。
- code constraints for software projects。
- artifact/document/workflow rules for service projects。
- approval categories and forbidden operations。

验收：

- Hermes 启动任务前能读取规则。
- 软件项目能看到 code/test/path rules。
- 服务项目能看到 artifact/approval/handoff rules。

### Phase 4：Portfolio 多项目控制面

实现：

- project registry loading。
- health/blockers/handoff summary。
- stale status/artifact warnings。
- active tasks and pending runs。

验收：

- Hermes 可以从 portfolio 看所有项目。
- 能识别哪个项目需要处理。
- 能跳转到具体项目 bootstrap。

### Phase 5：Closeout 和 provider 增强

实现：

- PR CI summary。
- unresolved review threads summary。
- provider capability report。
- fixture-backed tests。

验收：

- PR link closeout 能报告 CI/review 状态。
- provider refresh 能报告可用能力和缺口。

### Phase 6：Canary 和 release

至少跑四类 canary：

- Sula Core project。
- generic non-software service project。
- software delivery project。
- provider-backed Google Drive style project。

每个 canary 必须验证：

- bootstrap。
- rules。
- status。
- query。
- report/create。
- check。
- task intake。
- artifact locate/register。

## Manifest 和配置建议

0.17.0 不必立刻大幅扩展 `.sula/project.toml`。应优先复用：

- `[workflow]`
- `[orchestration]`
- `[automation]`
- `[agent_behavior]`
- `[storage]`
- `[portfolio]`
- `[document_design]`

如果需要新增 MCP server policy，建议使用本地配置而不是项目真相：

```text
.sula/local/mcp-policy.json
```

该文件不应成为跨机器项目事实。它描述当前机器允许 MCP server 操作哪些 project roots、开启哪些 write classes。

项目级长期 policy 若需要进入 manifest，应在 0.17.x 后续版本谨慎添加。

## 对比当前版本的具体收益

### 现在

- agent 需要自己读文件、猜命令、理解规则。
- 多项目状态需要逐个目录查看。
- 外部 agent 有可能直接改 Sula state。
- 任务机制需要 agent 主动记得使用。
- 项目规则散落在 manifest、AGENTS、docs、templates 中。
- 服务类项目可以被 Sula 管，但 agent 接入协议不够清晰。

### 0.17.0 之后

- agent 通过 `project.bootstrap` 获得项目身份、状态、规则、handoff、禁止事项。
- Sula-managed writes 由 Sula 执行。
- Hermes 可以通过 portfolio 发现需要处理的项目。
- 任务、artifact、report、check 成为工具闭环。
- 软件项目的 code rules 以 policy view 暴露给 agent。
- 服务项目的 artifact、审批、交付、handoff 规则也以 policy view 暴露。
- closeout 能包含更可信的 PR/CI/review/provider evidence。
- 新 agent 接入成本显著降低。
- 项目交接不再依赖某一个 agent 的聊天记忆。

## 风险和控制

### 风险：MCP 写操作放大错误

控制：

- 默认 read-only。
- write classes 显式启用。
- Sula 执行写入，不给 agent 任意文件写权限。
- audit/check/report。

### 风险：过度设计 provider discovery

控制：

- 0.17.0 只做 provider capability report。
- 不做动态 schema execution layer。

### 风险：软件项目能力污染服务项目

控制：

- generic object model。
- workflow pack 决定 artifact routing。
- profile 只表达真实项目类型，不强套 software-delivery。

### 风险：旧功能被重写或删除

控制：

- 0.17.0 是 adapter/control-plane addition。
- CLI, templates, lifecycle, artifact, workflow, orchestration 都保留。
- 新 MCP surface 调用现有 core function/CLI contracts。

## Definition of Done

0.17.0 完成时应满足：

- `sula check` 和 `doctor --strict` 通过。
- 所有现有 canary 通过。
- 至少一个 non-software service canary 通过。
- MCP read-only tools 可被 Hermes 使用。
- MCP controlled write tools 由 Sula 完成写入。
- `project.bootstrap` 输出完整 project/rules/status/handoff summary。
- `portfolio.status` 能汇总多个项目。
- PR closeout structured checks 覆盖 CI/review status。
- Provider capability report 可见。
- README 和 reference docs 更新。
- Release record 说明 0.17.0 的边界：agent-native control surface, not business-system automation.

## 给执行 AI 的工作指令

执行 0.17.0 升级的 AI 必须：

1. 先读 `.sula/memory-digest.md`。
2. 不删除既有 Sula 能力。
3. 不把 MCP server 做成唯一入口。
4. 不引入核心强依赖。
5. 不开放任意 shell 或任意文件写。
6. 先实现 read-only MCP tools。
7. 再实现受控 record tools。
8. 写入必须通过 Sula core/CLI contract。
9. 每个新增写 tool 都要有 tests。
10. 更新 docs、schema、README、change record。
11. 最后运行 `python3 scripts/sula.py check --project-root .` 和 `python3 -m unittest discover -s tests -v`。

## 最终结论

Sula 0.17.0 应该把 Sula 从“项目内 CLI + 记忆系统”升级为“agent 原生的通用项目操作系统控制面”。

这个升级的核心收益不是让 Sula 替项目做更多业务执行，而是让任何人、任何 agent、任何团队成员都可以从任何接入点无缝进入项目：

- 先知道项目是什么。
- 先知道规则是什么。
- 先知道当前状态是什么。
- 先知道下一步是什么。
- 工作后把事实、证据和交接写回 Sula。

这就是 Sula 0.17.0 的产品边界和执行方向。
