---
id: 2026-05-23T05-25-40Z--decision-richen-changes-summary-mark
time: 2026-05-23T05:25:40Z
kind: decision
refs: [2026-05-23T05-20-55Z--decision-add-turn-mark-view]
tags: [visibility, turn-mark, ux]
author: jing
---
Replaced the one-line "[sula] +N (counts...)" mark with a multi-line block
that lists each appended fragment by kind + 120-char summary, with ✓/✗
markers for verification-fact fragments. The default human output of
`render --view changes-summary` is now this block; --json keeps the rich
structured form (per-fragment id/kind/summary/refs/passed).

Rationale: "+N (4 decision...)" is too abstract — the user cannot tell what
those decisions are about. The richer block carries actual content while
still respecting C7 (silent on empty turns) and adds zero new state.
