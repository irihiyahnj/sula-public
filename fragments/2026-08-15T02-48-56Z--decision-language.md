---
id: 2026-08-15T02-48-56Z--decision-language
time: 2026-08-15T02:48:56Z
kind: decision
refs: [2026-08-15T02-48-42Z--correction-60-legacy-legacy]
tags: [language, policy]
summary: 重述语言政策：人读的内容随项目语言，机器键与路径保持英文
---
上一条退休了 legacy 期的 add-project-language-policy-for-generated-docs，它绑在已不存在的 manifest [language] 段上。政策本身仍在执行——本向量的判断片段就是中文写的——所以按 B2 重述为 vector 期判断，而不是让它随实现一起蒸发。

政策：面向人阅读的内容（片段正文、summary、文档、命令输出）跟随项目语言；文件路径、fragment id、frontmatter 键名、kind 字符串保持英文，以保证同步、解析与跨项目可移植性稳定。

这一条不带 governs：它治理的是写作习惯，不是磁盘上的某个路径，没有可被见证移除的主体。
