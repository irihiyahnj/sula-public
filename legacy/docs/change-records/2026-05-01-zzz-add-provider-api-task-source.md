# Add Provider API Task Source

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

Sula orchestration could already read local task files, provider task document mirrors, and generic trigger/intake events. The remaining task-source gap was a provider adapter path that reads task intent directly through Sula's provider abstraction without making a mirrored task document mandatory.

## Analysis

- Provider-owned task truth should remain outside centrally managed Sula files.
- Sula should normalize provider tasks into the same risk, acceptance, validation, and blocker model used by local tasks.
- The first provider API implementation should be dependency-light and testable without credentials.
- Existing Google Drive fixture and read-only refresh infrastructure can support a safe provider task source contract.

## Chosen Plan

- Add `task_source = "provider-api"` as a first-class orchestration task source.
- Add `provider_task_item_id`, `provider_task_item_kind`, and `provider_task_item_url` to the orchestration manifest contract.
- Extend the provider adapter protocol with `fetch_tasks`.
- Implement fixture-backed Google Drive task lists and Google Doc checklist parsing.
- Keep orchestration disabled by default and block enabled provider-api sources with missing provider task identity.

## Execution

- Added provider task snapshot dataclass and provider adapter `fetch_tasks` protocol.
- Implemented Google Drive provider task fetching from explicit fixture task arrays or normalized Google Doc checklist text.
- Added Sula normalization for provider-api tasks, including provider metadata passthrough.
- Added manifest defaults, schema, config payload fields, policy checks, and documentation.
- Added unit coverage for fixture-backed provider-api task ingestion.

## Verification

- `python3 -m py_compile scripts/sula.py scripts/sula_providers/base.py scripts/sula_providers/google_drive.py scripts/sula_providers/__init__.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_provider_api_task_source_reads_fixture_backed_provider_tasks tests.test_sula.SulaCliTests.test_provider_task_document_source_and_portfolio_orchestration_summary -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_init_creates_manifest_lock_and_templates tests.test_sula.SulaCliTests.test_adopt_approve_applies_and_validates_repo tests.test_sula.SulaCliTests.test_status_json_summarizes_project tests.test_sula.SulaCliTests.test_provider_api_task_source_reads_fixture_backed_provider_tasks tests.test_sula.SulaCliTests.test_provider_task_document_source_and_portfolio_orchestration_summary -v`
- `python3 -m unittest discover -s tests -v` passed, 106 tests in 972.209s.
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py doctor --project-root . --strict --json`
- `python3 scripts/sula.py check --project-root . --json`
- `python3 scripts/sula.py orchestration doctor --project-root . --json`
- `python3 scripts/sula.py portfolio orchestration --portfolio-root ~/.sula/portfolio --json`

## Rollback

- Remove `provider-api` from `ORCHESTRATION_TASK_SOURCE_CHOICES`, schema, defaults, docs, and task loading.
- Remove `fetch_tasks` from the provider adapter protocol and Google Drive adapter.
- Existing local and provider-task-document sources remain unaffected.

## Data Side-effects

- New manifests can include provider task identity fields.
- Orchestration task snapshots can now include provider metadata on normalized tasks.
- No remote writes are introduced.

## Follow-up

- Add authenticated provider task API variants beyond Google Drive task documents.
- Add remote PR/provider verification adapters for accepted closeout.
- Add Codex SDK/app-server runner adapters behind the optional runner boundary.

## Architecture Boundary Check

- highest rule impact: preserved. Sula reads and normalizes provider-owned task truth through an adapter, but does not centralize provider task content into managed operating-system files.
