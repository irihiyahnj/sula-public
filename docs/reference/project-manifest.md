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
- `status_max_age_days`: idle-project freshness backstop for `STATUS.md`; this does not override the stricter rule that `STATUS.md` cannot lag behind the latest durable record and still pass `check`
- `status_recent_decision_limit`: maximum number of `## Recent Decisions` bullets allowed in `STATUS.md`; older decisions should stay in durable records instead of the current-state page
- `status_current_focus_limit`: maximum number of `## Current Focus` bullets allowed in `STATUS.md`
- `status_blocker_limit`: maximum number of `## Blockers` bullets allowed in `STATUS.md`
- `status_archive_file`: durable archive file where overflow items trimmed out of `STATUS.md` should be preserved

### `[workflow]` (optional but recommended)

- `pack`
- `stage`
- `artifacts_root`
- `docs_root`
- `execution_mode`
- `design_gate`
- `plan_gate`
- `review_policy`
- `workspace_isolation`
- `testing_policy`
- `closeout_policy`

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

### `[language]` (optional but recommended)

- `content_locale`
- `interaction_locale`
- `preserve_user_input_language`

### `[projection]` (written by current Sula releases; optional for legacy consumers)

- `mode`
- `enabled_packs`

### `[document_design]` (optional but recommended)

- `principles_path`
- `source_first`
- `register_derived_artifacts`
- `preferred_source_format`
- `schedule_bundle`
- `proposal_bundle`
- `report_bundle`
- `process_bundle`
- `training_bundle`

## Example

See [../../schema/project.example.toml](../../schema/project.example.toml).

## Design Notes

- TOML is used instead of YAML to avoid external parser dependencies.
- The manifest should capture stable project facts, not temporary task state.
- Projects without Git may still adopt Sula; repository branch fields may use sentinel values such as `n/a` when Git metadata is intentionally absent.
- The optional `[memory]` section configures durable memory paths and freshness expectations without turning project history into managed truth.
- The optional `[workflow]` section tells Sula which workflow pack should drive artifact routing, stage semantics, durable workflow-document paths, and execution policy.
- `artifacts_root` remains the general routed-artifact root. `docs_root` is the source-first location for durable workflow documents such as `spec`, `plan`, and `review`.
- `execution_mode`, `design_gate`, `plan_gate`, `review_policy`, `workspace_isolation`, `testing_policy`, and `closeout_policy` let a project express how much workflow rigor it wants without baking one agent plugin's behavior into project truth.
- The optional `[storage]` section records which storage adapter owns the workspace. `google-drive` should be treated as an adapter, not as a core project type.
- `storage.workspace_root` is the current machine's access root for the adopted workspace. It should not be treated as the stable identity of provider-backed artifacts across devices.
- The optional `[portfolio]` section lets a project register itself into a broader multi-project workspace without hard-coding that workspace into Sula Core.
- The optional `[language]` section lets a project choose the language for Sula-generated docs, records, and human-readable command output while preserving user-authored text as-is.
- The `[projection]` section separates Sula's kernel capabilities from the repo-visible governance surface. New `generic-project` and `react-frontend-erpnext` adoptions default to `detached`, while current `sula-core` defaults to `governed`.
- Legacy adopted projects may not have a `[projection]` section yet. Current Sula versions treat those repositories as `governed` until the manifest is rewritten, so existing visible docs continue to sync safely.
- `enabled_packs` records which visible projection packs are active. Disabling a pack removes that pack's visible files from Sula ownership, but it does not turn off kernel capabilities such as `doctor`, `check`, `query`, `artifact`, or `feedback`.
- The optional `[document_design]` section records how formal planning, proposal, report, process, and training documents should be structured, while keeping project-owned source files as the editable truth. When the `document-design` projection pack is disabled, `principles_path` may be set to `n/a`.
- Project history stays in the project repository, not in the manifest.

See [provider-backed-artifact-identity.md](provider-backed-artifact-identity.md) for the cross-device identity model behind provider-backed project files.
