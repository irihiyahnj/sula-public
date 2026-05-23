---
id: 2026-05-07T00-00-00Z--decision-add-autopilot-code-task-dispatch
time: 2026-05-07T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-07-add-autopilot-code-task-dispatch.md
---
# Add Autopilot Code Task Dispatch

## Metadata

- date: 2026-05-07
- executor: Sula-supervised DeepSeek Flash executor with Codex host review
- branch: main
- related commit(s): pending
- status: implemented

## Background

Sula already routed natural-language fleet upgrade intents through `auto`, but an implementation goal that referenced a local goal file still returned `unknown`. That meant the host chat model had to do mechanical planning and patch execution instead of delegating low-risk code work through Sula's executor route.

## Analysis

- Fleet upgrade routing must remain first because it has a deterministic maintenance path.
- Unknown goals should still block rather than pretending broad language understanding is solved.
- Low-risk implementation and fix goals can use the existing automation and orchestration pipeline instead of a new dispatcher.
- Host review remains mandatory because model execution does not replace verification evidence.

## Chosen Plan

- Classify scoped implementation/fix goals and `.sula/local/` goal-file references as `code.task`.
- Make `auto --dry-run` return a compact planned task without dispatching an executor.
- Make non-dry-run code tasks append an automation intent and dispatch through the existing orchestration policy gates.
- Preserve fleet upgrade routing precedence.

## Execution

- Updated `scripts/sula.py` with `code.task` intent classification and dispatch handling.
- Added tests for English implementation goals, Chinese implementation goals, fix goals, non-dry-run dispatch, and fleet upgrade preservation.
- Documented the code-task route in `docs/reference/autopilot-intent-router.md`.
- Added this change record and updated the docs map/template for the completion-first whitepaper.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_auto_code_task_intent_dispatches_to_orchestration tests.test_sula.SulaCliTests.test_auto_upgrade_intent_delegates_project_upgrade_to_executor tests.test_sula.SulaCliTests.test_auto_upgrade_intent_unchanged_by_code_task_routing -v`
- `python3 scripts/sula.py auto --project-root . --intent "执行 .sula/local/goal-completion-first-whitepaper-implementation.md 中的 Sula Completion-First Agent Operating System 落地任务" --dry-run --json`

## Rollback

- Revert the `code.task` branch in `classify_auto_intent` and `auto_intent`.
- Remove the added code-task dispatch tests.
- Revert the autopilot reference and docs map additions if the route is withdrawn.

## Data Side-effects

- A local orchestration task and run history were recorded for `completion-first-auto-code-task-dispatch`.
- Executor metrics observed during implementation:
  - permission-blocked run: 51,335 tokens, USD 0.149971
  - successful retry: 1,753,144 tokens, USD 1.489388
- The run exposed that a nested copy workspace can still let ClaudeCode discover and mutate the parent Git root.

## Follow-up

- Harden workspace isolation so a copy workspace cannot accidentally mutate the parent repository.
- Improve compact status so a long-running subprocess appears as the current active run rather than showing the previous latest run.
- Add executor preflight for ClaudeCode permission mode and tool allowlist correctness before dispatch.

## Architecture Boundary Check

- highest rule impact: preserved. The change extends Sula's reusable operating-system layer and does not add project-specific business truth.
- managed/project split: preserved. Local executor credentials and wrapper configuration remain under `.sula/local` or machine environment.
- dependency impact: none. No SDK or third-party package is required by Sula Core.
