---
id: 2026-08-15T05-01-13Z--pitfall-note-py-shell-stdin-heredoc
time: 2026-08-15T05:01:13Z
kind: pitfall
refs: [2026-08-15T05-00-15Z--decision-verifier-b9]
tags: [note, shell, pitfall]
summary: note.py 正文走 shell 参数会被插值：用 stdin heredoc
---
上一条片段 decision-verifier-b9 的正文缺了一段：原文写的是「4 个共用同一条 `unittest && doctor`」，反引号被 zsh 当成命令替换执行（终端里留下 `zsh: command not found: unittest`），那段代码名被吃掉，落盘成「4 个共用同一条 。」。

按 B1/E3 不修改、不删除那个片段——它的判断本身仍然成立且在force，缺的只是正文里一个命令名。这条片段补上原文，并把这个陷阱本身记成可继承的知识，而不是留一次无意义的 churn。

陷阱：把正文作为 shell 参数传给 note.py 时，双引号内的反引号、`$(...)`、`$VAR` 都会被 shell 先求值。片段正文经常包含命令示例，所以这是必然会再次发生的事。

安全写法是走 stdin，并且 heredoc 分隔符加单引号（关掉插值）：

    python3 tools/sula_vector/note.py . --kind decision --title "..." <<'BODY'
    正文里可以放 `任何命令`、$变量、$(替换)
    BODY

这条片段本身就是这么写的。

工具侧不改：note.py 收到的已经是 shell 处理后的字符串，它无法区分「用户本来就想写这些字符」和「shell 吃掉了内容」。这属于宿主与工具的边界，不是 note.py 能代为防御的。
