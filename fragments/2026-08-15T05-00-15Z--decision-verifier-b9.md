---
id: 2026-08-15T05-00-15Z--decision-verifier-b9
time: 2026-08-15T05:00:15Z
kind: decision
refs: [2026-08-15T02-46-41Z--correction-b8, 2026-07-25T19-11-42Z--goal-b8, 2026-05-23T05-50-10Z--decision-trust-is-reader-side]
tags: [b9, verifier, goals, boot]
summary: 共用 verifier 被提问：B9 唯一可机械化的强度子类
governs: tools/sula_vector/render.py
---
B9 要求目标带 verifier，从不要求 verifier 真的检验了那个声明。这是本轮之前唯一剩下的静默失败面：--view goals 打出 ✓，而没有任何东西说那个 ✓ 可能是空的。

「这条命令是否证明了这个 done_when」整体不可判定，不该假装能解决。但有一个子类是关于片段的事实而非关于代码的判断：**同一条 verifier 命令站在多个互不相关的目标背后，它对其中任何一个都不具备区分度**——它因为与任何单个 done_when 无关的原因通过。

实测本向量：5 个目标，4 个共用同一条 。goal-b8 就在其中——它的 done_when 承诺「跨会话继承」，而那条命令跑的测试套件里没有一条检查继承。唯一带独立 verifier 的目标（py_compile）不被标记。这个信号很锐利，不是词汇重叠那类猜测。

呈现位置分两级：--view goals 标记所有共用者；--for-agent 只列**已满足**的那些——那才是空 ✓ 正在被依赖的情况。目标还开着的时候没有人依赖任何东西，boot 保持沉默（C7）。

不做门。两个目标合法地断言同一个条件是可能的（例如「doctor 必须保持干净」）。所以这条只提问，答案归读者——与 decision-trust-is-reader-side 同一条边界：约定拦不住假话，只能让假话留痕。

这一条不解决 verifier 强度问题，只把它从不可见变成可见。剩下的残余仍在读者侧，是这层的边界。
