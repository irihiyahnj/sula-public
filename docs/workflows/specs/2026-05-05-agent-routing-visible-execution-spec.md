# Agent routing and visible execution status

## Metadata

- date: 2026-05-05
- kind: spec
- project: Sula
- workflow pack: operating-system
- workflow slot: design
- storage provider: local-fs
- execution mode: review-heavy
- design gate: complex-only
- plan gate: multi-step
- review policy: task-checkpoints

## Summary

This spec defines a Sula-native agent routing and visible execution layer.

The feature lets a project route planning, implementation, verification, and review to different agent providers and models while keeping users informed, in any supported coding CLI, about:

- the current host/chat agent
- the planning model
- the execution model
- the review model
- the active task and stage
- what has completed, what is running, what is next, and why a run is blocked

The immediate product problem is quota and visibility. A high-capability model is often worth using as the planner and reviewer, but it is wasteful as the default implementation engine for every edit. At the same time, Sula task progress must be visible through Sula itself, not only through one client such as Claude Code.

## Problem Statement

Sula already has task intake, orchestration runs, runner adapters, closeout gates, and agent behavior policy. It does not yet have a first-class way to express:

1. which agent role should use which provider and model
2. which roles may mutate files
3. how planner-reviewer feedback loops should continue until acceptance
4. what model is currently doing work
5. how every CLI should display the same task list and active stage

This creates two failures:

- Users burn expensive model quota on low-level implementation work that could be delegated to a cheaper executor.
- Users lose situational awareness when the task checklist is rendered by a specific client UI instead of by Sula's own cross-tool state.

## Goals And Non-goals

| Category | Details |
| --- | --- |
| Goals | Add a portable role-based model routing contract; make active work visible through Sula CLI and JSON surfaces; support planner-executor-verifier-reviewer loops; keep provider credentials local; preserve runner adapter boundaries; make current and selected models obvious to the user. |
| Non-goals | Change the model of the currently running chat session from inside Sula; require one AI provider; store API keys in project truth; make unattended code mutation the default; replace client-native task UIs; make Python 3.11+ or third-party packages mandatory. |

## Design Principles

- Sula Core owns routing policy, state, safety gates, and visibility.
- External runners own provider-specific API mechanics.
- The project manifest records durable preferences, not secrets or current account state.
- The current host/chat model is treated as an observed session fact when available, not a value Sula can reliably force.
- Planner and reviewer roles should be read-only by default.
- Executor roles may write only through an explicitly configured runner and workspace policy.
- Verification is command/evidence first. It may use a model for interpretation, but tests and Sula checks remain stronger evidence.
- Every important state transition must be available as human-readable CLI output and JSON.

## Role Model

Sula should distinguish these roles:

| Role | Purpose | Default Write Access | Typical Model Choice |
| --- | --- | --- | --- |
| `host` | The current interactive CLI/chat agent the user is talking to | inherited from client | user-selected, often unknown to Sula |
| `planner` | Read project context, decompose work, produce plan and acceptance criteria | false | strongest reasoning model |
| `executor` | Apply bounded code/doc changes from the approved plan | true when configured | cost-efficient coding model |
| `verifier` | Run commands, collect evidence, summarize failures | false unless command runner needs workspace writes | deterministic shell first, optional small model |
| `reviewer` | Review diff and evidence against plan and acceptance criteria | false | strongest reasoning model |
| `acceptor` | Human or policy gate that accepts completion | false | human by default |

The `host` role is special. Sula can display it only when the CLI or user provides metadata through environment variables, command flags, or MCP session metadata. If unavailable, the status surface must say `unknown`, not guess.

## Proposed Manifest Contract

The durable project policy should live in `.sula/project.toml`:

