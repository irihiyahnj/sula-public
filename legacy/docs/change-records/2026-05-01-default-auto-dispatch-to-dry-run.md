# Default auto dispatch to dry-run

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): uncommitted working-tree change
- status: draft

## Background

Sula's full-automation goal is weakened if users must remember when to manually enable automatic dispatch. The default should make Sula visibly act when it detects eligible low-risk work, while still preserving the boundary between automatic coordination and real project mutation.

## Analysis

- `auto_dispatch = true` alone is insufficient because the implementation only dispatches automatically when `[automation].mode = "execute"`.
- Defaulting to execute mode is acceptable only because the default orchestration runner remains `dry-run`.
- Real mutation remains behind explicit real-runner configuration, low-risk ceilings, approval-category checks, and closeout evidence.
- Human-readable activity feedback is the user-awareness mechanism: users should see that Sula recorded an event, created an intent, and dispatched a dry-run record without needing to know the trigger command.

## Chosen Plan

- Default `[automation].mode` to `execute`.
- Default `[automation].auto_dispatch` to `true`.
- Keep `[orchestration].runner = "dry-run"` as the default runner boundary.
- Update documentation and tests so the default is automatic dry-run dispatch, not manual opt-in dispatch.
- Preserve explicit `assist` mode as the project-level downgrade path for teams that want intent creation without automatic run records.

## Execution

- Updated Sula defaults in `scripts/sula.py`.
- Updated the example manifest and Sula Core's own manifest.
- Updated README, manifest reference docs, orchestration plan docs, release notes, and related change records.
- Updated automation tests to prove default low-risk events dispatch to dry-run and explicit assist mode keeps intent queued.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 scripts/sula.py doctor --project-root . --strict --json`
- `python3 scripts/sula.py orchestration doctor --project-root . --json`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_automation_check_failure_creates_intent_without_manual_trigger tests.test_sula.SulaCliTests.test_automation_default_dispatches_low_risk_intent_to_dry_run tests.test_sula.SulaCliTests.test_automation_assist_mode_keeps_intent_queued tests.test_sula.SulaCliTests.test_orchestration_defaults_to_enabled_dry_run_records`

## Rollback

- Set default automation mode back to `assist`.
- Set default `auto_dispatch` back to `false`.
- Existing projects can locally set `[automation].mode = "assist"` to keep automatic intent creation without dispatching runs.

## Data Side-effects

- Default projects can create more `.sula/state/orchestration/runs.jsonl` entries because eligible low-risk automation intents now dispatch to dry-run automatically.
- No provider writes, release actions, destructive actions, or real runner mutations are introduced by this default.
- Human-readable command output may show automatic dispatch feedback more often.

## Follow-up

- Add a retention or compaction command for high-volume automation and orchestration ledgers.
- Consider a concise `automation status` command that summarizes recent automatic dispatches for users who want an explicit control panel.

## Architecture Boundary Check

- highest rule impact: preserved. The change makes Sula more automatic by default, but project-owned business truth remains outside managed templates and real mutation remains behind explicit runner configuration plus risk and approval gates.
