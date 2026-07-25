---
id: 2026-07-25T22-52-40Z--decision-tier-tier
time: 2026-07-25T22:52:40Z
kind: decision
refs: [2026-07-25T22-46-45Z--correction-fleet]
tags: [render, principle, defect, silent-loss]
summary: tier 是原则的分组提示，不是过滤条件；无 tier 的项目原则此前在所有视图里不可见
---
view_principles 里是 if tier in grouped——tier 不属于五档就整条丢弃。而 boot 的判断列表又显式排除 kind == principle（因为原则本该在自己的块里全文渲染）。两处排除叠加的结果是：一条没有 tier 的 principle 片段在 --for-agent 和 --view principles 里都不出现，文件躺在 fragments/ 里但任何视图都看不到它。

这比 n=10 严重。n=10 是截断，被漏掉的判断至少在 --view effective 里查得到；这个是彻底隐形，没有任何视图能显示它。

发现过程：给钱王炽落判断时写了一条项目原则「她的动机不是钱，所以议价姿态本身就是风险——不要压 220／180」。那是那个项目最要命的一条判断，丢掉它可能直接毁掉合作。落盘后我核对片段计数对不上，才查出它根本没进 boot。cn6 自己那条 principle-toto-understanding-vs-safety 同样无 tier，同样从 v1.0 时代起就一直不可见。

修法取维度：tier 用来分组，从不用来过滤。不属于五档的归入 project 桶，以「Project principles」为标题渲染在 Tier A–E 之后。五档的输出字节不变（把 'Tier ' 从格式串移进 TIER_TITLES 的值）。项目自己的原则是一等公民而不是例外——真实项目的原则本来就不该套 Tier A–E 的壳。