```toml
[agent_routing]
enabled = true
mode = "plan-execute-review"
visibility = "always"
default_budget_policy = "cost-aware"
budget_breach_behavior = "ask"
executor_context_mode = "bounded"
executor_output_contract = "json"
executor_default_reasoning_effort = "high"
executor_max_turns = 8
executor_max_run_minutes = 5
executor_max_cost_cents = 30
max_review_cycles = 3
on_review_fail = "return-to-executor"
require_final_acceptance = true

[agent_routing.roles.planner]
provider = "openai"
model = "gpt-5.5"
reasoning_effort = "xhigh"
write_access = false

[agent_routing.roles.executor]
provider = "deepseek"
model = "deepseek-flash"
reasoning_effort = "high"
write_access = true
workspace_mode = "copy"

[agent_routing.roles.verifier]
provider = "local"
model = "shell"
write_access = false

[agent_routing.roles.reviewer]
provider = "openai"
model = "gpt-5.5"
reasoning_effort = "xhigh"
write_access = false
```

Allowed `mode` values:

| Mode | Behavior |
| --- | --- |
| `off` | No role routing. Existing orchestration behavior continues. |
| `assist` | Sula displays recommended roles and model hints but does not dispatch model-specific runners. |
| `plan-execute-review` | Planner produces plan, executor mutates, verifier checks, reviewer gates, executor retries when review fails. |
| `review-only` | Current host or existing runner implements; configured reviewer validates before closeout. |
| `executor-only` | A configured executor runs tasks without model-based planning or review, still gated by Sula closeout. |

## Local Provider Contract

Provider mechanics and secrets are machine-local:

```json
{
  "providers": {
    "openai": {
      "kind": "openai-compatible",
      "endpoint_env": "SULA_OPENAI_BASE_URL",
      "api_key_env": "SULA_OPENAI_API_KEY",
      "allowed_roles": ["planner", "reviewer"]
    },
    "deepseek": {
      "kind": "openai-compatible",
      "endpoint_env": "SULA_DEEPSEEK_BASE_URL",
      "api_key_env": "SULA_DEEPSEEK_API_KEY",
      "allowed_roles": ["executor"]
    }
  }
}
```

Recommended local path: `.sula/local/agent-providers.json`.

This file must not be treated as project truth and must not be copied into managed templates. It may name environment variables but must not contain raw API keys.

## Visible Execution State

Sula should own a cross-CLI visible state surface under ignored runtime state:

| File | Purpose |
| --- | --- |
| `.sula/state/orchestration/events.jsonl` | Append-only stage and role events. |
| `.sula/state/orchestration/latest.json` | Latest project orchestration summary. |
| `.sula/state/orchestration/active.json` | Active task, role, stage, model, and next action. |
| `.sula/state/orchestration/budgets.json` | Optional token, cost, minute, and retry counters. |

Minimum event shape:

```json
{
  "event_id": "evt_20260505_001",
  "timestamp": "2026-05-05T00:00:00Z",
  "run_id": "run_20260505_001",
  "task_id": "task_001",
  "stage": "execute",
  "role": "executor",
  "provider": "deepseek",
  "model": "deepseek-flash",
  "reasoning_effort": "high",
  "state": "running",
  "summary": "Applying bounded implementation changes from approved plan.",
  "next_action": "Run verifier checks after executor returns.",
  "write_access": true,
  "workspace": ".sula/local/workspaces/task_001",
  "cost_estimate": {
    "tokens_input": 0,
    "tokens_output": 0,
    "cost_usd": null
  }
}
```

The status display should render this information in plain text:

```text
Sula active execution
Task: Add agent routing and visible execution status
Mode: plan-execute-review
Host: Codex CLI / model unknown
Planner: openai:gpt-5.5 / xhigh / read-only / completed
Executor: deepseek:deepseek-flash / high / write-enabled / running
Verifier: local:shell / pending
Reviewer: openai:gpt-5.5 / xhigh / pending
Cycle: 1 of 3
Next: run verification after executor returns
```

## CLI And Agent Entry Surfaces

Sula should add these human and machine surfaces:

| Command | Purpose |
| --- | --- |
| `sula session start` | Standard CLI entry banner: memory digest pointer, active tasks, active model roles, required next command. |
| `sula orchestration status` | Existing status should include active role/model/stage. |
| `sula orchestration status --compact` | Render one compact English execution line with run state, task completion count, main model/depth, executor model/depth/runner effort, workspace, executor budget, elapsed time, cost, last event, and next action. |
| `sula orchestration status --watch` | Poll and render active execution state until the run finishes or is cancelled. |
| `sula orchestration timeline` | Render recent run events from `events.jsonl`. |
| `sula agent-routing status --json` | Emit resolved routing policy, local provider readiness, active role, and model visibility. |
| `sula agent-routing doctor` | Validate manifest fields, local provider config, role permissions, and missing credentials without printing secrets. |

