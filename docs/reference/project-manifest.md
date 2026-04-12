# Sula Project Manifest

Sula uses `.sula/project.toml` as the local project manifest.

The safe baseline profile is `generic-project`. Narrower profiles can add more specific managed docs when they express the project more truthfully.

## Required Sections

### `[project]`

- `name`
- `slug`
- `description`
- `profile`
- `default_agent`

### `[repository]`

- `primary_branch`
- `working_branch_prefix`
- `deployment_branch`

### `[rules]`

- `highest_rule`
- `custom_backend_allowed`
- `react_router_allowed`

### `[stack]`

- `frontend`
- `backend`

### `[paths]`

- `api_layer`
- `state_layer`
- `app_shell`
- `status_file`
- `change_records_file`

### `[commands]`

- `install`
- `dev`
- `build`
- `typecheck`

### `[deploy]`

- `base_path`
- `production_url`
- `workflow`

### `[auth]`

- `session_expiry_codes`
- `permission_denied_codes`

### `[memory]` (optional but recommended)

- `change_record_directory`
- `release_record_directory`
- `incident_record_directory`
- `digest_file`
- `status_max_age_days`

### `[workflow]` (optional but recommended)

- `pack`
- `stage`
- `artifacts_root`

### `[storage]` (optional but recommended)

- `provider`
- `sync_mode`
- `workspace_root`
- `provider_root_url`
- `provider_root_id`

### `[portfolio]` (optional)

- `portfolio_id`
- `workspace`
- `owner`

## Example

See [../../schema/project.example.toml](../../schema/project.example.toml).

## Design Notes

- TOML is used instead of YAML to avoid external parser dependencies.
- The manifest should capture stable project facts, not temporary task state.
- Projects without Git may still adopt Sula; repository branch fields may use sentinel values such as `n/a` when Git metadata is intentionally absent.
- The optional `[memory]` section configures durable memory paths and freshness expectations without turning project history into managed truth.
- The optional `[workflow]` section tells Sula which workflow pack should drive artifact routing and stage semantics.
- The optional `[storage]` section records which storage adapter owns the workspace. `google-drive` should be treated as an adapter, not as a core project type.
- The optional `[portfolio]` section lets a project register itself into a broader multi-project workspace without hard-coding that workspace into Sula Core.
- Project history stays in the project repository, not in the manifest.
