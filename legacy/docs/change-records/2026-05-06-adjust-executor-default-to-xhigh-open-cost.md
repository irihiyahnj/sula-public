# 2026-05-06 - Adjust Executor Default To Xhigh Open Cost

## Metadata

- Date: 2026-05-06
- Executor: Codex
- Branch: main
- Related commits: pending
- Status: implemented

## Background

After testing the first delegated executor route, the operator clarified that
executor quality matters more than a small fixed cost threshold. Many real tasks
are long-running, and stopping them only because a default dollar cap is reached
undermines the purpose of delegation.

## Analysis

The useful control is not a hard cost stop. The useful control is visibility:
show the executor model, depth, workspace, elapsed time, and reported cost while
keeping the expensive host model focused on planning and review.

## Chosen Plan

- Default executor reasoning effort to `xhigh`.
- Treat `executor_max_cost_cents = 0` as open cost, meaning no hard cost cap.
- Keep the bounded executor contract visible in `session start` and compact
  orchestration status.
- Preserve optional finite cost caps for projects that explicitly want them.

## Execution

- Updated the agent routing default executor effort from `high` to `xhigh`.
- Updated executor configure so the selected executor effort is also remembered
  as the executor contract default effort.
- Added manifest schema support for non-negative integer cost caps.
- Updated compact status and session display to render open-cost contracts
  clearly instead of showing `$0.00`.
- Updated docs and regression tests.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_shell_runner_receives_bounded_executor_contract_and_compact_budget tests.test_sula.SulaCliTests.test_shell_runner_receives_reasoning_effort_and_compact_status_line tests.test_sula.SulaCliTests.test_agent_routing_configure_remembers_executor_choice_until_replaced -v`

## Rollback

Revert the default effort and cost-cap semantics. Projects would return to the
0.18.8 behavior of `high` executor default effort and a finite `$0.30` default
cost budget.

## Data Side-effects

The local Sula project executor route was updated to `deepseek-v4-flash /
xhigh` with open cost. This project-local `.sula/project.toml` change remains
uncommitted and is not part of Sula Core release truth.

## Follow-up

- Make local executor wrappers report periodic cost checkpoints when the
  underlying CLI supports streaming usage metadata.

## Architecture Boundary Check

- Highest rule impact: preserved. This changes reusable Sula routing policy
  defaults without storing provider secrets or project-owned business truth.
- Sync impact: adopted projects inherit the completion-first default while
  retaining the ability to set finite local caps.
