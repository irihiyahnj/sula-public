---
id: 2026-07-25T19-44-20Z--decision-witness-delta-churn
time: 2026-07-25T19:44:20Z
kind: decision
tags: [witness, defect, substrate]
summary: witness 的 delta 路径必须转义控制字符，否则含换行的文件名永久churn
---
为钱王炽接入时发现：它的 migration_workspace/boardmix_md/ 下有 4 个文件名内含换行符（'便签-回来目的\n初步.md' 这种，来自其他工具同步过来的文档）。

witness 的 delta 是一行一文件、格式 'marker digest size path'，折叠时用 split(None, 3) 解析。路径含换行就断成两行：尾行解析不出被丢弃，头行记下被截断的路径。于是每次运行都把真路径报成新增、把幻影路径报成删除，实测连续三次复现、永不收敛。这既违反 C7（churn），更严重的是折叠出的状态是错的——那几个文件的证据不可信。

修法是写入时转义 \\ \n \r、折叠时还原。只转义控制字符，CJK 路径保持可读（用 unicode_escape 会把中文变成 \uXXXX，那是拿可读性换正确性）。不加向后兼容垫片（D4）：旧片段里被截断的幻影路径会在下一次捕获时被记为删除，状态自愈——实测钱王炽刷新后一次捕获即收敛，随后两次沉默。

这个缺陷只在文档型底座上暴露。代码仓库的文件名不会长这样，所以 v1.0 到 v1.1.2 一直没碰到——接入真实的 iCloud 文档文件夹是它第一次被触发。
