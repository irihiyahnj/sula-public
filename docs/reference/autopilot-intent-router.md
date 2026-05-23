# Sula Autopilot Intent Router

## Purpose

Sula Autopilot is the commandless entry layer for project maintenance. A user can state a goal in natural language, and every Sula-aware coding CLI should first ask Sula how that goal should be routed instead of immediately spending the host chat model on mechanical work.

The initial shipped slices cover Sula fleet upgrades and low-risk code-task dispatch. Fleet upgrades are repetitive, easy to validate, and often best handled by Sula's deterministic executor. Low-risk implementation and fix goals are routed into orchestration so the configured executor can do the long patch loop while the host model supervises, reviews, and accepts.

## Entry Contract

Agents should route natural-language maintenance goals through:

```bash
python3 scripts/sula.py auto --project-root . --intent "<user goal>"
```

For fleet work, agents may also pass an explicit scope:

```bash
python3 scripts/sula.py auto --project-root . \
  --intent "upgrade all Sula projects under this directory" \
  --scope /path/to/scope
```

Sula returns either:

- a routed autopilot workflow, such as `fleet.upgrade`
- a low-risk code task packet, such as `code.task`
- a blocked result when the goal is not classified yet

Unknown goals must stay blocked. Sula should not pretend to understand open-ended natural language before a portable workflow exists.

## Code Task Dispatch

Implementation and fix goals are classified as `code.task` when the user intent includes English action words such as `implement`, `implementation`, or `fix`, Chinese action words such as `实现` or `落地`, or a reference to a local Sula goal file under `.sula/local/`.

Dry-run mode only plans the task:

```bash
python3 scripts/sula.py auto --project-root . \
  --intent "执行 .sula/local/goal-file.md 中的落地任务" \
  --dry-run --json
```

Non-dry-run mode stores a low-risk automation intent and dispatches it through the existing orchestration pipeline when policy allows. That means the same risk ceiling, approval categories, runner route, executor contract, retry loop, status surface, and closeout checks apply to code tasks.

The host model remains responsible for:

- deciding whether the task is actually safe to treat as low-risk
- repairing runner permission or wrapper failures
- reviewing executor diffs and validation evidence
- closing or rejecting the run

The executor is expected to mutate only the scoped files required by the task and return JSON with touched files, validation evidence, token metrics, and cost metrics.

## Fleet Upgrade Guard

Fleet upgrades are executor-required by default.

The host model's job is:

- classify and plan
- verify Sula's route and status
- review executor evidence
- give corrective feedback if the executor fails
- decide whether the user-facing goal is complete

The executor's job is:

- run the mechanical project upgrade
- run the allowed Sula validation commands
- return structured status, validation evidence, touched files, and metrics

If an active project is behind the target version and has no configured real model runner, Sula uses its deterministic zero-model upgrade executor. That executor runs Sula's own `sync`, `doctor --strict`, `memory digest`, and `check` commands and reports zero token and zero model cost. The host model should review the resulting status and evidence instead of performing the mechanical upgrade itself.

## Supported Fleet Executor

The first real fleet executor adapter is project-local `shell-command`:

```toml
[orchestration]
runner = "shell-command"
runner_command = "path/to/local-wrapper"
workspace_mode = "copy"

[agent_routing.roles.executor]
provider = "deepseek"
model = "deepseek-v4-flash"
reasoning_effort = "xhigh"
write_access = true
```

The wrapper receives:

- `SULA_EXECUTOR_REQUIRED=true`
- `SULA_AGENT_ROLE=executor`
- `SULA_MODEL_PROVIDER`
- `SULA_MODEL_NAME`
- `SULA_MODEL_REASONING_EFFORT`
- `SULA_RUNNER_EFFORT`
- `SULA_FLEET_TASK_JSON`
- `SULA_AUTOPILOT_INTENT_JSON`

For Claude-style runner routes, Sula maps executor `xhigh` to runner effort `max` through `SULA_RUNNER_EFFORT`.

## Fleet Task Packet

`SULA_FLEET_TASK_JSON` contains:

- `task = "upgrade_sula_project"`
- `project_root`
- `current_version`
- `target_version`
- `source_script`
- `executor_required`
- allowed Sula commands for `sync`, `doctor --strict`, `memory digest`, and `check`
- forbidden behaviors, including destructive Git operations and business-code changes unless validation explicitly requires them
- expected JSON response fields

The wrapper should return one JSON object on stdout:

```json
{
  "status": "accepted",
  "summary": "Upgraded the project and validation passed.",
  "validation_evidence": ["sync ok", "doctor --strict ok", "check ok"],
  "metrics": {
    "runtime_seconds": 120,
    "token_count": 12000,
    "cost_usd": 0.02
  }
}
```

Valid statuses are `accepted`, `human-review`, `blocked`, and `failed`.

## Status Bar

Fleet runs write `.sula/state/fleet/latest.json` and expose a compact line:

```bash
python3 scripts/sula.py fleet status --project-root . --compact
```

The line follows the Sula visible-status style and includes reported executor
usage when wrappers return metrics:

```text
Sula: fleet/ok | Projects: 3/3 done | Main: codex/unknown/unknown | Executor: deepseek/deepseek-v4-flash/xhigh/max | Tokens: 12000 | Cost: $0.0200 | Guard: executor-required | Next: review report
```

This is the user-visible closure: they can see the active workflow, the supervising model, the executor route, whether the executor guard is active, and what needs attention next.

## Sync Impact

Existing projects remain compatible.

After syncing this release, Sula-managed `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `GEMINI.md`, and the docs map tell any AI coding CLI to route natural-language maintenance and low-risk implementation goals through `auto` first. Projects only need local executor configuration when they want real delegated execution instead of a blocked supervisor-only report or deterministic Sula maintenance path.
