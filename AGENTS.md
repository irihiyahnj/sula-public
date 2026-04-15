# AGENTS.md

This file is the primary instruction source for AI coding agents working in the Sula repository.

## Repository Identity

- Repository root is `Sula`.
- Sula is a reusable project operating system, not a single application product.
- Sula manages reusable ops structure, profiles, manifests, and sync tooling.

## Highest Rule

- Preserve the split between centrally managed operating-system files and project-owned business truth.
- Do not turn Sula into a one-project template repository.

## Working Rules

- Keep Sula improvements portable across adopted projects.
- Prefer profile-level abstractions over project-specific wording.
- Keep bootstrap scripts dependency-light.
- Do not make Python 3.11+ or third-party packages mandatory without a strong reason.
- When changing managed templates, consider sync impact on existing projects.
- When changing scaffold templates, keep them as starters, not as centrally enforced truth.
- Update Sula docs when introducing new profiles, manifest fields, or sync behavior.

## Current Scope

- Core managed files
- `generic-project` profile
- `react-frontend-erpnext` profile
- `sula-core` profile
- project manifest schema and example
- machine-readable CLI outputs for local software integration
- `onboard`, `adopt`, `init`, `sync`, `doctor`, `check`, `remove`, `query`, `status`, `artifact`, `portfolio`, `feedback`, `record`, and `memory digest` commands
- static launch-site assets under `site/`, including the canonical launch contract and bootstrap shim

## Current Capabilities

- Sula can encode formal document design policy in a first-class `[document_design]` manifest section, including source-first rules and reusable structure bundles for schedule, proposal, report, process, and training documents.
- Sula can capture reusable managed-file fixes from adopted projects as portable feedback bundles, then ingest, review, and decide them in Sula Core before later rollout through normal versioned sync.
- Sula can register provider-backed artifacts for Google Drive style workspaces, including stable fields such as `project_relative_path`, `provider_item_id`, `provider_item_kind`, `provider_item_url`, `derived_from`, and `identity_key`.
- Sula can now track artifact-family truth sources and freshness for collaborative provider-backed files through fields such as `family_key`, `artifact_role`, `source_of_truth`, `collaboration_mode`, `last_refreshed_at`, and `last_provider_sync_at`.
- Sula can now refresh provider-native Google Docs and Google Sheets in read-only mode through `artifact refresh`, cache normalized provider snapshots under `.sula/cache/provider-snapshots/`, and auto-trigger that refresh when freshness intent is detected.
- Sula can now run a first-class daily `check` workflow that verifies status-memory structure, kernel health, and whether `.sula/state/current.md` plus `.sula/memory-digest.md` are still synchronized with current source documents.
- Sula can materialize project-owned source files into import-friendly deliverables through `artifact materialize`.
- Sula can prepare machine-readable provider import plans through `artifact import-plan`, including auto-generated `.docx` or `.xlsx` bridge artifacts when a Google Docs or Google Sheets import still needs a local handoff file.
- `artifact create` can now render formal source-document bundles for `schedule`, `proposal` / `plan`, `report`, `process`, and `training` artifacts instead of falling back to a single generic shell.
- Current materialization formats:
  - `.md` / `.txt` / `.html` -> `.html`
  - `.md` / `.txt` / `.html` -> `.docx` on macOS through `textutil`
  - `.csv` / `.tsv` / `.json` -> `.xlsx`
- Treat these features as the preferred bridge when a project needs Google Docs or Google Sheets outputs before direct provider-side document creation is available.
- When a new session needs details, read:
  - `docs/reference/feedback-bundle-lifecycle.md`
  - `README.md` artifact section
  - `docs/reference/provider-backed-artifact-identity.md`
  - `docs/change-records/2026-04-12-add-provider-backed-artifact-registration-identity.md`
  - `docs/change-records/2026-04-12-add-artifact-materialization-for-docs-and-sheets.md`
  - `docs/change-records/2026-04-12-add-provider-import-plans-for-google-docs-and-sheets.md`
  - `docs/change-records/2026-04-12-add-truth-source-and-freshness-checks-for-collaborative-provider-artifacts.md`
  - `docs/change-records/2026-04-12-add-provider-native-read-only-refresh-and-artifact-refresh-command.md`

## Out Of Scope For Now

- automatic GitHub app integration
- remote sync service
- stack profiles not yet backed by real project use
