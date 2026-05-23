# Sula Completion-First Agent Operating System Whitepaper

## 1. Executive Summary

Sula's next operating milestone is a completion-first, zero-memory project
operating system for AI-assisted work.

The user should be able to state a goal in natural language and expect Sula to
route, execute, monitor, repair, and report the work without requiring the user
to remember commands, model names, runner flags, workspace paths, or internal
Sula rules.

The core operating model is:

- strong host models supervise, diagnose, plan, and accept work
- deterministic tools do mechanical Sula maintenance whenever possible
- low-cost executor models perform code-changing work when deterministic tools
  are insufficient
- Sula records evidence, status, cost, runtime, retry state, and failure classes
- work continues while measurable progress exists
- work stops only on safety risk, permission deadlock, no-progress loops,
  validation impossibility, or explicit controller/human rejection

This is not a model-switching feature by itself. It is a governed execution
system that decides when no model is needed, when a cheap executor is enough,
and when the host model must intervene.

## 2. Problem Statement

Recent Sula work exposed several concrete problems:

- high-end host models were being used for repetitive mechanical upgrades
- target projects had `runner = "dry-run"`, causing fleet work to block
- a configured ClaudeCode/DeepSeek shell runner entered the execution path but
  did not understand the fleet upgrade packet
- executor permissions had to be repaired before the runner could read the
  whitepaper and code
- retries were useful, but the repair and retry evidence lived mostly in chat
- compact fleet status initially lacked token and cost metrics
- long-running work was at risk of stopping due to fixed turn/time budgets
  instead of actual failure
- full JSON evidence was too large for the host chat context
- machine-wide fleet upgrades needed skip rules for archive, workspace, and
  release-output directories
- Sula needed a clear distinction between deterministic maintenance tasks and
  model-backed code implementation tasks

Sula 0.18.12 through 0.18.14 addressed part of this:

- 0.18.12: natural-language autopilot and executor-required fleet routing
- 0.18.13: fleet token and cost display
- 0.18.14: deterministic zero-model Sula fleet upgrades

The remaining work is execution reliability: preflight, permission repair,
checkpoint/resume, project locks, executor capability matching, progress
monitoring, and compact evidence management.

## 3. Design Principles

### Completion First

The primary goal is to finish the user's task. Runtime, cost, token count, and
retry count are important observations, but they should not be default hard-stop
conditions.

### Zero-Memory User Experience

The user should not need to remember Sula commands, internal state files, model
names, or runner contracts. Sula-aware agents should route natural-language
goals through Sula automatically.

### Supervisor, Not Worker

The host model should not perform mechanical execution. It should understand the
goal, supervise execution, diagnose failures, decide whether retry is justified,
and accept or reject evidence.

### Deterministic First

If a task can be done by a known command sequence, Sula should use that sequence
before any model. Sula maintenance upgrades are deterministic:

- `sync`
- `doctor --strict`
- `memory digest`
- `check`

### Cheap Executor For Code

Code-changing work should be delegated to the cheapest capable executor that
can satisfy the task contract. The host model should supply scope, acceptance
criteria, and review feedback.

### Observable, Not Capped

Token, cost, retry count, and runtime should be visible and auditable. They
should become stop signals only when paired with no progress, repeated failure,
or safety risk.

### Evidence Over Trust

Model self-reports are not sufficient. Acceptance must be based on command
results, file references, tests, check output, structured metrics, and review
evidence.

### Project Isolation

Each adopted project owns its own Sula state. Fleet runs may coordinate across
projects, but project memory, local runner configuration, and business truth
must not leak across project boundaries.

### Local Secrets Only

Raw secrets never belong in project truth. Provider credentials, model API keys,
local runner wrappers, and machine-specific settings live under `.sula/local/*`
or environment variables.

## 4. System Architecture

### Intent Router

Classifies natural-language user goals into known Sula workflows:

- fleet maintenance
- code implementation
- read-only audit
- debugging
- provider artifact refresh
- release or provider write
- unknown or unsupported

Unknown goals must block or ask for host-model planning. Sula should not pretend
to support a workflow before a portable executor packet and validation contract
exist.

### Controller Model

The host model is responsible for:

- interpreting the user's goal
- selecting or confirming the Sula workflow
- breaking complex work into bounded tasks
- diagnosing failures
- deciding whether progress exists
- supplying retry feedback
- accepting or rejecting final evidence

