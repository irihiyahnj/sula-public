---
id: 2026-05-23T08-53-58Z--decision-auto-update-skill-and-fleet-cron
time: 2026-05-23T08:53:58Z
kind: decision
refs: [2026-05-23T08-43-11Z--decision-explicit-trigger-checklist, 2026-05-23T05-59-09Z--decision-each-project-self-contained]
tags: [auto-update, fleet, cron, zero-touch, skill]
author: jing
---
Operator asked: "can projects periodically check the canonical repo and
update themselves automatically?"

Answer: yes, via a per-project skill + an operator-level scheduling layer.

Per-project skill: tools/sula_vector/skills/auto-update-from-canonical.py
- Aggregates SHA-256 of all 10 tracked tooling files locally
- Fetches each remote counterpart from raw.githubusercontent.com
- If aggregate hashes match → silent no-op (Tier C7)
- If they differ → clones canonical to temp, runs migrate.py, verifies
  post-update aggregate hash matches remote, emits kind:operation fragment
- Resilient to transient network failure (exits 0 on canonical unreachable)
- Cron-friendly --quiet mode

Why aggregate-hash, not single-file: an earlier draft compared only
render.py; it would have missed updates that touch only skills or docs.
Aggregate-hash catches any change to any tracked file. Cost: 10 HTTP
GETs per check (well within GitHub rate limits at daily cadence).

Operator scheduling: tools/sula_vector/auto-refresh-fleet.sh
- Discovers all Sula vector projects on a device by scanning for
  AGENTS.md with the <!-- sula-vector --> sentinel
- Runs each project's own auto-update skill
- Filters out backups/archives/sandbox copies

Invocation: cron, launchd, systemd timer, or manual. The skill is
in each project (self-contained); the fleet wrapper is operator-
level (this device's choice, not Sula's).

This satisfies the user's request for zero-touch automation without
violating principles:
- B7 substrate handles: cron is substrate, not Sula
- C7 no churn: aggregate-hash compare is cheap; no work when current
- B2 no implicit state: any update emits a kind:operation fragment;
  the update itself is recorded as project truth
- Self-contained: each project has its own skill copy; the cron just
  invokes them

Each device's operator decides the cadence. Each project's owner can
disable on their device by removing the cron entry, with no effect on
the project itself.
