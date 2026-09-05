---
id: 2026-08-16T09-32-53Z--intent-sula-vector
time: 2026-08-16T09:32:53Z
kind: intent
tags: [subagent, review-fixes, p1]
summary: 派子代理修复评审发现的 Sula Vector 缺陷
done_when: P1-1..P1-4 修复并加回归测试，P2 文档同步；python3 -m unittest tools.sula_vector.tests.test_sula_vector 全绿；render . --view doctor exit 0；doctor 的 unexplained-change 被对应 decision --explains 结清
verifier_ref: shell: python3 -m unittest tools.sula_vector.tests.test_sula_vector && python3 tools/sula_vector/render.py . --view doctor
executor_command: codex -a never exec --ephemeral --sandbox workspace-write -
---
你是通过 Sula Vector 的 llm-dispatcher skill 从主代理派出的子代理。工作目录是 /Users/jing/dev/Project/projectdev/sula-vector。这是一次真实的代码修复任务，不是 dry-run。

第一步按 AGENTS.md 的两步 boot 执行：记录当前 UTC 时间作为 session_start，然后运行并阅读：
python3 tools/sula_vector/render.py . --for-agent

必须遵守的边界：
- 永远不要编辑或删除 fragments/ 下已有片段；新片段只能用 tools/sula_vector/note.py 追加。
- 不要修改 legacy/。
- 不要 commit；把 working tree 留给操作者复核。
- 保持标准库 only，不加第三方依赖。
- 修改核心代码的同时，在 tools/sula_vector/tests/test_sula_vector.py 加对应回归测试。
- 不要顺手做重构或与本任务无关的 cleanup。

修复清单（按优先级）：

P1-1 render.py 的 _is_satisfied() 对 intent 的语义错误。
现状：kind=intent 且含 done_when 时，只要有任何 fact/verification-fact 反向引用该 intent 就返回 True；passed:false 的 verification-fact 也会“关闭”方向，导致失败的方向从 boot 和 open_intents 消失。
要求：intent 含 done_when 时，只有以下情况视为满足：(a) closure_map 中显式 closes；(b) 存在 passed 为 true 的 verification-fact 反向引用。普通 fact 反向引用不再自动满足；passed:false 绝不满足。goal 的现有逻辑保持不变。加回归测试：intent + passed:false 必须仍出现在 view_digest 的 open_intents；intent + 普通 fact 反向引用不满足；intent + passed:true 满足；显式 closes 满足。全套测试通过。

P1-2 note.py 的 --field 可以覆盖保留字段。
现状：fields.update(extra) 无条件执行，--field kind=goal 等可覆盖 id/time/kind/refs，绕过引用校验并写出医生会报错的文件，而工具还报告成功。
要求：--field 的 key 不允许是保留键：id、time、kind、lane、refs、tags、closes、supersedes、explains、broken_ref、explained_by、done_when、verifier_ref 等由专门参数控制的字段。命中时打印明确错误并返回非 0，不写文件。加测试：--field kind=goal 必须失败且不产生 fragment；--field id=<something> 必须失败。

P1-3 符号引用在 doctor 与 note.py 之间不一致。
现状：render.py view_doctor() 对含 ":" 且不以 "20" 开头的目标跳过 dangling-ref 检查，但 note.py 的未知 id 校验不跳过，导致 --refs family:key 这类文档允许的 symbolic ref 无法通过官方写入口创建。
要求：把“是否为符号引用”抽成一个公共函数（例如 render.py 中的 is_symbolic_ref），note.py 和 doctor 共用；note.py 的 --refs/--closes/--supersedes/--explains 校验对符号引用放行（broken_ref 不变）。加测试：note.py --refs family:demo 成功写入；doctor 对写出的片段不报 dangling-ref；普通未知 id 仍被拒绝。

P1-4 render.py 对非法 UTF-8 片段崩溃。
现状：load_report() 只捕获 OSError，read_text 抛 UnicodeDecodeError 会让 render 直接 traceback，而不是进入 doctor problem 列表。
要求：把 UnicodeDecodeError（或 UnicodeError）也转成 Problem("unreadable", ...)，render 继续完成。加测试：写入一个非法 UTF-8 的 .md 文件，view_doctor 报告 unreadable 且不抛异常。

P2-5 文档漂移。
现状：CONTRIBUTING.md、.github/pull_request_template.md、SECURITY.md 仍引用当前根目录不存在的 scripts/sula.py、tests/test_sula.py、examples/okoktoto 等 legacy 路径。
要求：把验证基线更新为当前真实命令：
  python3 -m unittest tools.sula_vector.tests.test_sula_vector -v
  python3 tools/sula_vector/render.py . --view doctor
  python3 tools/sula_vector/render.py . --for-agent > /dev/null
并删除/改写这些文件中对 legacy CLI 的过期引用；SECURITY.md 的范围从 scripts/sula.py 改为 tools/sula_vector/。保持 AGENTS.md 中“legacy 文件是历史参考”的表述不变。

完成后的验收与收尾：
1. 运行 python3 -m unittest tools.sula_vector.tests.test_sula_vector -v，必须全绿。
2. 运行 python3 tools/sula_vector/skills/witness.py --project-root .，记录它输出的 witness id。
3. 用 note.py 追加一个 decision，--explains <刚才的 witness id>，说明你修了什么、为什么；一个 decision 覆盖本批修复即可。
4. 运行 python3 tools/sula_vector/render.py . --view doctor，必须输出 0 problems 且 exit 0。
5. 运行 python3 tools/sula_vector/render.py . --view changes-summary --since <你的 session_start>，在最终回复中完整贴出 [sula] +N this turn: 块。
6. 回复中还要列出：每个 P 项的完成状态、修改的文件、新增测试名、witness id、doctor 结果。