Projected AI instruction files should be updated so every supported coding CLI starts with the same Sula-owned context:

```text
Start each session by running or reading the output of:
python3 scripts/sula.py session start --project-root .
```

This is the practical fix for the current Claude Code versus Codex CLI mismatch. Sula cannot force every client UI to render a native checklist, but it can make the checklist a Sula command that every client is instructed to call and every human can run manually.

## Runner Flow

The first implementation should reuse existing runner boundaries instead of adding provider SDK dependencies to Sula Core.

1. `orchestration run` resolves `agent_routing`.
2. Sula writes an `active.json` record and a `planner.started` event.
3. A configured runner receives a JSON request with `role`, `model_hint`, `write_access`, `workspace`, task data, project policy, acceptance criteria, bounded executor contract, and minimal execution packet.
4. Planner returns a plan artifact or structured plan summary.
5. Sula dispatches executor with the approved plan.
6. Executor returns touched files, patch summary, and implementation notes.
7. Sula runs verifier commands and records evidence.
8. Reviewer receives plan, diff summary, touched files, and verification evidence.
9. If reviewer fails the work, Sula creates a review-fix cycle and returns structured feedback to executor.
10. Sula stops when reviewer accepts, human accepts, the task is blocked, or `max_review_cycles` is reached.

## Current Host Model Visibility

Sula should support optional session metadata:

| Source | Example |
| --- | --- |
| environment | `SULA_HOST_AGENT=codex-cli`, `SULA_HOST_PROVIDER=openai`, `SULA_HOST_MODEL=gpt-5.5` |
| CLI flags | `sula session start --host-agent codex-cli --host-model gpt-5.5` |
| MCP metadata | connector-provided session metadata when available |

If none is present, Sula reports:

```text
Host: unknown current CLI model
```

This is important. Guessing the host model would create false confidence and bad cost accounting.

## Safety And Policy Gates

- Planner and reviewer are read-only unless explicitly overridden.
- Executor write access requires real runner opt-in and compatible `workspace_mode`.
- Raw provider keys never appear in manifest, status, events, or logs.
- Missing provider config fails closed with a clear blocked state.
- Provider role allowlists prevent using an executor-only provider for review or a review-only provider for code mutation.
- Sula closeout still requires validation evidence; model approval alone is insufficient.
- Runs must be cancellable and resumable from Sula state.
- Two active mutating runs for the same project should be blocked unless policy explicitly allows concurrency.
- Prompt injection risk must be treated as a task risk input. Provider-backed content and external issues are untrusted until summarized into task-owned acceptance criteria.

## Budget And Cost Policy

Sula should track budget in three layers:

| Layer | Purpose |
| --- | --- |
| manifest | durable policy such as `default_budget_policy`, daily limits, max cycles |
| local provider config | optional per-provider cost hints and hard limits |
| runtime state | observed tokens, estimates, retries, elapsed minutes |

Budget breach behavior should be explicit:

| Setting | Behavior |
| --- | --- |
| `stop` | Stop immediately and mark run blocked. |
| `ask` | Stop before the next paid model call and require user approval. |
| `downgrade` | Switch to configured fallback role/model if available. |

Default should be `ask`.

## Implementation Plan

### Phase 1: Visibility first

