# Symphony Orchestration Absorption Execution Plan

## Metadata

- date: 2026-04-30
- status: active plan, automation and orchestration source-release slice landed
- owner: Sula Core maintainers
- source reference: `docs/reference/symphony-orchestration-absorption-plan.md`
- task: make Sula capable of completed Symphony-style orchestration while preserving Sula's project-operating-system boundary

## Execution Culture

Future AI sessions working on this upgrade must follow this plan before implementation.

Rules:

- Start from the reference document, not from chat history.
- Preserve Sula's highest rule: centrally managed OS files and project-owned business truth stay separate.
- Prefer contracts, adapters, and source-first artifacts over one hardcoded external workflow.
- Keep Core dependency-light; put heavy runtimes behind optional adapters.
- Treat every implementation step as sync-impacting until proven otherwise.
- Write JSON machine surfaces before polished UI surfaces.
- Add tests for manifest, CLI output, state records, and safety gates before expanding automation.
- Do not enable unattended execution by default.

## Final Product Definition

The completed feature is present when Sula can:

- declare orchestration policy in a manifest
- declare automation policy in a manifest
- observe normal Sula entrypoints and external adapter events without manual trigger rituals
- classify useful events into durable intents
- expose automation intents as orchestration tasks
- automatically dispatch eligible low-risk work into the default dry-run runner without requiring a manual trigger
- inspect configured task sources
- normalize tasks from at least local and one external source
- decide eligibility and risk
- create isolated task workspaces
- run at least one real agent runner and one dry-run runner
- record run events and outcomes under `.sula/state/orchestration/`
- expose current orchestration state through `status --json`
- expose portfolio-level orchestration summaries
- enforce cost, retry, timeout, approval, and stop-all controls
- require validation evidence before accepted closeout
- propose reusable memory and feedback promotions

## Implementation Progress

Landed in the first implementation slice:

- optional `[orchestration]` manifest contract, enabled by default with the non-mutating `dry-run` runner
- optional `[automation]` manifest contract, enabled in execute mode by default with dry-run orchestration as the default runner boundary
- schema and example manifest coverage
- project config accessors and JSON payload exposure
- local JSON task source adapter
- provider task document adapter for Markdown checklist and JSON mirror files
- provider API task source adapter with provider task item identity and fixture-backed Google Drive task ingestion
- CLI/user-intent intake into local orchestration tasks
- generic trigger intake for Sula commands, webhooks, provider task documents, and external task surfaces
- event-driven automation intake for normal `check`, `doctor`, `status`, `query`, `sync`, and artifact freshness entrypoints
- automation events, intents, and latest state under `.sula/state/automation/`
- automation intents exposed as orchestration tasks without a required local task file
- default execute-mode auto-dispatch for eligible low-risk intents behind risk ceiling, approval, orchestration enablement, and dry-run runner gates
- deterministic normalized task model
- risk, approval, blocker, acceptance-criteria, and budget gates
- dry-run runner record path
- `shell-command` real runner adapter with isolated copy workspace support and command evidence capture
- `codex-sdk` runner adapter using a JSON-over-stdin command contract and normalized evidence response
- `codex-app-server` runner adapter using an HTTP JSON request contract and optional bearer-token lookup
- closeout evidence gate for accepted runs
- Sula-native `[agent_behavior]` policy with run-record quality checklists and verification/success-criteria closeout gates
- closeout evaluation payload and review-required promotion candidates for reusable lessons
- `.sula/state/orchestration/` records for runs, latest status, task snapshots, and budgets
- `orchestration status`, `tasks`, `intake`, `run`, `close`, `cancel`, `stop-all`, and `doctor`
- `status --json` orchestration summary
- portfolio-level orchestration summary
- closeout evaluator for task validation requirements, touched files, links/artifacts, and requested `sula check`
- manifest-controlled closeout verification adapters for local files, catalog artifacts, provider metadata, PR URLs, and ordinary URLs
- remote verification policy for PR/provider references with `reference-only`, `opportunistic`, and `required` modes
- unit coverage for enabled dry-run defaults, CLI intent intake, and closeout evidence

Still pending:

- credentialed real-project canary runs for GitHub PR verification, provider-backed artifact verification, and Codex runner endpoints
- more automation classifiers from real project provider, status, and workflow failure patterns
- authenticated provider task adapters beyond the current Google Drive task-document path when a real provider task API is selected
- production hardening around long-running remote runner cancellation and streamed runner events

## Workstreams

### Contract And Schema

Goal: make orchestration a first-class optional Sula capability.

Required outputs:

- `[orchestration]` manifest section
- schema validation
- example manifest values
- project config accessors
- `doctor` checks for invalid policy
- documentation in reference docs

Acceptance:

- missing `[orchestration]` keeps existing projects valid
- `enabled = true` with `runner = "dry-run"` is the default behavior
- invalid runner, task source, budget, trust, or risk values are reported clearly
- JSON outputs include orchestration config when present

### Task Source Abstraction

Goal: support tracker-neutral task ingestion.

Required outputs:

