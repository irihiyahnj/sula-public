# Add truth-source and freshness checks for collaborative provider-backed artifacts

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: unknown
- related commit(s): pending review commit
- status: completed

## Background

Sula could already register provider-backed artifact identity, materialize bridge files, and prepare provider import plans, but it still lacked a session-layer answer to a common real-world failure mode: collaborative Google Docs or Google Sheets could change outside the current session while Sula kept trusting a stale local copy or stale retrieval context.

## Analysis

- Users should not have to remember a fixed freshness command or explain provider-vs-local truth every time.
- Artifact identity was already rich enough to carry the next layer, but the catalog and query surfaces still lacked family-level truth-source and freshness semantics.
- If provider metadata is incomplete, silently falling back to the local workspace copy is the wrong behavior for collaborative documents.

## Chosen Plan

- extend artifact registration with truth-source, collaboration, family, and freshness metadata
- teach artifact families to distinguish `workspace-source`, `provider-native-source`, and `exported-derivative`
- detect natural-language freshness intent in `query` and `artifact locate`
- expose truth-source and stale-local-copy summaries in `query`, `artifact locate`, and `status`
- add regression tests for freshness intent, provider metadata gaps, and artifact-family grouping

## Execution

- added `family_key`, `artifact_role`, `source_of_truth`, `collaboration_mode`, `last_refreshed_at`, and `last_provider_sync_at` to registered artifact metadata
- added family-level truth-source evaluation plus provider-metadata-gap reporting
- updated query compaction to group artifact families by `family_key`, not only by path
- taught `query --q "先看最新版本再继续"` and similar natural-language phrases to trigger freshness-oriented retrieval
- updated `artifact locate --json` and `status --json` to expose truth-source and freshness summaries
- added regression tests for provider-native truth preference, metadata-gap reporting, and workspace/provider/derivative family tracking

## Verification

- `python3 -m unittest tests.test_sula`

## Rollback

- remove the new artifact freshness metadata fields if Sula intentionally reverts to path-only artifact indexing
- restore query family compaction to path-only grouping if family-level truth-source modeling is intentionally backed out

## Data Side-effects

- existing artifact catalog entries remain readable and gain the new fields on next write or registration
- query, locate, and status JSON outputs now include additional truth-source and freshness metadata for artifact results

## Follow-up

- add direct provider fetch adapters when Sula is ready to pull provider-native Google Docs or Google Sheets content without external bridge steps
- decide whether truth-source freshness should gain explicit age thresholds per workflow pack

## Architecture Boundary Check

- highest rule impact: preserved; truth-source and freshness logic lives in removable Sula metadata while project-owned source files and provider-native deliverables remain the real business artifacts
