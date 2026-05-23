---
id: 2026-05-23T08-43-11Z--operation-v1-0-2-trigger-checklist-rollout
time: 2026-05-23T08:43:11Z
kind: operation
refs: [2026-05-23T08-43-11Z--decision-explicit-trigger-checklist]
tags: [release, v1-0-2, fleet-refresh, protocol-improvement]
author: jing
projects_updated: 14
---
v1.0.2 patch shipped: explicit trigger checklist added to host operating
protocol.

Changed:
- migrate.py: install_agents_template suffix now contains the 8-trigger
  positive list and 5-item negative list, replacing the prior abstract
  "append for anything worth preserving" wording
- All 14 adopted projects on this device: AGENTS.md sentinel block
  replaced with the new content (priority notice retained)
- 13 external projects: tooling files refreshed (9 each, idempotent)
- Sula self: tooling source-of-truth (no copy needed)
- 34/34 tests still pass

Convention itself unchanged at v1.0 (frozen). Only the host protocol
text changed; agent BEHAVIOUR will converge across LLMs once they
read the new AGENTS.md at next boot.

Tag: sula-vector-v1.0.2.
