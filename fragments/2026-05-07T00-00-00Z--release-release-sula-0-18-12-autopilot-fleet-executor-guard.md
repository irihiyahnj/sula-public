---
id: 2026-05-07T00-00-00Z--release-release-sula-0-18-12-autopilot-fleet-executor-guard
time: 2026-05-07T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-07-release-sula-0-18-12-autopilot-fleet-executor-guard.md
---
# Release Sula 0.18.12 Autopilot Fleet Executor Guard

## Metadata

- date: 2026-05-07
- executor: Codex host with local Sula validation
- branch: main
- status: ready

## Scope

Sula 0.18.12 ships the first practical commandless autopilot workflow:
natural-language Sula upgrade/update/sync goals can route to an
executor-required fleet upgrade instead of being performed directly by the host
chat model.

Included changes:

- `auto` command for natural-language maintenance classification
- `fleet upgrade` for discovered Sula project upgrades under a filesystem scope
- `fleet status --compact` for a Sula-owned status bar
- executor-required guard for fleet upgrades
- `shell-command` fleet executor dispatch using `SULA_FLEET_TASK_JSON`
- managed AI instruction updates so new and synced projects know to call `auto`

## Risks

- The first classifier is intentionally narrow; unrecognized natural-language
  goals block instead of guessing.
- Real fleet execution currently requires a configured project-local
  `shell-command` wrapper.
- Host models still need to respect the managed instruction files; Sula blocks
  executor-required fleet work when they call `auto`, but it cannot prevent an
  agent from bypassing Sula entirely.

## Verification

- targeted autopilot delegation and blocking tests passed
- supervised executor retry regression test passed
- Python compile checks passed for `scripts/sula.py`, `tests/test_sula.py`, and
  `site/launch/bootstrap.py`
- `site/sula.json` parses as JSON

## Rollback

Revert the 0.18.12 commit and tag, then return `VERSION`, `.sula/version.lock`,
`.sula/kernel.toml`, `site/sula.json`, and `site/launch/bootstrap.py` to
0.18.11 references.

## Follow-up

- Use real project fleet runs to measure speed, cost, and code quality.
- Add more autopilot workflows only after their executor packets and validation
  contracts are explicit.
