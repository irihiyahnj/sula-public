---
id: 2026-05-23T09-03-40Z--decision-update-check-at-boot-not-cron
time: 2026-05-23T09:03:40Z
kind: decision
refs: [2026-05-23T09-03-40Z--correction-cron-was-wrong-layer, 2026-05-23T05-25-40Z--decision-enshrine-host-operating-protocol]
tags: [boot-protocol, auto-update, philosophy, c2]
author: jing
---
Crystallised: **tooling auto-update happens at session boot, not on a
schedule.**

Why boot is the right layer:
- An update only matters if an agent is about to use the tooling.
- An idle project doesn't need fresh tooling — fetching daily wastes
  effort (C7) and approximates a daemon (B4).
- The boot moment is when the agent demands a working environment;
  it's the natural checkpoint.
- Network failures or canonical unavailability gracefully degrade
  to "use what you have"; agents still proceed.

Implementation:
- AGENTS.md "At session start" step 2 invokes
  auto-update-from-canonical.py --quiet
- Skill aggregate-hashes 10 tooling files; if drift detected, runs
  migrate.py to refresh; if not, silent
- Network unreachable → silent skip (exit 0)
- Actual updates emit kind:operation in the project (B8)

Cost: each session boot adds 10 HTTP GETs to raw.githubusercontent.com.
Bounded latency (10s timeout). For most projects most sessions, this
is sub-second. For long sessions, the cost is amortised once.

This pattern is preferred over cron because it satisfies all of:
- B4 (no background process pretending to be substrate)
- C2 (work happens at the right layer — when work begins)
- C5 (one action per session boot covers update + boot)
- C7 (idle projects do zero work)
- B7 (substrate handles networking; Sula doesn't manage schedules)
- Self-contained (each project's skill handles itself; no shared
  device-level orchestrator)

Operators who want manual fleet refresh can still use:
  python3 tools/sula_vector/skills/auto-update-from-canonical.py --project-root <path>
or
  tools/sula_vector/update-from-canonical.sh --project-root <path>

These are operator one-shots. The cron pattern is no longer
recommended.