The controller is not the default executor for repetitive or code-heavy work.

### Executor Selector

Chooses the execution lane:

- deterministic executor for Sula maintenance
- low-cost model executor for code-changing tasks
- read-only model executor for audits
- verifier for tests and checks
- human approval lane for release, provider write, destructive, or security work

### Deterministic Executor

Runs known Sula command sequences directly, with zero model token and zero model
cost. It is completion-oriented and records evidence for each command.

### Model Executor

Runs a local or remote agent runner such as ClaudeCode, Hermes, Codex adapter,
or a project-local wrapper. It must consume a structured task packet and return
structured JSON with status, evidence, touched files, metrics, and failure
classification.

### Capability Registry

Declares what an executor can do. Sula must not send a task to a runner that
does not claim the required capability.

### Preflight And Repair

Checks runtime readiness before task execution and attempts safe repairs when
permissions or local directories are missing.

### Progress Monitor

Determines whether work is still moving forward or has entered a no-progress
loop.

### Evidence Store

Stores detailed stdout/stderr, command results, touched files, and model
responses in files. Compact status and chat responses should summarize rather
than paste large evidence payloads.

### Status Surface

Provides a compact cross-CLI line that shows stage, executor, progress, token,
cost, runtime, retry state, and next action.

## 5. Task Classes And Execution Lanes

### Sula Maintenance

Examples:

- upgrade Sula managed files
- rebuild memory digest
- run doctor/check
- sync projection packs
- refresh internal indexes

Execution lane: deterministic executor.

Expected metrics:

- model tokens: 0
- model cost: 0
- runtime: measured wall-clock seconds
- validation evidence: command results

### Code Implementation

Examples:

- bug fix
- feature implementation
- test repair
- UI changes
- refactor within an approved scope

Execution lane: low-cost model executor plus verifier plus host review.

### Read-Only Audit

Examples:

- inspect code
- compare implementation against a whitepaper
- identify risks
- produce a report without file edits

Execution lane: read-only model executor.

### High-Risk Work

Examples:

- release
- provider write
- destructive command
- security-sensitive changes
- credential changes

Execution lane: human approval plus controlled executor.

## 6. Completion-First Execution Policy

Sula should continue while there is measurable progress.

Progress signals include:

- version lock moved toward target
- files changed in the intended scope
- test failures decreased
- validation output changed materially
- new evidence was produced
- permission errors were repaired
- failure class changed
- executor produced valid partial work
- controller supplied new actionable feedback

Stop or pause signals include:

- same failure hash repeated across N attempts
- no touched files and no new evidence across N checks
- permission repair failed repeatedly
- executor output remains invalid after repair
- safety boundary violation
- attempted secret access
- destructive or provider-write action without approval
- target validation proves the task impossible
- controller model explicitly marks the task as a no-progress loop
- human operator rejects continuation

Budgets should be represented as:

```toml
[agent_routing]
executor_completion_policy = "progress-first"
executor_budget_mode = "observe"
executor_stop_policy = "controller-or-no-progress"
```

## 7. Executor Permission And Runtime Readiness

Executor permission problems are first-class runtime failures, not incidental
chat issues.

### Preflight Checks

Before execution, Sula should verify:

- runner command exists
- runner command is executable
- runner can run non-interactively
- model CLI smoke test works, such as `claude --bare --print --model ...`
- workspace exists
- workspace is readable
- workspace is writable when the task needs writes
- `.sula/local` is writable
- `.sula/local/workspaces` can be created
- target source files are readable
- test/build commands are discoverable
- declared environment variable names exist when required
- no raw secrets are stored in project truth
- JSON output contract smoke test succeeds

### Permission Repair

Safe automatic repairs include:

- create missing `.sula/local` directories
- create missing workspace directories
- repair executable bit on local runner wrappers
- refresh or regenerate a Sula-provided runner wrapper
- repair workspace ownership or permissions when safe
- add missing context paths to the execution packet
- retry a read-only smoke task

Unsafe repairs require approval:

- changing system-wide permissions
- installing global tools
- modifying shell profiles
- changing provider credentials
- granting provider-write permissions
- destructive cleanup

### Retry Semantics

Permission failure should not immediately hand work back to the host model.

