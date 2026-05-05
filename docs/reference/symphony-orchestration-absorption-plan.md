# Symphony Orchestration Absorption Plan

## Purpose

This document defines how Sula should absorb the durable value of OpenAI Symphony-style Codex orchestration without turning Sula into a single tracker, agent, or implementation template.

The target is a completed Sula orchestration capability: Sula can govern, dispatch, observe, verify, and learn from agent-executed project work while preserving the split between centrally managed operating-system files and project-owned business truth.

## Strategic Decision

Sula should absorb the orchestration model, not the reference implementation.

Absorb:

- task-source to workspace to runner to verification control loop
- tracker-neutral task abstraction
- deterministic isolated workspaces
- explicit agent runner contracts
- bounded concurrency, retry, cancellation, and stale-run recovery
- structured observability and run records
- cost, risk, trust, and eligibility policies
- feedback and memory promotion from completed runs

Do not absorb as defaults:

- Linear-only workflow assumptions
- Elixir/Phoenix runtime dependency
- mandatory unattended coding-agent execution
- one fixed issue-state model
- root-level `WORKFLOW.md` as the only source of project workflow truth
- agent prompts as durable business truth

## Completed-State Outcome

In the completed version, Sula becomes a project execution operating system.

Sula should be able to:

- read eligible work from configured task sources
- observe normal Sula entrypoints and external adapter events without requiring users to manually create orchestration triggers
- classify useful events into durable automation intents
- expose automation intents as orchestration tasks when planning is enabled
- dispatch eligible low-risk intents automatically when project policy explicitly allows execute mode
- classify risk and required gates from manifest policy
- allocate isolated workspaces per task
- launch a configured runner adapter
- stream run state into Sula-managed operational records
- enforce cost, concurrency, timeout, retry, and cancellation policies
- require evidence before accepting completion
- preserve audit trails for accepted, abandoned, failed, and blocked runs
- promote reusable lessons into memory, feedback bundles, managed docs, or checks
- expose project and portfolio orchestration state through human and JSON surfaces

## Architecture Boundary

Sula Core owns the operating contract:

- manifest schema
- task-source abstraction
- runner abstraction
- workspace isolation policy
- risk and eligibility policy
- run registry
- observability schema
- closeout and verification gates
- memory and feedback integration

Project-owned truth owns the actual work:

- task intent
- acceptance criteria
- domain decisions
- source documents
- code changes
- business workflow content
- provider-native deliverables

Adapters own external mechanics:

- Linear, GitHub Issues, local task files, provider task documents
- Codex SDK, Codex app-server, CLI runner, future agent runners
- Git, worktree, container, remote worker, and provider APIs

## Manifest Target

The completed capability includes two policy layers:

- `[automation]` controls event observation, intent creation, automatic planning, and automatic dispatch.
- `[orchestration]` controls task-source loading, runner execution, workspace boundaries, run records, and closeout gates.

Automation is enabled by default in execute mode with `auto_dispatch = true` so Sula can notice normal command/provider/status events, create follow-up intent, and dispatch eligible low-risk work without user memory. Orchestration is enabled by default with the non-mutating `dry-run` runner so task visibility, run records, and closeout gates are available immediately while real execution remains an explicit adapter decision.

Current Sula automation contract:

```toml
[automation]
enabled = true
mode = "execute"
auto_intake = true
auto_plan = true
auto_dispatch = true
risk_ceiling = "low"
approval_required_for = ["release", "security", "provider-write", "destructive"]
event_sources = ["sula-cli", "provider", "status", "artifact", "workflow", "external"]
```

The completed orchestration capability adds an optional `[orchestration]` section. It defaults to enabled with `runner = "dry-run"`.

Current Sula orchestration contract:

```toml
[orchestration]
enabled = true
mode = "ticket-runner"
task_source = "local"
runner = "dry-run"
tasks_path = "docs/workflows/tasks.json"
workspace_root = ".sula/local/workspaces"
workspace_mode = "none"
trust_profile = "local-sandboxed"
max_concurrent_runs = 1
max_retry_count = 1
max_run_minutes = 30
daily_budget_minutes = 120
unattended_risk_ceiling = "low"
require_human_approval_for = ["release", "security", "provider-write", "destructive"]
status_surface = "sula"
```

The current implementation keeps the safe local/dry-run adapter pair as the default and implements `shell-command`, `codex-sdk`, and `codex-app-server` behind explicit runner configuration. Sula still treats every runner as an adapter boundary: Core owns task normalization, workspace policy, event capture, and closeout evidence, while project-local commands or app servers own actual agent execution.

