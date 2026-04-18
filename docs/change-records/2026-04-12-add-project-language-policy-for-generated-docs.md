# Add project language policy for generated docs and records

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Sula had started to fit real non-code project work, but its generated docs, records, and human-readable command output still defaulted to English. That was a poor fit for Chinese-first project workspaces, especially when project owners needed to read status, change records, and generated artifacts directly inside Drive-synced folders.

## Analysis

- File paths and stable machine keys should remain English so sync, parsing, and cross-project portability stay stable.
- The actual human-facing content should follow the project's chosen language instead of leaking repository-default English.
- Existing project-owned files must stay preserved; switching language later should affect future generated content without forcing a destructive rewrite of prior scaffolds.

## Chosen Plan

- add a project-level `[language]` manifest section with content and interaction locales
- teach onboarding to suggest and capture the default language once
- localize generated status, change records, record templates, memory digest, and artifact templates while keeping paths stable
- make status and record parsing recognize both English and Chinese section and field labels

## Execution

- added `[language]` to the manifest example and reference docs
- updated onboarding to infer and ask for `content_locale`
- localized scaffold templates and builtin record/artifact rendering through locale-aware tokens
- added parsing aliases so `doctor`, `status`, `query`, and kernel extraction can read Chinese headings and metadata fields
- added regression tests for Chinese onboarding, Chinese generated files, and post-adoption locale switching

## Verification

- ran `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- ran `python3 -m unittest discover -s tests -v`
- ran `python3 scripts/sula.py sync --project-root .`
- ran `python3 scripts/sula.py sync --project-root examples/okoktoto`
- ran `python3 scripts/sula.py doctor --project-root . --strict`
- ran `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`

## Rollback

- revert the commit that introduces the language policy and localized templates
- re-run sync to restore the prior English-only generated content contract

## Data Side-effects

- no runtime data side-effects
- adopted projects gain language metadata in `.sula/project.toml` and localized generated content on future renders

## Follow-up

- add site-launch and public bootstrap copy that explains the language choice during onboarding
- decide whether `query` and `doctor` should eventually support more localized human-readable output families beyond Chinese and English

## Architecture Boundary Check

- highest rule impact: preserved; only Sula-generated operating content is localized, while project-owned truth and stable file paths remain under project control
