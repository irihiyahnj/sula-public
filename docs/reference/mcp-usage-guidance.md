# Sula MCP 使用指南

Sula 0.17.0 提供了两种 MCP 接入方式：`mcp call` 和 `mcp serve`。选择哪一种取决于使用场景。

## 核心判断：`mcp call` 优先，`mcp serve` 按需

| 维度 | `mcp call`（按需调用） | `mcp serve`（常驻服务器） |
|------|------------------------|---------------------------|
| 机制 | 每次调用启动一个短命进程，返回 JSON 结果后退出 | stdio JSON-RPC 长连接，工具定义持续注入 session context |
| 新会话 token 开销 | **0** | ~3000-5000 token（23 个工具定义注入 prompt） |
| 单次 Sula 查询 token | ~300（完整 bash 调用） | ~100（直接调工具） |
| 跨项目查询 | 每次指定 `--project-root` | portfolio 模式下可直接查注册项目 |
| 故障隔离 | 每次独立，一次失败不影响后续 | server 挂掉则所有连接 session 丢失 Sula 能力 |
| 需要配置 | 不需要任何配置文件 | 需要 `mcp.json`（Codex）或 `mcp_servers` 配置 |

## 默认策略：`mcp call`

**绝大多数场景推荐 `mcp call`**，原因：

1. **零配置** — 不需要 `mcp.json`，不需要修改 Codex/CC 配置
2. **零税** — 不用 Sula 的 session 绝不为此支付 token
3. **灵活** — 任何 agent 随时可以 `sula mcp call --tool sula.project.status --project-root .`
4. **不耦合** — Sula 作为普通 CLI 工具存在，不与 agent 运行时绑定
5. **可跨项目** — `--project-root` 可以是任意路径

### 在 AGENTS.md / Sula skill 中引导使用

在项目的 AGENTS.md 或 Sula skill 中添加：

```bash
# 查项目状态
python3 ~/.sula/source/scripts/sula.py mcp call \
  --tool sula.project.status --project-root .

# 查 portfolio 全局健康
python3 ~/.sula/source/scripts/sula.py mcp call \
  --tool sula.portfolio.status
```

Agent 不需要知道 MCP 协议细节，只需要知道这些命令等价于「查 Sula 状态」。

## 何时用 `mcp serve`

以下场景才值得为 `mcp serve` 付出常驻开销：

1. **重度 Sula 使用** — 单一 session 中预计调用 Sula 10+ 次
2. **需要写工具** — report、scaffold、intake、close 等记录类操作需要 serve 的 `--enable-write-class` 参数
3. **专用项目 session** — 一个 Codex session 专门管一个项目，Sula 是其主要操作对象

此时在项目根目录放置 `.mcp.json`：

```json
{
  "mcpServers": {
    "sula": {
      "command": "python3",
      "args": [
        "/home/jing/.sula/source/scripts/sula.py",
        "mcp", "serve",
        "--allow-project-root", ".",
        "--portfolio-root", "/home/jing/.sula/portfolio",
        "--enable-write-class", "record"
      ]
    }
  }
}
```

## 不要做的事

- ❌ **不要在全局 `~/.codex/mcp.json` 中配 Sula** — 会让所有 session（包括跟 Sula 无关的实验 session）都吃 5000 token 开销
- ❌ **不要假设 MCP 会主动提示 agent 使用** — MCP 暴露工具定义，不输出自然语言引导。agent 用不用 Sula 取决于 AGENTS.md 的规则，不取决于 MCP 可用性
- ❌ **不要为每个项目都配 serve** — 大部分项目 agent 偶尔查一次状态就够了

## 多 Agent 协作中的角色

MCP 不是治理推广机制。Sula 治理管线的推广靠的是 AGENTS.md 和 Sula skill 中写死的规则。

MCP 解决的是**多 Agent 同时工作时的状态一致性**：所有 agent 通过同一套工具访问同一个 Sula 状态源，不会出现「A 看到任务 open，B 已经关了」的分歧。

但它不解决：
- 并发写入冲突（还是需要 git merge / 编排层任务分配）
- 人类是否会用（人类用 `sula.py status` 比 MCP JSON 直观得多）
