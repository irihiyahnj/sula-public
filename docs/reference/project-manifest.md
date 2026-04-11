# Sula Project Manifest

Sula uses `.sula/project.toml` as the local project manifest.

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

## Example

See [../../schema/project.example.toml](../../schema/project.example.toml).

## Design Notes

- TOML is used instead of YAML to avoid external parser dependencies.
- The manifest should capture stable project facts, not temporary task state.
- Project history stays in the project repository, not in the manifest.
