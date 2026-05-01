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

### `[orchestration]` (optional; disabled by default)

- `enabled`: must default to `false` unless a project explicitly opts into dispatch
- `mode`: `ticket-runner`, `review-assistant`, or `status-only`
- `task_source`: current core implementation supports `local`, `provider-task-document`, and `provider-api`
- `runner`: current core implementation supports `dry-run`, `shell-command`, `codex-sdk`, and `codex-app-server`
- `runner_command`: shell command used when `runner = "shell-command"` or `runner = "codex-sdk"`
- `runner_endpoint`, `runner_token_env`: HTTP endpoint and optional token environment variable for `runner = "codex-app-server"`
- `tasks_path`: project-owned local task file for the `local` task source
- `provider_task_item_id`, `provider_task_item_kind`, `provider_task_item_url`: provider-native task source identity when `task_source = "provider-api"`
- `workspace_root`: root for isolated task workspaces
- `workspace_mode`: `none`, `branch`, `worktree`, `copy`, `container`, or `remote`
- `trust_profile`
- `allow_project_root_runner`: explicit opt-in for real runners to use the project root when `workspace_mode = "none"`
- `max_concurrent_runs`
- `max_retry_count`
- `max_run_minutes`
- `daily_budget_minutes`
- `unattended_risk_ceiling`
- `require_human_approval_for`
- `status_surface`
- `verification_adapters`: closeout reference adapters enabled for accepted-run checks; defaults to `local-file`, `artifact-catalog`, `provider-metadata`, `pull-request-url`, and `url`
- `remote_verification_policy`: `reference-only`, `opportunistic`, or `required`; controls whether PR/provider closeout references must be remotely verified before acceptance

### `[automation]` (optional; enabled by default)

- `enabled`: controls whether Sula records command/provider/status events into the automation state inbox
- `mode`: `observe`, `assist`, or `execute`; `assist` records events and creates intents, while `execute` may dispatch eligible low-risk work
- `auto_intake`: automatically classify observed events into task intent when useful
- `auto_plan`: expose automation intents as orchestration tasks without requiring a manual `orchestration trigger`
- `auto_dispatch`: allow `execute` mode to start eligible runs automatically
- `risk_ceiling`: highest risk level eligible for automatic dispatch
- `approval_required_for`: categories that still require human approval before dispatch
- `event_sources`: enabled event sources such as `sula-cli`, `provider`, `status`, `artifact`, `workflow`, and `external`

### `[agent_behavior]` (optional but recommended)

- `quality_policy`: `sula-karpathy-inspired` or `minimal`
- `clarification_policy`: `non-trivial-only`, `always`, or `never`
- `diff_scope_policy`: `surgical`, `task-scoped`, or `open`
- `success_criteria_policy`: `required`, `recommended`, or `off`
- `assumption_policy`: `surface-when-uncertain`, `always`, or `off`
- `complexity_policy`: `simplicity-first` or `project-default`
- `require_verification`
- `forbid_drive_by_refactors`

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
- The optional `[orchestration]` section is Sula's Symphony-style control-plane contract. It is deliberately disabled by default, uses local task files and dry-run execution as the safe default adapter pair, and records state under `.sula/state/orchestration/` rather than turning runner prompts or tracker metadata into project truth.
- `tasks_path` is project-owned task intent. Sula normalizes it for dispatch, but task descriptions, acceptance criteria, and validation requirements remain business truth owned by the project.
- `task_source = "provider-task-document"` reads a project-local mirror of an external/provider task document from `tasks_path`. Markdown checklist lines and JSON task mirrors normalize into the same task model while preserving the provider document as project-owned task truth.
- `task_source = "provider-api"` reads tasks through the configured storage provider adapter using `provider_task_item_id`, `provider_task_item_kind`, and `provider_task_item_url`. The current Google Drive adapter supports fixture-backed task lists and read-only Google Doc checklist parsing, preserving provider-owned task truth outside managed Sula files.
- The optional `[automation]` section is the event-driven Sula kernel above orchestration. Sula commands such as `check`, `doctor`, `status`, `query`, `sync`, and artifact freshness operations can automatically record events under `.sula/state/automation/`, classify failed or freshness-related events into intents, and expose those intents to orchestration as tasks. Manual `orchestration trigger` remains available for backfill and debugging, but normal Sula usage should not depend on users remembering to trigger work by hand.
- `workspace_root` and `workspace_mode` are safety controls. Sula blocks workspace paths that escape the configured project root in the current local implementation.
- `runner = "shell-command"` is the first real runner adapter. It requires `runner_command`, blocks project-root mutation unless `allow_project_root_runner = true`, and should normally run in `workspace_mode = "copy"` so evidence is collected from an isolated workspace.
- `runner = "codex-sdk"` runs a project-configured command that receives a JSON request on stdin and returns optional JSON evidence on stdout. This keeps SDK installation project-local instead of making a Sula dependency mandatory.
- `runner = "codex-app-server"` posts the same JSON request to `runner_endpoint` and can read a bearer token from `runner_token_env`. This is the remote runner boundary for app-server style execution.
- `verification_adapters` controls Sula-native closeout reference checks. These adapters are deliberately metadata/reference based by default; they can validate local files, artifact catalog entries, provider-backed artifact metadata, PR URLs, and ordinary URLs without forcing a remote service integration.
- `remote_verification_policy = "opportunistic"` tries fixture-backed or credential-backed remote checks when available but does not block accepted closeout if credentials are absent. Set it to `required` only when the project has configured the needed provider or PR credentials.
- The optional `[agent_behavior]` section records portable agent execution policy. It absorbs reusable Karpathy-style coding guidance as Sula-native behavior gates instead of binding adopted projects to one editor, plugin, or assistant.
- `agent_behavior` policy is subordinate to the repository highest rule, project-owned truth, workflow gates, tests, and human approval requirements.
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
