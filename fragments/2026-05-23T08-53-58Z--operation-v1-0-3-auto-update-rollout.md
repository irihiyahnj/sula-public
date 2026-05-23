---
id: 2026-05-23T08-53-58Z--operation-v1-0-3-auto-update-rollout
time: 2026-05-23T08:53:58Z
kind: operation
refs: [2026-05-23T08-53-58Z--decision-auto-update-skill-and-fleet-cron]
tags: [release, v1-0-3, auto-update, fleet]
author: jing
---
v1.0.3: per-project auto-update skill + operator-level fleet refresh
wrapper.

New files in canonical:
- tools/sula_vector/skills/auto-update-from-canonical.py (175 lines)
- tools/sula_vector/auto-refresh-fleet.sh (77 lines)

migrate.py: install_tooling now also copies the new skill into each
project (10 files total per project, was 9).

All 14 adopted projects on this device received the new skill via a
fleet refresh (re-running migrate.py, idempotent).

Aggregate-hash compare verified across the fleet: all 14 projects
report "already current" against canonical.
