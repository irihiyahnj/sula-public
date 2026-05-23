---
id: 2026-05-01T00-00-00Z--decision-zzzz-add-remote-verification-and-codex-runners
time: 2026-05-01T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-01-zzzz-add-remote-verification-and-codex-runners.md
---
# Add Remote Verification And Codex Runners

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

Sula orchestration could already normalize local, provider-document, and provider-API tasks, then evaluate closeout evidence through dependency-light reference checks. The remaining mainline gaps were a real Codex runner boundary and an optional way to require remote truth for PR/provider references before accepted closeout.

## Analysis

- Sula Core should not vendor an SDK, force a remote service, or make credentials mandatory for every adopted project.
- Runner adapters should use one stable request/response contract so projects can swap local SDK commands, app servers, or future runners without changing task truth.
- Remote verification must be policy-controlled because some projects need credential-backed enforcement while others only need reference capture.
- Tests need fixture-backed paths so the feature is verifiable without live GitHub or Google credentials.

## Chosen Plan

- Add `remote_verification_policy` with `reference-only`, `opportunistic`, and `required` modes.
- Keep the default as `opportunistic`: verify through fixtures or credentials when available, but do not block closeout solely because credentials are absent.
- Implement PR verification through fixture files and optional GitHub API lookup.
- Implement provider reference verification through the existing provider adapter boundary.
- Implement `codex-sdk` as a JSON-over-stdin command runner.
- Implement `codex-app-server` as an HTTP JSON runner with optional bearer-token lookup through `runner_token_env`.

## Execution

- Added manifest defaults, schema fields, config accessors, payload output, and policy validation for remote verification and Codex runner endpoint settings.
- Added closeout remote verification metadata and `unverified_remote_links` enforcement when policy is `required`.
- Added PR fixture/GitHub verification and provider adapter verification helpers.
- Added Codex runner request payload construction and normalized response merging for status, summary, touched files, validation evidence, links, and metrics.
- Updated README, manifest reference docs, orchestration plan docs, and status handoff.
- Added unit coverage for `codex-sdk`, `codex-app-server`, and required remote PR verification.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_codex_sdk_runner_collects_json_evidence tests.test_sula.SulaCliTests.test_orchestration_codex_app_server_runner_collects_json_evidence tests.test_sula.SulaCliTests.test_orchestration_closeout_requires_remote_pr_verification_when_configured tests.test_sula.SulaCliTests.test_orchestration_closeout_resolves_provider_artifacts_and_pr_urls -v`
- `python3 -m unittest discover -s tests -v` passed, 109 tests in 879.224s.
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py doctor --project-root . --strict --json`
- `python3 scripts/sula.py check --project-root . --json`
- `python3 scripts/sula.py orchestration doctor --project-root . --json`
- `python3 scripts/sula.py portfolio orchestration --portfolio-root ~/.sula/portfolio --json`

## Rollback

- Remove `remote_verification_policy`, `runner_endpoint`, and `runner_token_env` from the manifest schema, defaults, docs, and config payload.
- Revert `codex-sdk` and `codex-app-server` dispatch to policy errors while keeping `dry-run` and `shell-command` intact.
- Remove remote verification enforcement while keeping typed local/reference verification adapters.

## Data Side-effects

- Manifests can now describe remote verification policy and Codex app-server endpoint settings.
- Closeout records can include remote verification status, source, provider state, PR merge state, and unverified remote link blockers.
- No provider or GitHub writes are introduced.

## Follow-up

- Run credentialed canaries against one real GitHub PR, one provider-backed artifact, and one real Codex runner endpoint before broad rollout.
- Add streamed event capture and cancellation propagation for long-running remote app-server runners.
- Add authenticated provider task adapters beyond the current Google Drive document/checklist contract when a real task API target is selected.

## Architecture Boundary Check

- highest rule impact: preserved. Sula keeps runner execution and remote credentials behind explicit adapter boundaries while project-owned task truth, provider artifacts, and PR systems remain outside centrally managed Sula files.