The completed contract must keep these concerns explicit:

- enabled state
- task source
- runner
- workspace isolation
- trust profile
- concurrency
- retries and timeouts
- budget
- risk ceiling
- approval requirements
- observability surface

## Task Source Model

Sula should normalize all task sources into one task object.

Required normalized fields:

- `id`
- `source_kind`
- `source_url`
- `identifier`
- `title`
- `description`
- `state`
- `priority`
- `labels`
- `blocked_by`
- `project_slug`
- `acceptance_criteria`
- `validation_requirements`
- `risk_hints`
- `created_at`
- `updated_at`

Initial source kinds should be:

- `local-task`
- `github-issue`
- `linear-issue`
- `provider-task-document`

The source adapter reads and normalizes tasks. It should not decide business completion alone.

Current implementation:

- Sula entrypoints such as `check`, `doctor`, `status`, `query`, `sync`, `artifact locate`, and `artifact refresh` can record automation events under `.sula/state/automation/`
- failed checks and doctor runs become durable automation intents when `[automation].auto_intake = true`
- automation intents are exposed as orchestration tasks when `[automation].auto_plan = true`, even when no local task file exists
- automatic dispatch is enabled by default, but only eligible low-risk tasks dispatch, `[orchestration].enabled = true` must hold, and no approval category can be required
- the default runner remains `dry-run`, so automatic dispatch creates auditable run records before any project opts into a real runner
- local task source reads JSON from `orchestration.tasks_path`
- the file may be either a JSON array or an object with a `tasks` array
- `provider-task-document` reads a project-local provider/external task mirror from `orchestration.tasks_path`, supporting Markdown checklist lines and JSON task mirrors
- `provider-api` reads tasks through a configured provider adapter using `provider_task_item_id`, `provider_task_item_kind`, and `provider_task_item_url`
- `orchestration intake` captures CLI/user intent into that local task file with `source_kind = "cli-intent"`
- `orchestration trigger` remains available for backfill and debugging, but normal Sula usage should not rely on users remembering to trigger work by hand
- `orchestration tasks --json` emits normalized task objects
- missing acceptance criteria, blockers, terminal states, risk above ceiling, or approval categories make a task ineligible

## Runner Model

Sula runner adapters should share one contract.

Required runner operations:

- `prepare`
- `start`
- `stream_events`
- `cancel`
- `summarize`
- `collect_evidence`
- `cleanup`

Initial runner kinds:

- `dry-run`
- `codex-sdk`
- `codex-app-server`
- `shell-command`

Sula Core should treat runner implementation details as adapter mechanics. The Core contract is about inputs, safety, event capture, and completion evidence.

Current implementation:

- `dry-run` is implemented and records scheduling/policy/evidence without mutating project files
- `shell-command` is implemented as a real local runner when explicitly configured with `runner_command`
- `codex-sdk` is implemented as a JSON-over-stdin command adapter that can return normalized status, touched files, validation evidence, links, and metrics
- `codex-app-server` is implemented as an HTTP JSON adapter with optional bearer-token lookup through `runner_token_env`
- shell-command runs are blocked unless they use an isolated workspace or explicitly allow project-root execution
- non-dry-run adapters are reserved but blocked with explicit reasons
- run records are appended to `.sula/state/orchestration/runs.jsonl`

## Workspace Model

Each task run must use an isolated workspace.

Required invariants:

- workspace path stays under configured workspace root
- workspace key is sanitized from task identifier
- runner cwd is the task workspace
- task workspace is never the Sula Core source tree unless the policy explicitly allows self-work
- cleanup behavior is policy-driven and recorded

Workspace modes:

- `none`: inspection-only or local project operations with no isolated copy
- `branch`: branch isolation inside project root
- `worktree`: Git worktree per task
- `copy`: filesystem copy per task
- `container`: containerized workspace per task
- `remote`: remote worker workspace

## Risk And Eligibility Policy

Sula should not dispatch every task automatically.

Risk classes:

- `low`: documentation, formatting, read-only refresh, status digest, deterministic checks
- `medium`: normal code changes, artifact generation, provider import plans, non-destructive sync
- `high`: release, security, auth, provider writes, destructive cleanup, schema migration, data mutation
- `blocked`: missing acceptance criteria, missing credentials, ambiguous ownership, unsafe prompt content

Eligibility rules:

