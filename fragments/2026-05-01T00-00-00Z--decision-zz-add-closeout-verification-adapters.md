---
id: 2026-05-01T00-00-00Z--decision-zz-add-closeout-verification-adapters
time: 2026-05-01T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-01-zz-add-closeout-verification-adapters.md
---
# Add Closeout Verification Adapters

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

Sula orchestration closeout already validated task requirements, touched files, links, artifacts, and requested `sula check` evidence. The remaining completed-state gap was that references were still reported mostly as generic links. Direct provider APIs and PR adapters will need a stable verification shape before they can be connected safely.

## Analysis

- Accepted closeout should expose what kind of reference was checked, not just whether a string resolved.
- Provider-backed artifacts should resolve through the existing artifact catalog and provider metadata before remote provider APIs exist.
- PR links should be recognized as PR references without forcing GitHub or GitLab credentials into the core path.
- The adapter list should be manifest-controlled and disabled-by-default orchestration should remain safe for existing projects.

## Chosen Plan

- Add `orchestration.verification_adapters` as a first-class manifest field.
- Default the adapters to `local-file`, `artifact-catalog`, `provider-metadata`, `pull-request-url`, and `url`.
- Expand closeout evaluation into typed `verification_checks` while preserving the existing `link_checks` and `unresolved_links` compatibility fields.
- Keep the implementation dependency-light and metadata/reference based until direct provider and PR APIs are explicitly added.

## Execution

- Added manifest parsing, validation, schema, example manifest, and project payload support for `verification_adapters`.
- Added typed closeout reference resolution for local files, catalog artifacts, provider-backed artifacts, provider item URLs, PR URLs, and generic URLs.
- Updated accepted closeout enforcement to keep blocking unresolved references through the richer typed checks.
- Added unit coverage for provider-backed artifact and PR URL closeout resolution.
- Updated README and manifest/orchestration reference docs.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_closeout_evaluator_blocks_unresolved_required_evidence tests.test_sula.SulaCliTests.test_orchestration_closeout_resolves_provider_artifacts_and_pr_urls tests.test_sula.SulaCliTests.test_orchestration_trigger_and_shell_command_runner_collect_evidence -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_init_creates_manifest_lock_and_templates tests.test_sula.SulaCliTests.test_adopt_approve_applies_and_validates_repo tests.test_sula.SulaCliTests.test_status_json_summarizes_project tests.test_sula.SulaCliTests.test_orchestration_defaults_to_disabled_and_supports_dry_run_records tests.test_sula.SulaCliTests.test_orchestration_closeout_resolves_provider_artifacts_and_pr_urls -v`
- `python3 -m unittest discover -s tests -v` passed, 105 tests in 1021.734s.
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py doctor --project-root . --strict --json`
- `python3 scripts/sula.py check --project-root . --json`
- `python3 scripts/sula.py orchestration doctor --project-root . --json`
- `python3 scripts/sula.py portfolio orchestration --portfolio-root ~/.sula/portfolio --json`

## Rollback

- Remove `verification_adapters` from the manifest schema, defaults, payload, and documentation.
- Revert closeout reference resolution to the previous generic URL/artifact/local-file check.
- Keep historical `verification_checks` fields in run records as audit history.

## Data Side-effects

- New closeout records include `verification_adapters` and typed `verification_checks`.
- Existing closeout records remain readable because `link_checks` and `unresolved_links` are preserved.

## Follow-up

- Add PR API adapters that can verify merged/reviewed state when GitHub or GitLab credentials are configured.
- Add provider-native verification adapters that can refresh and verify provider item metadata before accepted closeout.
- Add Codex SDK/app-server runner adapters behind the existing optional runner boundary.

## Architecture Boundary Check

- highest rule impact: preserved. Sula validates operating evidence and provider/artifact references without making remote provider task fields or PR metadata centrally managed business truth.
