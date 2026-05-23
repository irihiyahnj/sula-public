---
id: 2026-05-23T05-14-14Z--decision-enshrine-tier-a-e-principles
time: 2026-05-23T05:14:14Z
kind: decision
refs: [2026-05-23T05-14-14Z--decision-adopt-sula-vector-convention]
tags: [principles, enforcement, tier-a-e]
author: jing
---
The five tiers of design principles (A highest rule, B invariants, C
aesthetics, D discipline, E anti-patterns) ship as kind:principle fragments
in every adoption. `render --for-agent` prepends them to every agent boot,
so any LLM on any device sees them immediately. `render --view principles`
exposes them for human/CI inspection.

Modifying a principle requires appending a kind:decision with refs back —
supersession is visible in every subsequent render.
