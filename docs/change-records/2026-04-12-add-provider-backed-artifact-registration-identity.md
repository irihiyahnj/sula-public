# Add provider-backed artifact registration identity

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Sula already had a local-sync Google Drive storage adapter and an artifact catalog, but artifact registration still assumed that every deliverable could be identified by one local project path. That was not enough for Google Docs or Google Sheets that may be provider-native first and only optionally exported into local files later.

## Analysis

- The next usable step was not a full direct Google API adapter. It was a stable artifact identity layer that could register provider-backed deliverables today without breaking the existing local artifact workflow.
- Existing path-based artifact registration needed to stay compatible because current adopted projects already rely on it.
- Query and object indexing also needed to see provider-backed identity data, otherwise the new metadata would exist only in the catalog and not in retrieval.

## Chosen Plan

- Extend `artifact register` with provider-backed metadata fields.
- Keep `path` compatibility for current local-sync projects.
- Persist stable artifact identity metadata in `.sula/artifacts/catalog.json`.
- Surface those fields through artifact lookup and kernel object indexing.

## Execution

- updated `artifact register` to accept provider-backed metadata such as `project_relative_path`, `provider_item_id`, `provider_item_kind`, `provider_item_url`, and `derived_from`
- updated artifact catalog entries to persist `identity_key`, `project_relative_path`, `local_access_paths`, and provider-backed metadata
- updated artifact object generation and locate/query search inputs so provider-backed artifact ids and paths are retrievable
- updated README usage examples and the provider-backed identity reference doc
- added regression tests for both local artifact registration and provider-backed registration without a local file path

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_artifact_create_register_and_locate_json`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_artifact_register_supports_provider_backed_identity_without_local_path`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_adopt_with_google_drive_storage_adds_google_drive_adapter tests.test_sula.SulaCliTests.test_query_returns_matching_object_results tests.test_sula.SulaCliTests.test_chinese_locale_artifact_title_generates_stable_file_and_chinese_content`

## Rollback

- revert the artifact registration changes in `scripts/sula.py`
- remove the new provider-backed artifact fields from `.sula/artifacts/catalog.json` only if the old path-only contract is intentionally restored

## Data Side-effects

- newly created or updated artifact catalog entries include additional provider-backed identity fields
- existing path-only artifact entries remain readable without migration
- no manifest schema changes

## Follow-up

- add direct provider-native document enumeration after real Google Drive project usage stabilizes
- teach query family compaction to use artifact identity keys when provider-native and exported derivatives should collapse into one family
- decide whether provider-native revision metadata belongs in the artifact catalog or in a future provider adapter cache

## Architecture Boundary Check

- highest rule impact: preserved; provider-backed identity lives in removable Sula operating metadata while project deliverables remain project-owned truth
