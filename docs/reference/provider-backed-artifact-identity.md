# Sula Provider-Backed Artifact Identity

This document defines how Sula should identify, index, and query project artifacts when the storage provider is not just the local filesystem and the same project may be opened from different devices or through direct provider APIs.

Google Drive is the first concrete case, but the rule must stay portable to future providers such as Feishu Drive.

## Core Rule

A provider-backed artifact belongs to the project, not to one machine.

Absolute local paths are runtime access details. They are not durable artifact identity.

## Why This Matters

- Google Drive local-sync roots differ across devices.
- A project may contain both ordinary files and provider-native documents such as Google Docs or Google Sheets.
- The same deliverable may be seen through different access channels: local-sync, export, or direct provider API.
- Query results should still resolve to one project artifact instead of splitting into machine-specific duplicates.

## Current State

Today `google-drive` is modeled as a storage adapter in `local-sync` mode.

Sula can already:

- record storage metadata in `[storage]`
- discover files under the adopted project root
- register artifacts in `.sula/artifacts/catalog.json`
- index local sources and artifacts into `.sula/objects/`, `.sula/indexes/`, and `.sula/cache/kernel.db`
- emit provider import plans under `.sula/exports/provider-imports/` for external software or future direct adapters

The current artifact registration flow can also persist provider-backed identity metadata:

- `project_relative_path`
- `provider_item_id`
- `provider_item_kind`
- `provider_item_url`
- `derived_from`
- `identity_key`
- `family_key`
- `artifact_role`
- `source_of_truth`
- `collaboration_mode`
- `last_refreshed_at`
- `last_provider_sync_at`

`project_relative_path` should now be read as "the provider-native target path inside the recorded provider root", not as a machine-local path guess.

Today Sula can treat a registered native Google Doc or Google Sheet as the fact source for a collaborative artifact family, and it can surface freshness risk when a local copy may be stale.

Today the preferred bridge is:

1. keep the project-owned source file in the workspace
2. materialize `.docx`, `.html`, or `.xlsx` only when needed
3. ask `artifact import-plan` for a provider-specific import contract
4. let external software or a future adapter perform the real provider import
5. register the resulting provider-native item back into the artifact catalog

## Identity Layers

### 1. Stable Project Identity

This is the durable identity Sula should use for provider-backed artifacts.

Preferred stable coordinates:

- `storage.provider`
- `storage.provider_root_id`
- provider item id such as a Drive file id, Doc id, or Sheet id
- project-relative location such as a workflow slot path under the project workspace
- artifact kind, status, and version label when the provider item can have multiple project revisions

### 2. Runtime Access Identity

This is how one machine or one adapter reaches the artifact right now.

Examples:

- local absolute path inside a Google Drive sync directory
- current `workspace_root`
- local exported filename such as a `.docx`, `.pdf`, or `.md`
- a temporary provider API fetch path

Runtime access identity may change without changing the project artifact itself.

## Storage Rules

### Workspace Root

`workspace_root` should mean "the current machine's access root for this project workspace".

It should not mean:

- the permanent identity of the project
- the permanent identity of an artifact
- a value that must match across devices

### Provider Root

`provider_root_id` and `provider_root_url` should identify the provider-side project container.

For Google Drive this is the stable folder identity that survives local path changes across devices.

Provider-native item placement should then be derived as:

- `provider_root_*`: the top-level project container
- `project_relative_path`: the native item path under that container
- `provider_parent_relative_path`: the folder path under that container that should hold the native item

If a provider-native artifact is registered or planned without an explicit `project_relative_path`, Sula should default it from the workflow slot plus a stable title stem such as `delivery/2026-04-12-hospital-intake-draft`. That keeps native Docs and Sheets out of the provider root folder by default.

## Artifact Rules

Provider-backed artifacts should be treated as first-class project objects even when they are not plain local files.

Sula should distinguish at least these artifact shapes:

- synced file: a normal file that exists inside the local adopted project root
- provider-native document: a Google Doc or Google Sheet that may not have a stable exported file in the local root
- exported derivative: a PDF, Markdown file, CSV, or other generated file derived from a provider-native source

Sula now records these shapes directly through `artifact_role`:

- `workspace-source`
- `provider-native-source`
- `exported-derivative`

For cross-device identity, Sula should prefer:

1. provider item identity
2. project-relative location
3. artifact catalog identity

Sula should not prefer:

1. one machine's absolute path
2. one machine's local sync root

## Query And Indexing Rules

When `sync_mode = "local-sync"`:

- files inside the adopted project root should be indexed as local project files
- those files should still inherit provider metadata from the storage adapter
- query should treat the file as a project object, not as a machine-local orphan
- query, `artifact locate`, and `status` should expose which family member is the current truth source and whether local copies may be stale

