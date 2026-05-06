# Release Sula 0.15.0 orchestration control plane and runner boundaries

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- status: prepared

## Scope

Version the current Sula source tree as `0.15.0` so the completed automation kernel, orchestration control-plane work, closeout verification model, and Codex runner boundaries can roll forward as one coherent minor release.

## Risks

- public launch-facing metadata and source tag must stay aligned after publication, or bootstrap consumers may resolve inconsistent release baselines
- projects that enable orchestration without understanding workspace, runner, or verification policy will now expose more explicit review and closeout gates instead of loose best-effort automation
- automation now defaults to execute-mode auto-dispatch, but default dispatch lands in the dry-run runner; projects that configure a real runner should review risk ceilings and approval categories before allowing unattended mutation
- a true external release still requires a clean export, public tag publication, and at least one credentialed canary using real PR/provider verification and a real Codex runner endpoint

## Verification

- `python3 -m unittest discover -s tests -v` passed, 111 tests in 1015.257s.
- `python3 -m unittest tests.test_sula.SulaCliTests.test_automation_check_failure_creates_intent_without_manual_trigger tests.test_sula.SulaCliTests.test_automation_default_dispatches_low_risk_intent_to_dry_run tests.test_sula.SulaCliTests.test_automation_assist_mode_keeps_intent_queued -v` passed.
- `python3 scripts/sula.py canary verify --project-root . --all` passed for `sula-root`, `okoktoto-v5-example`, `field-ops-generic-canary`, and `client-service-drive-canary`.
- `python3 scripts/sula.py doctor --project-root . --strict --json` passed.
- `python3 scripts/sula.py check --project-root . --json` passed.
- `python3 scripts/sula.py orchestration doctor --project-root . --json` passed.
- `python3 scripts/sula.py release export-public --project-root . --output /tmp/sula-public-0.15.0 --overwrite --json` succeeded and exported 297 files.
- `python3 scripts/sula.py release readiness --project-root . --json` still fails for the expected public-release reasons: dirty working tree and historical lineage metadata that keep the recommended strategy at `fresh-public-repo`; embedded canaries pass.

## Rollback

- revert the `0.15.0` source-release batch if the orchestration control-plane surface should not become the next downstream sync target
- if rollback is required, move the launch-facing source ref back to a previously validated public tag and re-run readiness

## Follow-up

- maintain launch-facing metadata and upgrade prompts so they continue to point at the published `v0.15.0` baseline
- run one credentialed canary for PR/provider verification and one real `codex-app-server` canary before broad external rollout
- expand automation classifiers after real project runs reveal recurring provider, status, and workflow failure patterns
