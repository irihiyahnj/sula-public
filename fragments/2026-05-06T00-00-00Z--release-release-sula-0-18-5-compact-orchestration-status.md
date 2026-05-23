---
id: 2026-05-06T00-00-00Z--release-release-sula-0-18-5-compact-orchestration-status
time: 2026-05-06T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-06-release-sula-0-18-5-compact-orchestration-status.md
---
# Release Sula 0.18.5 Compact orchestration status

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.5` so adopted projects can receive compact orchestration status and executor effort routing through normal Sula upgrade flow.

The release promotes a reusable workflow that first appeared as a MedFlow-local need: operators need a concise English tool line showing whether Sula ran, which model/depth handled the main session and executor route, how many tasks are done, what workspace mode was used, and whether there is remaining work.

## Risks

- Compact context display currently reports a placeholder when the host environment does not expose context-window usage.
- Runner effort mapping is intentionally conservative: Claude-style routes map `xhigh` to `max`; other routes receive the Sula effort label directly.
- Existing local project wrappers may still exist until each adopted project syncs and removes them deliberately.

## Verification

- Final gate passed on 2026-05-06:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula -v`
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py canary verify --project-root . --all`
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py doctor --project-root . --strict`
  - `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py check --project-root .`
  - `git diff --check`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.5`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.5`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`, `site/launch/bootstrap.py`, and tests to `0.18.4` / `v0.18.4`.
- Revert compact status and executor effort routing changes if downstream runner routing behavior regresses.

## Follow-up

- After MedFlow syncs to this release, remove any project-local Sula wrapper that duplicates compact status behavior.
