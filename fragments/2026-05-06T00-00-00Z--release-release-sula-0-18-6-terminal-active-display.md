---
id: 2026-05-06T00-00-00Z--release-release-sula-0-18-6-terminal-active-display
time: 2026-05-06T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-06-release-sula-0-18-6-terminal-active-display.md
---
# Release Sula 0.18.6 terminal active display

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.6` so adopted projects inherit
the corrected orchestration status semantics. Terminal runs now remain in
history after closeout instead of being presented as the active execution slot.

## Risks

- Projects that relied on the previous compact status phrasing will need to
  adjust their local wrappers if they mirrored Sula output.
- Existing adopted projects remain compatible, but they will not see the new
  status wording until they sync this release.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_session_start_surfaces_visible_execution_and_unknown_host_model tests.test_sula.SulaCliTests.test_session_start_does_not_show_terminal_run_as_active -v`
- `python3 scripts/sula.py session start --project-root .`
- `python3 scripts/sula.py orchestration status --project-root . --compact`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.6`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.6`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`, `site/launch/bootstrap.py`, and release notes to `0.18.5` / `v0.18.5`.
- Revert the orchestration status visibility filter if the idle display needs to
  return to the previous phrasing.

## Follow-up

- Remove any downstream project-local wrappers that duplicated active-status
  handling after syncing to this patch.