- Add `session start` command.
- Add `active.json` and `events.jsonl` writer helpers.
- Make `orchestration status` display active task, active stage, and resolved runner.
- Add `orchestration status --compact` for a single-line tool view suitable for long-running chat updates.
- Add `orchestration status --watch`.
- Update `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `GEMINI.md`, and templates to tell every CLI to show Sula session status at startup.

Done when Codex CLI, Claude Code, and a plain terminal can all show the same active task list and current stage using Sula commands.

### Phase 2: Routing schema and doctor

- Add `[agent_routing]` manifest parsing, defaults, schema validation, status payloads, and docs.
- Add `.sula/local/agent-providers.json` loader.
- Add `agent-routing status` and `agent-routing doctor`.
- Add tests for no-secret output, missing provider config, invalid role/provider mapping, and disabled routing.

Done when users can see planned, executor, verifier, and reviewer model choices before any paid call happens.

### Phase 3: Role-aware runner requests

- Extend `codex-sdk`, `codex-app-server`, and `shell-command` request JSON with `role`, `model_hint`, `write_access`, and `routing_cycle`.
- Preserve existing runner behavior when `[agent_routing]` is absent.
- Record role transitions in `events.jsonl`.
- Gate executor writes through workspace and risk policy.

Done when a runner can tell whether it is acting as planner, executor, verifier, or reviewer.

### Phase 4: Review loop

- Implement `plan-execute-review` loop with `max_review_cycles`.
- Add structured reviewer feedback returned to executor.
- Require verifier evidence before reviewer acceptance.
- Store final route summary in run records and closeout payloads.

Done when the expensive reviewer can reject work and Sula automatically sends bounded feedback to the executor until accepted or blocked.

### Phase 5: Budget enforcement

- Add runtime budget counters and optional provider cost hints.
- Add budget breach behavior.
- Surface token/cost/minute estimates in status.
- Add tests for budget stop, ask, and fallback behavior.

Done when cost-aware routing is enforceable, not just documented.

## Verification Plan

- Unit tests for manifest parsing and defaults.
- Unit tests for local provider config loading without secret leakage.
- Unit tests for `session start`, active state rendering, and JSON payloads.
- Fixture tests for Codex-style unknown host model and explicit host model metadata.
- Runner request compatibility tests for old runner configs and role-aware configs.
- End-to-end orchestration fixture for planner-executor-verifier-reviewer happy path.
- End-to-end fixture for reviewer rejection followed by executor retry.
- Budget breach fixture for `ask` behavior.
- Existing release gates:
  - `python3 scripts/sula.py check --project-root .`
  - `python3 scripts/sula.py doctor --project-root . --strict`
  - `python3 -m unittest discover -s tests -v`

## Open Questions

- Should role routing live entirely under `[agent_routing]`, or should some fields extend `[orchestration]` to reduce manifest sprawl?
- Should Sula provide a tiny local OpenAI-compatible runner script, or only define the JSON contract and let projects provide runner commands?
- What is the minimum useful cost accounting if providers do not return token usage consistently?
- Should `session start` be human-first by default with `--json` for tools, or should it auto-detect non-interactive use?
- Should routing state be kept only under `.sula/state/orchestration/`, or should a shorter `.sula/state/session.json` exist for fast startup reads?

## Things Easy To Miss

- The host/chat model cannot always be detected. Sula must show unknown rather than inventing an answer.
- Client-native task lists are not portable. Sula needs its own CLI and JSON status, even if clients also render their own checklist.
- A cheap executor can produce expensive review churn. `max_review_cycles` and budget policy are mandatory.
- Provider outputs may include untrusted instructions from issue text or provider documents. Planner summaries and acceptance criteria must control the executor prompt.
- Concurrent CLIs can race. Active mutating runs need a simple project lock or single-writer policy.
- Local provider config must name env vars, not contain credentials.
- Model names change. Sula should validate shape and provider readiness, but should not hard-code every model catalog.
- Review success is not verification. Tests, Sula checks, touched files, and closeout evidence remain required.
- A failed or cancelled run still needs visible state and cleanup guidance.
- The feature must work in service/document projects, not just software repos.

## Architecture Boundary Check

- highest rule impact: preserved; Sula owns reusable routing, visibility, and safety policy while project-owned tasks, acceptance criteria, source docs, and code changes remain project truth.
- portability impact: positive; the design avoids binding Sula to Codex, Claude Code, DeepSeek, OpenAI, or one UI.
- dependency impact: controlled; provider API mechanics remain in runner adapters or local scripts, not mandatory Sula Core dependencies.
- sync impact: managed templates need startup instruction updates, but runtime state and local provider config stay outside central managed truth.
