# Release Sula 0.18.9 xhigh open cost executor

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.9` so adopted projects receive a
completion-first executor default: `xhigh` executor reasoning effort with open
cost visibility rather than a hard default dollar cap.

## Risks

- Open cost means Sula will not block a long executor run solely due to reported
  spend. Operators should still monitor compact status and runner metrics.
- Projects that need strict cost caps can explicitly set
  `executor_max_cost_cents` to a positive value.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_shell_runner_receives_bounded_executor_contract_and_compact_budget tests.test_sula.SulaCliTests.test_shell_runner_receives_reasoning_effort_and_compact_status_line tests.test_sula.SulaCliTests.test_agent_routing_configure_remembers_executor_choice_until_replaced -v`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.9`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.9`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `.sula/kernel.toml`,
  `site/sula.json`, `site/launch/bootstrap.py`, changelog, and release notes to
  `0.18.8` / `v0.18.8`.
- Revert the executor default effort and open-cost semantics if projects need
  finite cost caps by default.

## Follow-up

- Add streaming usage checkpoints once local runner adapters can expose
  incremental token/cost data.
