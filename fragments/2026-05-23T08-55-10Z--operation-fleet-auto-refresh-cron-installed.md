---
id: 2026-05-23T08-55-10Z--operation-fleet-auto-refresh-cron-installed
time: 2026-05-23T08:55:10Z
kind: operation
refs: [2026-05-23T08-53-58Z--decision-auto-update-skill-and-fleet-cron, 2026-05-23T08-53-58Z--operation-v1-0-3-auto-update-rollout]
tags: [cron, automation, fleet, this-device]
author: jing
device: jing's-laptop
schedule: "0 3 * * *"
---
Daily fleet auto-refresh cron installed on this device.

Crontab line:

  0 3 * * * /home/jing/Project/projectdev/sula/tools/sula_vector/auto-refresh-fleet.sh --quiet >> /home/jing/.sula-fleet-refresh.log 2>&1

Behaviour:
- 03:00 local time daily, scans /home/jing for AGENTS.md files containing
  the <!-- sula-vector --> sentinel
- For each discovered project, invokes that project's own
  auto-update-from-canonical.py skill
- Skill aggregate-hashes 10 tracked tooling files locally and remotely;
  if equal → silent no-op; if drift → clones canonical and runs migrate.py
- Each actual update emits a kind:operation fragment IN THE UPDATED
  PROJECT (not in this device's Sula vector)
- Errors and updates logged to /home/jing/.sula-fleet-refresh.log

Operator scope: this device only. Other devices running the same
projects can install their own cron at their own cadence — entirely
their choice. The skill itself ships with each project (self-contained).

Verification at install:
- One-shot run: 14/14 projects already current, updated=0, errors=0
- python3 at /usr/bin/python3, git at /usr/bin/git (cron-reachable)
- Existing crontab entry (medflow/app3 daily evidence collector)
  preserved alongside

Disable: edit crontab with 'crontab -e' and remove the line, OR remove
the auto-refresh-fleet.sh script. Each adopted project's auto-update
skill remains available for manual invocation regardless.
