---
id: 2026-05-01T00-00-00Z--decision-zzzzz-add-automation-kernel-for-event-driven-orchestration
time: 2026-05-01T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-01-zzzzz-add-automation-kernel-for-event-driven-orchestration.md
---
# Add Automation Kernel For Event Driven Orchestration

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

The initial orchestration implementation still depended too heavily on explicit user commands such as `orchestration trigger` or `orchestration run`. That made the control plane useful, but it did not satisfy Sula's operating-system principle: connected project surfaces should naturally produce follow-up work without requiring users to remember a special trigger ritual.

## Analysis

- Manual trigger commands are still useful for backfill, tests, and debugging, but they cannot be the primary automation path.
- Sula needs a layer above orchestration that watches normal Sula entrypoints, records operational events, classifies useful follow-up intent, and exposes those intents as tasks.
- Automatic dispatch must remain policy-gated because Sula is reusable across adopted projects with different trust levels.
- The default should be automatic but non-mutating: observe, classify, plan, and dispatch by default into the dry-run runner; real execution still requires explicit runner configuration and must pass risk and approval gates.

## Chosen Plan

- Add a first-class `[automation]` manifest section.
- Default automation to `enabled = true`, `mode = "execute"`, `auto_intake = true`, `auto_plan = true`, and `auto_dispatch = true`.
- Record events under `.sula/state/automation/events.jsonl`.
- Store deduped automation intents under `.sula/state/automation/intents.jsonl`.
- Make automation intents appear as orchestration tasks without requiring a local task file or a manual trigger.
- Allow automatic dispatch only when automation execute mode, auto-dispatch, orchestration enabled, risk ceiling, and approval-category gates all pass; the default runner remains dry-run.

## Execution

- Added manifest defaults, schema fields, config payloads, validation, example manifest updates, and docs for `[automation]`.
- Added automation event, intent, latest-state, and status payload helpers.
- Wired `check`, `doctor`, `status`, `query`, `sync`, `artifact locate`, and `artifact refresh` into the automation observer.
- Added event classifiers for failed checks, failed doctors, provider freshness errors, status truth-source risks, and generic failed Sula commands.
- Merged automation intents into orchestration task loading while keeping manual `orchestration trigger` available for debugging and backfill.
- Preserved safety gates so automatic dispatch cannot bypass risk ceilings, approval categories, orchestration enablement, or runner closeout requirements.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_automation_check_failure_creates_intent_without_manual_trigger tests.test_sula.SulaCliTests.test_automation_default_dispatches_low_risk_intent_to_dry_run tests.test_sula.SulaCliTests.test_automation_assist_mode_keeps_intent_queued -v`

## Rollback

- Remove `[automation]` from manifest defaults, schema, docs, and config payloads.
- Remove automation event observation calls from normal Sula entrypoints.
- Keep existing manual `orchestration intake`, `orchestration trigger`, and `orchestration run` commands intact.

## Data Side-effects

- Adopted projects can now contain runtime automation state under `.sula/state/automation/`.
- No external provider writes, remote execution, or project business truth mutation is introduced by the default dry-run dispatch mode.
- Execute-mode dispatch remains opt-in and still records runs under `.sula/state/orchestration/`.

## Follow-up

- Add richer event classifiers as real project workflows expose more recurring failure and freshness patterns.
- Add long-running runner streaming and cancellation propagation after the first real app-server canary.
- Consider a future provider event polling adapter after a real external task source needs continuous sync.

## Architecture Boundary Check

- highest rule impact: preserved. Sula owns operational event and intent state, while project-owned task truth, provider artifacts, and domain decisions remain outside centrally managed templates.
