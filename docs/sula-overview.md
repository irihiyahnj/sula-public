# Sula：AI 原生的项目操作系统

## 一句话

**Sula 是一套以文件为协议、以 CLI 为 API 的项目操作系统。它让任何 AI 模型在任何项目中都能可靠、可验证、可交接地工作。**

---

## 问题：AI 编程很好用，但不可靠

AI 编程工具的现状是：

- AI 说"做完了"，但文件没改全
- AI 说"测试通过了"，但其实没跑
- 换个模型（Claude → GPT），行为完全不一样
- 关了对话明天回来，AI 不记得昨天做了什么
- 人把项目交给另一个 AI，要重新解释全部上下文

这些问题不是某个模型不够聪明。而是**所有 AI 都缺少一个统一的治理层**——没有标准告诉我"当前项目状态是什么、任务该怎么接、做完了怎么验证"。

## Sula 做什么

Sula 不写代码。它提供的是 AI 开发中缺失的三个基础层：

| 层 | 做什么 | 核心机制 |
|---|---|---|
| **状态层** | 项目完整状态在任何时候可被任何 AI 读取 | `STATUS.md` + `memory-digest.md` |
| **任务层** | 任务从创建到验证到关闭的完整闭环 | `workflow start` → work → `orchestration close` |
| **验证层** | 做完了就是做完了，不是 AI 说了算 | 文件存在检查 + 链接可解析 + `sula check` |

## 怎么做：核心机制

### 1. 文件即协议，CLI 即 API

Sula 完全以文件和命令行工作。没有服务器，没有数据库，没有平台锁定。

```
项目结构（一个被 Sula 管理的项目）：

.sula/                    ← 内核（AI 自动维护）
  project.toml            ← 项目配置
  kernel.toml             ← 内核清单
  memory-digest.md        ← 当前状态摘要（每次对话开始时读）
  state/current.md        ← 运行时状态（AI 自动生成）

STATUS.md                 ← 项目主状态文件（人也可以看）
CHANGE-RECORDS.md         ← 变更记录索引
docs/change-records/      ← 详细变更记录
docs/workflows/tasks.json ← 活跃任务清单

scripts/sula.py           ← 唯一的可执行入口
site/sula.json            ← 跨 AI 协议描述符
```

### 2. Session 生命周期：零遗忘

每次对话，AI 自动走这三个步骤：

```
开始 → 读 memory-digest.md，知道项目当前状态
工作 → workflow start → 执行 → orchestration close
结束 → sula report，自动更新 STATUS.md + 再生 memory-digest
```

效果：**人和 AI 在任何时候接手项目，都是"热启动"。**

### 3. 任务闭环：不是 AI 说做完了就算

```
workflow start           ← 把自然语言任务形式化为结构化文档
  ↓
执行（AI 写代码）
  ↓
orchestration close      ← 验证：文件在不在？链接对不对？check 通不通过？
  ↓
不通过 → 显示阻塞原因 → AI 修复 → 再 close → 循环直到通过
```

### 4. 跨 AI 协议：不锁平台

`site/sula.json` 包含 `workflow_auto_loop` 协议，用自然语言描述 AI 行为规则：

- 任务来了 AI 该怎么处理
- 什么时候形式化、什么时候执行
- 完成时验证什么
- 什么情况下问人

这跟你用 Claude、GPT、Gemini、DeepSeek 无关。**任何能读文件的 AI 代理都能按同一协议工作。**

### 5. agent_behavior 策略：约束 AI 的自由度

AI 默认会"即兴发挥"——顺手重构、改自以为是的代码、跳过验证。Sula 通过 project.toml 写入硬约束：

```
[agent_behavior]
quality_policy = "sula-karpathy-inspired"    ← 质量优先
diff_scope_policy = "surgical"               ← 只改该改的
forbid_drive_by_refactors = true             ← 禁止顺手重构
require_verification = true                  ← 必须验证
success_criteria_policy = "required"         ← 必须有成功标准
clarification_policy = "non-trivial-only"    ← 不确定就问
```