- low-risk tasks can run unattended when orchestration is enabled
- medium-risk tasks can run unattended only when the project policy allows it
- high-risk tasks require explicit approval or plan-only execution
- blocked tasks produce a clarification or plan artifact rather than code changes
- tasks with non-terminal blockers do not dispatch
- stale task source data must be refreshed before dispatch when freshness intent exists

## Safety Requirements

Completed orchestration must include these controls:

- explicit trust profile in manifest or runtime config
- allowlist of eligible task sources and projects
- allowlist of runner kinds
- sandbox or workspace isolation declaration
- stop-all command
- per-run cancel command
- budget exhaustion behavior
- secret redaction in logs
- prompt-injection warning for externally-authored task text
- destructive-operation approval gate
- provider-write approval gate
- release approval gate

No agent run should be able to silently mutate durable Sula state outside the normal Sula command surfaces.

Current command surface:

- `orchestration status`
- `orchestration tasks`
- `orchestration intake`
- `orchestration trigger --source-kind ... --identity-key ...`
- `orchestration run --task-id ...`
- `orchestration close --run-id ...`
- `orchestration cancel --run-id ...`
- `orchestration stop-all`
- `orchestration doctor`

`orchestration close` enforces the completed-state principle that runner success alone cannot accept work. Dry-run scheduling evidence can move a run to review, but accepted closeout requires additional validation evidence such as checks, reviewed artifacts, touched-file summaries, links, or operator-provided evidence. Accepted closeout now evaluates task-specific validation requirements, resolves touched files in the runner workspace or project root, resolves references through `verification_adapters` for local files, artifact catalog entries, provider metadata, PR URLs, and ordinary URLs, and runs `sula check` when the task or evidence requests it. `remote_verification_policy` controls whether PR/provider remote verification is reference-only, opportunistic, or required. When `[agent_behavior]` requires verification or success criteria, accepted closeout must also include evidence for those policy gates.

## Observability And Records

Sula should persist orchestration records under `.sula/state/orchestration/`.

Recommended files:

- `.sula/state/orchestration/runs.jsonl`
- `.sula/state/orchestration/latest.json`
- `.sula/state/orchestration/tasks.json`
- `.sula/state/orchestration/budgets.json`

Automation records live separately under `.sula/state/automation/`:

- `.sula/state/automation/events.jsonl`
- `.sula/state/automation/intents.jsonl`
- `.sula/state/automation/latest.json`

Each run record should include:

- run id
- task id and source
- runner kind
- workspace path
- risk class
- start/end timestamps
- status
- cost and runtime counters
- touched files summary
- validation evidence
- final disposition
- links to PRs, artifacts, change records, or provider items
- reusable lessons proposed for memory or feedback

`status --json` and `portfolio orchestration --json` expose orchestration summaries. `portfolio query --json` remains the cross-project content search surface.

## Completion Semantics

Runner success is not task success.

A task can close only when:

- acceptance criteria are addressed or explicitly marked not applicable
- required validation evidence exists
- workspace changes are summarized
- project state is synchronized through Sula checks when applicable
- high-risk actions have required approvals
- reusable lessons are either promoted, captured as feedback, or explicitly discarded

Final dispositions:

- `accepted`
- `human-review`
- `blocked`
- `failed`
- `abandoned`
- `superseded`
- `discarded`

## Learning Loop

Completed orchestration should strengthen Sula over time.

Possible promotion paths:

- project state update
- durable decision
- risk
- workflow artifact
- reusable rule
- feedback bundle
- managed template improvement
- new check or doctor warning
- documentation update

The agent should propose promotion candidates, but Sula should require explicit review before durable memory or managed templates change.

## Expected Benefits

Completed orchestration should provide:

- `3x` to `10x` higher throughput for routine maintenance and well-scoped software work
- `50%` to `80%` less human context switching for agent-supervised execution
- `70%+` lower multi-project status inspection time through portfolio-level orchestration state
- `40%` to `70%` lower stale artifact and stale state risk when provider refresh and daily checks are automated
- stronger auditability for failed, abandoned, and accepted AI work
- lower-cost exploration through isolated speculative tasks
- compounding improvement through memory and feedback promotion

These are target outcomes, not release guarantees. Measurement should use accepted outcomes, rework rate, validation pass rate, and cost per accepted result rather than raw PR count.

## Non-Negotiable Constraints

- Sula remains portable across adopted projects.
- Orchestration is available by default through the non-mutating `dry-run` runner.
- Core stays dependency-light.
- Heavy runtimes live in adapters or plugins.
- Project-owned truth is not replaced by agent prompts.
- All machine-facing surfaces should support JSON.
- Sync impact must be documented before managed templates change.
