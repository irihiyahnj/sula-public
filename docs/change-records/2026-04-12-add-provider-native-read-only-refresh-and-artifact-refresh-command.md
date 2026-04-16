# Add provider-native read-only refresh and artifact refresh command

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: unknown
- related commit(s): pending review commit
- status: completed

## Background

The prior truth-source and freshness work taught Sula how to decide when a collaborative provider-native file should be considered the fact source, but it still lacked a concrete provider refresh path. That meant freshness intent could change ranking and diagnostics, yet it could not actually fetch the latest provider metadata or cache a normalized provider snapshot.

## Analysis

- Commercial rollout requires a real read-only provider refresh path, not only artifact metadata semantics.
- The refresh path should stay dependency-light, avoid third-party Google SDK lock-in, and degrade safely when auth or metadata is missing.
- Sula also needs an explicit operator command so automation, debugging, and canary rollout do not depend only on natural-language freshness triggers.

## Chosen Plan

- add a provider adapter package under `scripts/sula_providers/`
- implement Google Drive backed read-only refresh for native Google Docs and Google Sheets
- add `artifact refresh` as the explicit CLI surface for provider-native truth-source refresh
- connect freshness-intent `query` and `artifact locate` flows to real provider refresh before result generation
- cache normalized provider snapshots under `.sula/cache/provider-snapshots/`

## Execution

- added `scripts/sula_providers/` with a base contract plus a Google Drive adapter that can read real APIs or local fixtures
- implemented `artifact refresh` with single-artifact, family, query, and all-collaborative modes
- wired freshness-intent query and artifact-locate paths to force provider refresh before returning results
- persisted provider refresh metadata such as revision id, modified time, fetch status, fetch error, and snapshot path back into the artifact catalog
- exposed provider refresh state in status summaries and regression tests

## Verification

- `python3 -m unittest tests.test_sula`

## Rollback

- remove `scripts/sula_providers/` and the `artifact refresh` subcommand if Sula intentionally returns to metadata-only freshness handling
- drop `.sula/cache/provider-snapshots/` if provider-native snapshot caching is intentionally backed out

## Data Side-effects

- artifact catalog entries may now gain provider refresh metadata and snapshot cache paths after a refresh
- `.sula/cache/provider-snapshots/` stores disposable normalized provider snapshots for the latest refresh

## Follow-up

- add write-side provider adapters only after the read-only refresh contract proves stable in real workspaces
- decide whether provider auth should later move from environment variables to a more formal local credential broker

## Architecture Boundary Check

- highest rule impact: preserved; provider refresh state and cached snapshots remain removable Sula operating metadata, while the project-owned files and provider-native deliverables remain the actual business artifacts
