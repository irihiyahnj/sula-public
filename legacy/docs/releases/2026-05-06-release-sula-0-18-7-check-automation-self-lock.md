# Release Sula 0.18.7 check automation self lock

## Metadata

- date: 2026-05-06
- executor: Codex with DeepSeek Flash executor assistance
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.7` so adopted projects receive
the `sula check` automation self-lock fix.

## Risks

- This patch intentionally ignores only Sula's own `sula-check` automation
  repair task ids during check gating. Normal project tasks and real pending
  runs continue to block `check`.
- Projects with stale generated state may still need `memory digest` before
  `check` passes.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_automation_check_failure_creates_intent_without_manual_trigger tests.test_sula.SulaCliTests.test_check_ignores_sula_check_automation_repair_self_lock tests.test_sula.SulaCliTests.test_automation_default_dispatches_low_risk_intent_to_dry_run -v`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.7`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.7`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`,
  `site/launch/bootstrap.py`, changelog, and release notes to `0.18.6` /
  `v0.18.6`.
- Revert the orchestration check filter if the automation repair intent should
  return to strict check gating.

## Follow-up

- Tighten the local executor runner prompt and permissions so future delegated
  work does not spend excessive turns on Claude Code permission prompts.
