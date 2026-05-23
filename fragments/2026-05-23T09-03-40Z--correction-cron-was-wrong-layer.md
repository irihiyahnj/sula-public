---
id: 2026-05-23T09-03-40Z--correction-cron-was-wrong-layer
time: 2026-05-23T09:03:40Z
kind: correction
refs: [2026-05-23T08-53-58Z--decision-auto-update-skill-and-fleet-cron, 2026-05-23T08-55-10Z--operation-fleet-auto-refresh-cron-installed]
tags: [self-correction, philosophy, c2, b4, cron-removed]
author: jing
broken_decision: "installing a daily cron entry to auto-refresh all 14 projects"
correct_layer: "boot-time check inside the host operating protocol — update only when work is about to begin"
---
The v1.0.3 cron-based fleet auto-refresh was over-engineered. Operator
caught the wrong-layer move:

  "仅仅为了更新这个会话，而去开启一个 Cron 服务，是不是会变得太复杂了？
  这会影响我们的哲学吗？"

Yes, it does. The cron pattern violated:

- B4 (no daemon / no kernel-as-truth): cron is OS-level not Sula-level,
  but its function — "Sula running in the background" — is exactly what
  B4 was meant to forbid in spirit.
- C5 (minimal interaction, one action per change): "install a cron and
  it silently fires 365 times/year" is structurally the opposite of
  "one action per change".
- C7 (no churn): polling 14 projects × 10 files daily, even when no
  agent is working, is wasted effort. Most days nothing changes; cron
  still runs.
- C2 (find the essential dimension): updates only matter when an
  agent is about to operate. The right layer is the boot moment, not
  a fixed schedule.

Fix:

1. Removed the cron entry from this device's crontab. Pre-existing
   cron (medflow/app3 evidence collector) preserved.
2. Removed tools/sula_vector/auto-refresh-fleet.sh from canonical
   (operator-level fleet wrapper was only useful for the cron pattern).
3. Updated AGENTS.md host operating protocol: "At session start" now
   has 4 steps:

   1. Note ISO time
   2. Run auto-update-from-canonical.py --quiet (best-effort refresh)
   3. Run render --for-agent
   4. Treat output as authoritative

   Update happens at the moment work begins, not on a schedule.
4. Bulk-applied the new protocol to all 14 adopted projects on this
   device.
5. The auto-update skill itself is RETAINED — it is now invoked at
   session start by every host LLM. Updates happen exactly when work
   is about to start; idle projects consume zero resources.

The skill, the wrapper-script update-from-canonical.sh, and the
manual-invocation pattern remain available for operators who want
explicit control. Only the daily-cron pattern was removed.

This correction itself is a live demonstration of C2 ("don't fight
at the wrong layer; back off and find the right one") and C7 ("no
churn — only do work when it's truly needed"). It also confirms the
trust model: when a wrong design is shipped, the fix is append a
correction + apply the structural change, with full audit trail.
