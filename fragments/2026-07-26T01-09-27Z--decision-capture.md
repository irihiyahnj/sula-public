---
id: 2026-07-26T01-09-27Z--decision-capture
time: 2026-07-26T01:09:27Z
kind: decision
refs: [2026-07-26T01-04-53Z--goal-capture]
tags: [capture, kiro, launchd, honesty]
summary: 捕获挂在宿主真的会读的地方；宿主格式必须核实而非推测
---
查 Kiro CLI 文档核实：钩子只在 agent 配置 JSON 的 hooks 字段里生效，触发点为 agentSpawn / userPromptSubmit / preToolUse / postToolUse / stop，没有 agentStop，且 .kiro/hooks/ 是 Kiro IDE 的位置。Sula 写的正是 .kiro/hooks/*.kiro.hook + agentStop，还打印「kiro installed」。结论：v1.1 起所有非 git 底座的机械捕获是死的，而安装器一直报成功。

对一个以诚实记录为目的的工具，谎报自己的接线比缺功能更糟——它让人以为不必再管。

四项修法：

一、Kiro CLI 改写 .kiro/agents/sula.json：agentSpawn 跑 boot（其 stdout 会被直接加进会话上下文，于是 boot 从「靠 agent 记得跑」变成机械注入），stop 触发 witness。kiro-cli agent validate exit 0。

二、写出但**不激活**。自定义 agent 会替换内建默认 agent 的系统提示词，那是用户没要求的降级，不能代替他决定。安装器明确打印 NOT active 与激活命令。这条是刻意的：能力要给到，选择权不拿走。

三、非 git 底座在 macOS 上装 launchd 而非打印 cron 行。cron 读 ~/Library/Mobile Documents 需要 Full Disk Access，launchd 跑在用户会话里不需要。已在 iCloud 项目上端到端实测：改一个文件后 launchctl kickstart，片段数 16→17，日志确认 witness 落盘。

四、launchd 的 label 附加路径哈希。中文目录名被 ASCII 正则剥空后会落到同一个 fallback，两个中文项目会共用一个 label 互相驱逐——与 note.py 的 slug 同一类缺陷（把非 ASCII 当成没有内容）。

根因不是这一个错，是 install.py 零测试覆盖，所以假成功报告活过了两个版本。现补四条测试，其中一条把 Kiro CLI 的合法触发点集合钉住：任何未来加的触发点若不在文档集合内，测试即失败。
