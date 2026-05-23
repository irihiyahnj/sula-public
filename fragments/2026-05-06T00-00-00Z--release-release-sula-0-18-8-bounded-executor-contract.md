---
id: 2026-05-06T00-00-00Z--release-release-sula-0-18-8-bounded-executor-contract
time: 2026-05-06T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-06-release-sula-0-18-8-bounded-executor-contract.md
---
# Release Sula 0.18.8 bounded executor contract

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.8` so adopted projects receive
bounded executor contracts and compact budget visibility for delegated runner
routes.

## Risks

- Existing runner adapters remain backward compatible, but custom runners should
  be updated to read the new contract fields if they want budget-aware behavior.
- Sula can enforce runtime timeout locally, but token/cost limits are currently
  post-run checks unless the local runner streams progress or stops itself.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_shell_runner_receives_bounded_executor_contract_and_compact_budget tests.test_sula.SulaCliTests.test_shell_runner_receives_reasoning_effort_and_compact_status_line tests.test_sula.SulaCliTests.test_role_aware_runner_request_and_visible_active_state -v`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.8`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.8`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `.sula/kernel.toml`,
  `site/sula.json`, `site/launch/bootstrap.py`, changelog, and release notes to
  `0.18.7` / `v0.18.7`.
- Revert the bounded executor contract implementation if custom runners regress.

## Follow-up

- Teach the local DeepSeek/Claude wrapper to consume the contract directly and
  run with non-interactive permissions inside copy workspaces.