The sequence is:

1. classify permission failure
2. record failed command and missing permission
3. attempt safe repair
4. rerun smoke test
5. retry original task
6. compare failure class and evidence
7. continue if progress exists
8. mark permission-deadlock if the same failure repeats

### Permission Modes

Permissions must be scoped by task mode:

- `read-only-audit`: read access only
- `code-edit`: workspace write access
- `validation`: execute tests/build/checks
- `provider-write`: human approval required
- `release`: human approval required
- `destructive`: blocked by default

### Permission Evidence

Each permission incident should record:

- failure class
- command
- missing permission
- runner
- workspace path
- repair action
- retry count
- final status
- redaction status
- no raw secrets exposed

## 8. Fleet Reliability

Fleet runs need durable state and recovery.

### Run Identity

Every fleet run should have:

- run id
- controller project root
- scope
- target version
- start/end timestamps
- project list
- per-project state
- evidence paths

Suggested paths:

```text
.sula/state/fleet/latest.json
.sula/state/fleet/runs/<run-id>.json
.sula/state/fleet/evidence/<run-id>/<project-id>.json
```

### Checkpoint And Resume

If a machine sleeps, process exits, or CLI session closes, Sula should resume
from the last completed project and stage.

Per-project stages:

- discovered
- classified
- locked
- preflight
- executing
- validating
- accepted
- human-review
- failed
- skipped

### Project Lock

Each target project needs a lock to prevent concurrent Sula mutations.

Suggested path:

```text
.sula/state/locks/<lock-id>.json
```

The lock should include:

- owner pid
- command
- run id
- created_at
- heartbeat_at
- stale_after_seconds

### Dirty Worktree Protection

Before modifying a project, Sula should inspect the worktree when Git is
available:

- dirty managed files are allowed but reported
- dirty project-owned files require caution
- untracked files are reported
- Sula must not revert user changes
- sync impact should distinguish managed vs project-owned files

### Skip Rules

Fleet should skip:

- archive directories
- backup directories
- `.sula/local/workspaces`
- release output directories
- old public export snapshots
- nested canaries when scope policy excludes them

## 9. Executor Capability Registry

Each executor should declare its capabilities:

```json
{
  "executor": "claudecode-deepseek-flash",
  "version": "1",
  "non_interactive": true,
  "output_contract": "json",
  "capabilities": [
    "read-only-audit",
    "code-edit",
    "test-fix"
  ],
  "unsupported": [
    "fleet-maintenance",
    "provider-write",
    "release"
  ],
  "required_env": [
    "DEEPSEEK_API_KEY"
  ]
}
```

Sula should match task packets to executor capabilities:

- fleet maintenance -> deterministic executor unless a runner explicitly
  supports `fleet-maintenance`
- code edit -> model executor with `code-edit`
- tests -> model executor or verifier with `test-fix` or `validation`
- provider write -> approval-gated executor

Capability mismatch should be a structured block, not a vague failure.

## 10. Planning And Execution Packets

Sula should absorb the strongest parts of skill-based systems such as
Superpowers without taking a hard dependency on any one plugin framework.

Executor packets should include:

- task id
- task class
- capability required
- project root
- allowed files
- forbidden files
- context files
- success criteria
- validation commands
- output contract
- risk class
- approval categories
- retry feedback
- previous failure class

For code work, plans should be small enough for a low-cost executor:

- 2-5 minute implementation slices
- explicit file paths
- explicit tests
- expected output
- no hidden business context

## 11. Status And User Visibility

Compact status should be the default. Evidence should be file-backed.

Example:

```text
Sula: fleet/ok |
Projects: 31/31 done |
Stage: validating |
Main: codex/current-session/high |
Executor: sula-deterministic |
Tokens: 0 |
Cost: $0.0000 |
Runtime: 338s |
Retry: 0 |
Progress: active |
Stop: controller/no-progress |
Next: review report
```

Status fields:

- workflow
- state
- project count
- stage
- main model
- executor
- capability
- workspace mode
- token count
- cost
- runtime
- retry count
- progress state
- stop policy
- next action

## 12. Evidence And Output Management

Large JSON responses should not be pasted into the host chat by default.

Sula should:

