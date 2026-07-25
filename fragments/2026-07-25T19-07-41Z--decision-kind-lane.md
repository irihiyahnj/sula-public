---
id: 2026-07-25T19-07-41Z--decision-kind-lane
time: 2026-07-25T19:07:41Z
kind: decision
refs: [2026-07-25T19-04-14Z--goal-boot-force-10]
tags: [render, lane, b3]
summary: kind→lane 查表保留，改为写入时回显；结构派生方案不成立
---
我先前提出用结构派生 lane（带 done_when/verifier_ref → direction，带 commit/hash → evidence，其余 → judgment），以消掉 LANE_BY_KIND 这张表。核对实际 kind 分布后此方案不成立：event(231)、release(23)、operation(8)、snapshot(2)、fact(1) 都没有可键的结构字段，「无字段→judgment」会把 250 多条证据翻进 in-force 判断集——正是刚修掉的那个 bug 的镜像。

真实情况是：direction 可结构派生（有闭合条件），judgment 与 evidence 的分界没有可用的结构信号，因为分界是「谁产出的、回答哪个问题」，而这恰恰由 kind 这个名字承载。所以那张表不是 E4 所指的中心化枚举——它没有校验、未命中即 fallback 到 evidence，而 254 条片段正靠这个 fallback 正确落格。它是「非机械 kind 的清单」，方向是对的。

真正的缺口只有一处：写入时看不见投影结果，一个判断类新 kind 会静默落进 evidence 并从 in-force 集消失。修法是让 note.py 追加时回显派生出的 lane，代价三行，不加校验、不加噪音。
