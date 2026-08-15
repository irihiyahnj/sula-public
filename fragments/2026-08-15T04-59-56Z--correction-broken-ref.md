---
id: 2026-08-15T04-59-56Z--correction-broken-ref
time: 2026-08-15T04:59:56Z
kind: correction
refs: [2026-08-15T02-47-06Z--decision-b8-done-gate-doctor-unexplained-change, 2026-07-25T22-46-45Z--correction-fleet]
tags: [doctor, b1, repair, fleet]
summary: broken_ref 必须支持列表：修复路径不可扩展等于门永久关闭
governs: tools/sula_vector/render.py
---
doctor 里 broken_ref 的实现是标量：acknowledged 用 str(f.get('broken_ref')) 收集，传列表会变成 "['a', 'b']"，匹配不上任何 id。于是悬空引用的修复路径是一条坏引用一个片段。

昆明同仁医院有 483 条悬空引用（v1.0 时代手写片段的遗留）。483 次 append 不是不方便，是没人会走的路。后果是那个项目的 done-gate 永久关闭。

这与本轮加门的论据直接冲突：我用「一道跑不完/关不上的检查提供的保证是零」推翻了 v1.1.2 的可见性方案，那么留一个让门永久失效的缺口就是同一个错误的另一面。加门这个动作自带一个义务——保证门能被诚实地重新打开。

改用 id_list，标量与列表都受支持（v1.0 片段写的是单个 id，必须继续有效）。

同时补上写入路径：note.py --broken-ref，是唯一不做存在性校验的写入参数——那些 id 之所以是坏的，恰恰因为没有任何片段承载它们，校验它们会让这条路根本无法使用。

诚实的边界：这只解决 dangling-ref。昆明同仁医院另有 301 条 header-disagreement，那类问题目前没有修复路径——frontmatter 里的 id/time 与文件名不一致，而按 B1 过去的片段不可编辑。要不要把「修正冗余副本」视为 B1 例外，是一个需要单独决定的设计问题，本轮不动。
