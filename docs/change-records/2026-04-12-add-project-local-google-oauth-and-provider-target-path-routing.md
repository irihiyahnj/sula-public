# Add project-local Google OAuth storage and provider target-path routing

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: unknown
- related commit(s): pending review commit
- status: completed

## Background

Sula could already refresh collaborative Google-native artifacts, but it still left two operational gaps: other sessions had to guess where project-specific Google OAuth state should live, and provider-native Docs or Sheets could still inherit ambiguous target paths from local bridge files instead of a stable folder path under the provider project root.

## Analysis

- Provider auth should default to a project-local removable secret path when a Sula project root is known.
- Provider-native item placement should be expressed as a provider-root-relative contract, not inferred later from one machine's `artifacts/` bridge file layout.
- External import/create workers need both the native item path and the parent folder path so they do not silently create documents at the provider root.

## Chosen Plan

- prefer `PROJECT/.sula/local/google-oauth.json` as the default project-local Google OAuth store
- let provider refresh try the project-local OAuth store first and then fall back to the global store
- treat `project_relative_path` as the provider-native target path under the provider root
- default provider-native target paths from workflow slot plus stable slug when no explicit path is given
- expose `provider_parent_relative_path` in import plans and truth-source summaries

## Execution

- added project-local OAuth path helpers and made Google provider refresh honor them
- updated `scripts/sula_google_auth.py` so `--project-root` defaults the OAuth output path to `.sula/local/google-oauth.json`
- updated provider-native registration and import planning so default target paths resolve to slot-relative paths such as `delivery/2026-04-12-shared-report-provider`
- surfaced provider target-path details in query, locate, status, and import-plan outputs
- ignored `.sula/local/*` in git so project-local token files remain removable local state

## Verification

- `python3 -m unittest tests.test_sula`

## Rollback

- remove the project-local OAuth helpers and return to global-only OAuth path resolution
- revert provider-native default target-path routing if Sula intentionally goes back to explicit-path-only registration

## Data Side-effects

- project-local Google OAuth state may now be stored under `.sula/local/google-oauth.json`
- provider import plans and truth-source summaries now expose provider target-path routing fields

## Follow-up

- add direct provider-side folder resolution and creation when Sula starts creating Docs or Sheets natively
- consider a future manifest-level slot-to-folder override only after real projects show a need beyond the workflow-slot default

## Architecture Boundary Check

- highest rule impact: preserved; secrets stay in removable local Sula state, and provider target-path routing remains operating metadata rather than project-owned business truth
