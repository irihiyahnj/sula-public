# Fix Unicode source id collisions in discovered source registry

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: main
- related commit(s): pending
- status: completed

## Background

Sula 0.11.0 generated discovered `source:` ids with an ASCII-only sanitizer. That worked for English-heavy paths, but it collapsed many Chinese and other Unicode filenames into the same short slug. In real adopted projects this produced duplicate ids inside `.sula/sources/registry.json`, and the next kernel sqlite rebuild failed with `sqlite3.IntegrityError: UNIQUE constraint failed: sources.id`.

## Analysis

- The failure belongs in Sula Core because it comes from shared kernel indexing, not from one project's local content.
- The fix should preserve existing ASCII ids where possible so English-only projects do not get unnecessary id churn.
- Recovery also needs an earlier validation surface because previously broken registries could sit on disk until a later sqlite rebuild crashed.

## Chosen Plan

- keep the existing ASCII slug behavior for ASCII-only ids
- generate Unicode-safe slugs for non-ASCII paths, with a short hash fallback only when the normalized text still cannot produce a usable slug
- guarantee per-registry uniqueness for discovered source ids, then teach `doctor --strict` to report duplicate ids in older registries before sqlite rebuild runs

## Execution

- updated discovered source registration so `discover_project_sources()` assigns ids through a uniqueness-aware helper instead of directly concatenating `source:` with the old ASCII-only sanitizer
- changed `sanitize_source_id()` to normalize text with Unicode awareness, preserve meaningful non-ASCII alphanumeric characters, and fall back to a stable short digest only when needed
- extended kernel doctor validation to detect malformed source entries and duplicate source ids in `.sula/sources/registry.json`
- added regression fixtures and tests for Chinese source paths, duplicate-id doctor failures, and the previously working localized adoption flow

## Verification

- `python3 -m py_compile scripts/sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_chinese_locale_renders_localized_status_and_supports_doctor -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_adopt_handles_chinese_source_paths_without_duplicate_registry_ids -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_doctor_reports_duplicate_source_ids_in_registry -v`
- copied the real 昆明同仁医院 project into a temporary directory, ran `sync`, then verified `doctor --strict` passed on the synced copy

## Rollback

- revert the commit that changes discovered source id generation, duplicate-id doctor validation, and the new regression tests
- rebuild the affected project's kernel state through a normal `sync` after the revert so registry and sqlite cache return to the previous behavior

## Data Side-effects

- projects with Unicode-named discoverable files get refreshed discovered `source:` ids on the next sync or kernel refresh
- English-only projects keep the previous ASCII-shaped discovered ids
- older broken registries become diagnosable through `doctor --strict` instead of failing only when sqlite rebuild happens

## Follow-up

- decide whether a later release should add a one-shot migration note for consumers jumping from `0.10.0` to the current `0.11.x` source state
- watch the next canary sync for any query or integration code that incorrectly assumed discovered source ids were always ASCII-only

## Architecture Boundary Check

- highest rule impact: preserved; the fix strengthens the stable kernel/source boundary without turning project-owned Unicode filenames into project-specific special cases
