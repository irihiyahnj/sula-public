---
id: 2026-07-25T19-08-11Z--decision-convention-freeze
time: 2026-07-25T19:08:11Z
kind: decision
refs: [2026-07-25T19-04-14Z--goal-boot-force-10]
tags: [versioning, convention, docs]
summary: convention freeze 保护片段有效性与语义，不保护渲染器缺陷
---
修 boot 截断会改变 --for-agent 的输出文本。README 与 RELEASE-NOTES 此前写的是「every v1.0 fragment parses and renders identically across all v1.x releases」，按字面读，这次修复需要 v2.0。

不这么读。权威文件 docs/sula-vector-convention.md 的措辞本来就只承诺解析层：「Bump the convention version only when a previously-valid fragment file would no longer parse」。是 README 和 RELEASE-NOTES 这两份派生文档把承诺放宽到了渲染字节。以「渲染不变」为冻结对象会得出一个荒谬结论：一个丢失在force状态的视图必须永久保留，因为修它算破坏兼容——这与 Tier A 直接冲突，Tier A 说每个视图都是 render(fragments, conventions)，视图从属于片段，不是反过来。

因此：CONVENTION_VERSION 保持 1.1，无片段失效、无片段改变语义；这是渲染器缺陷修复，按工具补丁发布（v1.1.1）。同时把 README 与 RELEASE-NOTES 的措辞收回到与权威 spec 一致：冻结覆盖片段有效性与语义，不覆盖视图字节。legacy/examples/ 下的旧副本不动，它们是历史参考。

B5（byte-stable replay）不受影响：它约束的是同一 (fragments, conventions) 下多次渲染一致，本轮实测两次 --for-agent 输出 sha 相同。
