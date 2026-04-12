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
- `onboard`, `adopt`, `init`, `sync`, `doctor`, `remove`, `query`, `status`, `artifact`, `portfolio`, `record`, and `memory digest` commands
- static launch-site assets under `site/`, including the canonical launch contract and bootstrap shim

## Current Capabilities

- Sula can register provider-backed artifacts for Google Drive style workspaces, including stable fields such as `project_relative_path`, `provider_item_id`, `provider_item_kind`, `provider_item_url`, `derived_from`, and `identity_key`.
- Sula can materialize project-owned source files into import-friendly deliverables through `artifact materialize`.
- Current materialization formats:
  - `.md` / `.txt` / `.html` -> `.html`
  - `.md` / `.txt` / `.html` -> `.docx` on macOS through `textutil`
  - `.csv` / `.tsv` / `.json` -> `.xlsx`
- Treat these features as the preferred bridge when a project needs Google Docs or Google Sheets outputs before direct provider-side document creation is available.
- When a new session needs details, read:
  - `README.md` artifact section
  - `docs/reference/provider-backed-artifact-identity.md`
  - `docs/change-records/2026-04-12-add-provider-backed-artifact-registration-identity.md`
  - `docs/change-records/2026-04-12-add-artifact-materialization-for-docs-and-sheets.md`

## Out Of Scope For Now

- automatic GitHub app integration
- remote sync service
- stack profiles not yet backed by real project use