- normalized task model
- local task-file adapter
- at least one external adapter design or implementation
- blocker handling
- active/terminal state mapping
- freshness metadata

Acceptance:

- local tasks can be listed without network access
- task normalization is deterministic
- ambiguous or incomplete tasks are classified as blocked
- adapter-specific fields do not leak into Core logic

### Runner Abstraction

Goal: allow multiple execution engines without coupling Core to one agent.

Required outputs:

- runner interface
- dry-run runner
- Codex runner adapter
- event normalization
- cancellation behavior
- evidence collection

Acceptance:

- dry-run can exercise the full scheduler without mutating project files
- Codex runner can be disabled without breaking Core
- runner failures map to normalized failure classes
- runner events are persisted as Sula run records

### Workspace Isolation

Goal: ensure task work never escapes its assigned workspace.

Required outputs:

- workspace key sanitizer
- workspace root resolver
- branch/worktree/copy mode planning
- path safety checks
- cleanup policies

Acceptance:

- workspace paths cannot escape the configured root
- each task gets a deterministic workspace identity
- cleanup is recorded
- Sula self-work requires explicit policy

### Orchestrator State And CLI

Goal: provide a usable orchestration control plane.

Required outputs:

- `orchestration status`
- `orchestration tasks`
- `orchestration run`
- `orchestration cancel`
- `orchestration stop-all`
- `orchestration doctor`
- JSON support for every command
- run registry files under `.sula/state/orchestration/`

Acceptance:

- commands work without external services when using local task source and dry-run runner
- repeated commands are idempotent where practical
- cancellation and stop-all are safe to run repeatedly
- status surfaces show running, retrying, blocked, failed, accepted, and human-review states

### Safety, Cost, And Approval Gates

Goal: prevent background agents from becoming uncontrolled mutation engines.

Required outputs:

- risk classifier
- eligibility gate
- budget counters
- retry caps
- timeout caps
- approval requirements
- secret redaction rules
- destructive-operation policy

Acceptance:

- high-risk tasks do not run unattended by default
- budget exhaustion prevents new dispatches
- missing credentials produce blocked state, not silent retries
- destructive or provider-write operations require policy allowance

### Verification And Closeout

Goal: make accepted work evidence-based.

Required outputs:

- validation evidence model
- closeout evaluator
- integration with `check`
- links to artifacts, PRs, or change records
- final disposition vocabulary

Acceptance:

- runner success alone cannot mark a task accepted
- missing validation creates human-review or blocked state
- accepted runs include evidence and touched-file summary
- failed and abandoned runs remain auditable

### Memory And Feedback Loop

Goal: convert repeated run lessons into durable Sula improvement.

Required outputs:

- promotion candidate schema
- memory capture integration
- feedback bundle integration
- review-required promotion flow

Acceptance:

- agents can propose lessons
- durable memory is not changed without review
- reusable managed-file fixes route through feedback bundles
- low-signal scratch notes can be discarded

### Portfolio Integration

Goal: make orchestration useful across many adopted projects.

Required outputs:

- portfolio orchestration summary
- cross-project blocked/running/review query
- stale project task detection
- provider-backed project compatibility

Acceptance:

- portfolio can report projects needing human attention
- non-code projects can use orchestration for refresh, document, and status tasks
- project-local policies remain authoritative

## Suggested Implementation Order For Future AI

Use this sequence unless a maintainer explicitly changes the plan:

1. Add contracts, docs, and schema with orchestration enabled by default through `dry-run`.
2. Add automation execute-mode policy so normal Sula entrypoints create events, intents, and dry-run dispatches without manual trigger.
3. Add local task source and dry-run runner.
4. Add run registry and JSON CLI status.
5. Add workspace safety.
6. Add risk, budget, timeout, retry, and approval gates.
7. Add verification and closeout.
8. Add one real runner adapter.
9. Add one external task-source adapter.
10. Add memory and feedback promotion proposals.
11. Add portfolio summaries.

## Done Criteria

The completed upgrade is done only when:

- `doctor --strict` passes
- `check` passes
- docs describe sync impact and defaults
- examples cover disabled orchestration and enabled dry-run orchestration
- tests prove a failed normal Sula entrypoint creates automation intent without manual trigger
- tests prove execute-mode automation can dispatch eligible low-risk intent without bypassing orchestration gates
- tests cover manifest parsing, task normalization, runner failure, workspace safety, budget gates, and closeout evidence
- no existing adopted project is forced into orchestration by sync
- rollback is documented

## Rollback Strategy

Rollback must be possible by:

- setting `[orchestration].enabled = false`
- setting `[automation].mode = "observe"` or `[automation].enabled = false`
- stopping all running orchestration processes
- leaving run records as audit history
- preserving project-owned task and artifact files
- avoiding destructive cleanup unless explicitly requested

## Notes For Later Agents

If you are executing this plan:

- Do not begin with a daemon.
- Do not begin with Linear.
- Do not begin with a dashboard.
- Begin with contracts, local tasks, dry-run execution, run records, and safety gates.
- If a change would make Python 3.11+, Node, Elixir, or third-party packages mandatory for Sula Core, stop and redesign it as an optional adapter.