When direct provider mode exists:

- provider-native items should be indexed even if no local exported file exists
- query should merge local-sync and provider-native observations into one artifact family when they refer to the same project object
- absolute local paths should be stored as access hints, not as the primary dedupe key

## Generation Rule

Sula should not require AI to "author the final document format by hand" every time.

The preferred flow is:

1. generate structured content once
2. let the adapter write that content into a provider-native document or sheet
3. optionally export derivatives such as PDF, CSV, or Markdown
4. register all resulting deliverables as project artifacts

This keeps the project truth in the project workspace while avoiding wasteful duplication between content generation and document materialization.

As a practical bridge before direct provider APIs exist everywhere, Sula may also materialize import-friendly local derivatives such as:

- Markdown to HTML or DOCX for Google Docs import
- CSV, TSV, or JSON tables to XLSX for Google Sheets import

Sula can now also write a machine-readable import plan that tells another tool exactly which bridge file to import, which provider item kind to create, and which `artifact register` metadata to persist afterward.

## Collaborative Freshness Rule

When an artifact family is marked `collaboration_mode = "multi-editor"` and has complete provider metadata, Sula should default to the provider-native item as the fact source.

When a user says things like:

- "这份表很多人在 Google 上一起改"
- "别人刚改过"
- "先看最新版本再继续"
- "以共享文档为准"

Sula should treat that as a freshness intent, rerun truth-source evaluation, and prefer provider-native facts over cached local interpretations.

The retrieval outputs now surface:

- `truth_source_type`
- `truth_source_artifact_id`
- `truth_source_path`
- `last_refreshed_at`
- `last_provider_sync_at`
- `local_copy_stale_risk`
- `missing_provider_metadata`

If required provider metadata is incomplete, Sula should not silently treat the workspace file as current. It should report the missing fields and require a minimal re-registration step before a provider-native truth-source claim is trusted.

## Read-only Refresh Path

Sula now has an explicit provider refresh workflow for collaborative provider-native artifacts:

- `artifact refresh --artifact-id ...`
- automatic provider refresh on freshness-intent `query`
- automatic provider refresh on freshness-intent `artifact locate`
- optional `status --refresh-provider` for an operator-driven full summary refresh

For Google-backed workspaces, the first shipping contract is read-only:

- Google Drive metadata is fetched to confirm `modifiedTime`, `version`, and the current web URL
- Google Docs bodies are normalized into a cache-friendly block model
- Google Sheets metadata is normalized into sheet summaries
- normalized provider snapshots are cached under `.sula/cache/provider-snapshots/`

Auth stays removable and local:

- real refresh uses `SULA_GOOGLE_ACCESS_TOKEN`
- local tests and canaries may use `SULA_PROVIDER_FIXTURE_DIR`

If refresh fails, Sula records fetch status and error details in removable artifact metadata instead of pretending that the old local context is still current.

## Cross-Device Examples

### Example 1: Same Drive project on two machines

Machine A sees:

- `workspace/Hospital-A/contracts/2026-04-12-intake-v1.md`

Machine B sees:

- `/Volumes/work/Drive/Hospital-A/contracts/2026-04-12-intake-v1.md`

Sula should treat both as the same project artifact if the provider root and project-relative location match.

### Example 2: Native Google Doc plus exported PDF

A hospital report exists as:

- Google Doc id `abc123`
- exported PDF under `artifacts/delivery/2026-04-12-hospital-report-v2.pdf`

Sula should model one logical report artifact family with:

- one provider-native source
- one exported derivative
- shared project status and version metadata

## Target Catalog Direction

The current artifact catalog already records storage provider metadata.

The next contract should extend artifact identity toward provider-backed fields such as:

- `provider_item_id`
- `provider_item_kind`
- `project_relative_path`
- `local_access_paths`
- `derived_from`

These should be additive fields in Sula-managed metadata, not project-owned business truth.

## Migration Path

1. Keep `google-drive` local-sync as the safe baseline.
2. Continue indexing local files under the adopted project root exactly as project files.
3. Extend artifact registration so provider-native documents can be registered without pretending they are ordinary local files.
4. Emit explicit provider import plans so external software does not need to guess how `.docx` or `.xlsx` bridge files map back to project artifacts.
5. Teach query dedupe to prefer provider identity plus project-relative location over absolute path.
6. Add direct provider adapters only after the local-sync contract is stable in real projects.

## Boundary Check

- highest rule impact: preserved; this model keeps provider access details inside removable Sula metadata while treating the real deliverables as project-owned artifacts under the adopted workspace