这些不是建议，是规则。AI 的行为被约束为"工程师水准"。

### 6. 接入零门槛：一句话

```bash
git clone https://github.com/irihiyahnj/sula-public.git /tmp/sula && \
python3 /tmp/sula/scripts/sula.py onboard --repo-url <项目地址> --accept-suggested --approve
```

背后自动完成：clone 仓库 → 分析项目类型 → 生成 project.toml → 创建 STATUS.md → 应用治理文件 → 验证。

---

## 0.17.0 方向：Agent 原生控制面

Sula 0.17.0 的升级方向是把这些文件和 CLI 能力暴露成受控的 agent-native project OS control surface：

- agent 通过稳定工具面读取 project bootstrap、rules、status、handoff、tasks 和 artifacts。
- Sula-managed writes 由 Sula 执行，不由外部 agent 直接改 `.sula/`、`STATUS.md` 或 orchestration records。
- 多项目场景从 portfolio surface 进入，先判断哪个项目需要处理。
- MCP-compatible server 是可选接入面，CLI 仍然独立可用。

完整设计见 [Sula 0.17.0 白皮书](reference/sula-0-17-0-agent-native-project-os-whitepaper.md)。

## 能做到什么

### 对人

| 场景 | 没有 Sula | 有 Sula |
|---|---|---|
| 新项目启动 | 手动建目录、写 README、记不住要加什么 | 一句话接入，所有治理文件自动生成 |
| 隔天回来 | "上次做到哪了？" | AI 自动读 memory-digest，热启动 |
| 交给别人 | 解释半天项目状态 | STATUS.md 给出完整 handoff |
| 换 AI 工具 | 行为完全不一样 | 行为一致，因为遵循同一协议 |

### 对 AI

| 场景 | 没有 Sula | 有 Sula |
|---|---|---|
| 开始工作 | 猜项目目标、猜规则 | 读 memory-digest + project.toml，确定性启动 |
| 完成任务 | 说"做完了" | orchestration close 验证文件 + 链接 + check |
| 阻塞 | 默默放弃 | check 输出阻塞原因，AI 知道改什么 |
| 跨平台 | 每个平台行为不同 | sula.json 协议不变 |

### 对项目

| 能力 | 说明 |
|---|---|
| 每日检查 | `sula check` 检测状态 drift、handoff 是否合规、memory-digest 是否过期 |
| 增量测试 | `sula test` 快速验证，`sula test --module` 模块级测试，`sula test --full` 发版前全量 |
| 自动化内核 | 任何 CLI 事件自动生成 intent → 规划 → 分派 → 执行 |
| 记忆系统 | 阶段性 session 捕获 → 审核 → 晋升为持久规则或查询路由 |
| 反馈回路 | 下游项目发现 Sula 问题 → 打包反馈 → 核心审核 → 融合回主线 |
| 发版治理 | `release readiness` 审计完整性，`export-public` 生成干净公开分支 |

---

## 不是什么

- **不是 AI 编辑器** — Sula 不写代码，它是底层治理
- **不是自主 Agent** — Sula 不独立跑任务，它给 AI 加验证而不是替代人
- **不是平台** — 不锁模型、不锁 IDE、不需要账号、不需要服务器
- **不是 SaaS** — 开源、Git 交付、无订阅

---

## 核心设计哲学

**用系统结构替代 AI 猜测。**

AI 在独立工作时有三个不确定性：状态不确定性（"我不知道这个项目什么情况"）、行为不确定性（"我应该怎么处理这个任务"）、结果不确定性（"我真的做完了吗"）。

Sula 用三个确定性回答：

- 状态确定性 — 文件记录，不靠记忆
- 行为确定性 — 协议约束，不靠 prompt 工程
- 结果确定性 — 可编程验证，不靠 AI 自述

---

## 版本

- **当前版本**: v0.18.4
- **仓库**: `https://github.com/irihiyahnj/sula-public.git`
- **许可证**: MIT
- **依赖**: Python 3 + Git
- **作者**: Sula Core Maintainers
