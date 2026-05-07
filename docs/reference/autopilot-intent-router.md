# Sula Autopilot Intent Router

## Purpose

Sula Autopilot is the commandless entry layer for project maintenance. A user can state a goal in natural language, and every Sula-aware coding CLI should first ask Sula how that goal should be routed instead of immediately spending the host chat model on mechanical work.

The initial shipped slice focuses on Sula fleet upgrades because they are repetitive, easy to validate, and expensive when a high-end host model performs them directly.

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
- a blocked result when the goal is not classified yet

Unknown goals must stay blocked. Sula should not pretend to understand open-ended natural language before a portable workflow exists.

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

After syncing this release, Sula-managed `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `GEMINI.md`, and the docs map tell any AI coding CLI to route natural-language maintenance goals through `auto` first. Projects only need local executor configuration when they want real delegated execution instead of a blocked supervisor-only report.