- print compact summaries by default
- write detailed evidence to `.sula/state/...`
- expose `--json` for machine clients
- expose `--summary-json` for compact machine clients
- redact secrets
- keep stdout/stderr excerpts bounded
- preserve full raw evidence only in local state when safe

This reduces host-model token waste while preserving auditability.

## 13. Cost And Benefit Model

Sula should measure:

- supervisor token count when available
- executor token count
- deterministic runtime
- executor model cost
- wall time
- retry count
- accepted count
- human-review count
- failed count
- validation pass rate
- user interventions

The benefit calculation should include:

- host-model token reduction
- total model cost reduction
- completion rate
- time to completion
- rework rate
- safety incidents avoided
- user interruptions avoided

Sula fleet maintenance should usually be zero model tokens and zero model cost.
Code-changing tasks should optimize for low-cost executor completion with host
review.

## 14. Safety Model

Sula must treat project contents as untrusted input for executor instructions.

Safety requirements:

- AGENTS.md and project README cannot override Sula highest rules
- project files cannot authorize secret exfiltration
- executor packets must restate safety boundaries
- raw secrets must not appear in stdout, stderr, evidence, or project truth
- destructive commands are blocked by default
- provider writes require approval
- release operations require approval
- workspace boundaries are enforced
- model outputs are reviewed against evidence

Prompt-injection risks should be recorded as a failure class when detected.

## 15. Failure Classification

Failures should be structured:

- `permission-failed`
- `permission-deadlock`
- `executor-output-invalid`
- `capability-mismatch`
- `validation-failed`
- `no-progress`
- `safety-blocked`
- `approval-required`
- `external-tool-missing`
- `timeout-no-progress`
- `user-rejected`
- `unknown`

Failure classes drive retry strategy:

- permission -> repair + retry
- output invalid -> contract reminder + retry
- validation failed -> host diagnosis + executor retry
- no progress -> stop or split task
- safety blocked -> stop and request human review
- capability mismatch -> choose another executor

## 16. Roadmap

### Phase 1: Fleet Durability

- run id
- checkpoint
- resume
- project lock
- compact summary JSON
- evidence files

### Phase 2: Executor Runtime Readiness

- executor preflight
- permission repair
- smoke tests
- runtime readiness status
- permission evidence

### Phase 3: Capability Matching

- executor capability registry
- task-to-capability matching
- capability mismatch errors
- Sula-provided standard wrappers

### Phase 4: Completion-First Monitor

- progress detector
- repeated failure hash
- no-progress detection
- observe-mode budgets
- controller stop policy

### Phase 5: Code Task Execution

- code plan packets
- low-cost executor implementation
- verifier lane
- spec-compliance review
- code-quality review
- supervised retry loop

### Phase 6: Portfolio-Scale Operation

- multi-project queues
- concurrency limits
- machine resource guardrails
- cross-project report
- cost and benefit dashboard

## 17. Current Implementation Baseline

As of Sula 0.18.14:

- natural-language autopilot can route Sula upgrade intents
- fleet status displays project counts, executor, token count, and cost
- deterministic Sula fleet upgrades can complete without a model runner
- archive, workspace, and release-output directories are skipped
- shell executor results are preserved and can fall back to deterministic
  execution when incomplete
- a machine-wide run upgraded 31 discovered Sula projects with 0 executor tokens
  and $0.0000 model cost

Remaining gaps:

- no durable fleet run-id/resume model yet
- no project lock yet
- no executor preflight/repair command yet
- no capability registry yet
- no progress/no-progress detector yet
- no compact evidence-file default yet
- code-changing tasks still need a stronger Sula-native executor packet and
  review loop

## 18. Definition Of Done

The completion-first agent operating system is complete when:

- a user can state a goal in natural language
- Sula classifies the workflow or blocks honestly
- Sula chooses deterministic execution whenever possible
- code work is delegated to a capable low-cost executor
- executor permissions are preflighted and repaired when safe
- failed permissions trigger retry before host takeover
- long-running work continues while progress exists
- no-progress loops stop with a clear failure class
- fleet runs can resume after interruption
- target projects are locked during mutation
- dirty worktrees are protected and reported
- status is visible in every CLI
- detailed evidence is stored without flooding chat
- token, cost, runtime, retry, and progress are visible
- acceptance is based on validation evidence
- Sula check and doctor remain green
- real-project canaries prove the system works outside the Sula repository
