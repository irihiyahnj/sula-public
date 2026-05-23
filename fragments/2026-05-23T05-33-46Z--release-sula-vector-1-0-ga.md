---
id: 2026-05-23T05-33-46Z--release-sula-vector-1-0-ga
time: 2026-05-23T05:33:46Z
kind: release
version: "1.0"
status: GA
refs: [2026-05-23T05-14-14Z--decision-adopt-sula-vector-convention, 2026-05-23T05-14-14Z--decision-enshrine-tier-a-e-principles, 2026-05-23T05-14-14Z--decision-skills-extension-model, 2026-05-23T05-20-55Z--decision-add-turn-mark-view, 2026-05-23T05-25-40Z--decision-enshrine-host-operating-protocol]
tags: [release, ga, ship-frozen]
author: jing
---
Sula Vector v1.0 GA shipped 2026-05-23.

Convention frozen: project_view = render(fragments, conventions). Tier A–E
principles enshrined as kind:principle fragments and prepended at every
agent boot. Host operating protocol (read --for-agent at session start;
display --view changes-summary at end of turn) installed in adopting
projects' AGENTS.md via migrate.py.

Reference implementation:
- render.py (~590 lines, stdlib-only, 8 views)
- migrate.py (~449 lines, idempotent legacy-Sula migrator)
- skills/verifier-shell.py (122 lines)
- skills/scheduler.py (145 lines)
- skills/llm-dispatcher.py (168 lines)
- AGENTS.md template (99 lines)
- convention spec (422 lines)
- test suite (539 lines, 34 tests)
Total tooling: ~2530 lines, no third-party deps.

Verification at ship:
- 34/34 tests pass in 1.8s
- Sula self vector (327 fragments) renders byte-stable (5849 bytes)
- 1terminal vector (28 fragments) renders byte-stable (4803 bytes)
- migrate.py idempotent across 3 consecutive runs in both repos
- All 3 reference skills exercised end-to-end on real fragments

Adoption: see tools/sula_vector/RELEASE-NOTES.md.
