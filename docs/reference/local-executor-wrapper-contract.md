# Local Executor Wrapper Contract

Sula Core does not call model provider APIs directly. Real executor model calls
belong in project-local runner commands, usually under `.sula/local/`, so each
project can choose its own CLI, model, API key environment, and permission
boundary without leaking local configuration into reusable Sula truth.

## When This Applies

This contract applies when a project configures a real executor runner, for
example:

```bash
python3 scripts/sula.py agent-routing configure --project-root . \
  --runner shell-command \
  --runner-command .sula/local/deepseek-flash-executor.sh \
  --provider deepseek \
  --model deepseek-v4-flash \
  --reasoning-effort xhigh \
  --workspace-mode copy \
  --write-access
```

Sula will dispatch the command inside the configured workspace. The wrapper is
responsible for calling Claude Code, Hermes, DeepSeek, or any other local model
surface.

## Inputs

Shell-command wrappers receive Sula context through environment variables.

Required routing fields:

- `SULA_RUN_ID`
- `SULA_TASK_ID`
- `SULA_TASK_TITLE`
- `SULA_AGENT_ROLE`
- `SULA_MODEL_PROVIDER`
- `SULA_MODEL_NAME`
- `SULA_MODEL_REASONING_EFFORT`
- `SULA_RUNNER_EFFORT`
- `SULA_ROUTING_CYCLE`

Executor contract:

- `SULA_EXECUTOR_CONTRACT_JSON`: JSON object with `context_mode`,
  `output_contract`, `default_reasoning_effort`, `max_turns`,
  `max_run_minutes`, `max_cost_cents`, `max_cost_usd`, and
  `budget_breach_behavior`.

Execution packet:

- `SULA_EXECUTION_PACKET_JSON`: minimal task packet with task id, title,
  description, risk, labels, acceptance criteria, validation requirements, diff
  scope, forbidden behaviors, and expected output fields.

Wrappers should prefer `SULA_EXECUTION_PACKET_JSON` over rereading tracker files.
The packet is the Sula-owned bounded work order.

## Expected Behavior

A good local wrapper should:

- pass only the bounded execution packet and relevant repo rules to the model;
- run in `workspace_mode = "copy"` unless the project intentionally allows root
  mutation;
- use non-interactive permissions suitable for the copied workspace;
- ask the model for strict JSON output;
- stop and report a blocker instead of asking interactive permission questions;
- run validation requirements when safe and available;
- return token and cost metrics when the underlying CLI reports them.

`executor_max_cost_cents = 0` means open cost by default. Sula records and shows
reported cost, but it does not fail a long task solely because spend exceeded a
small default threshold. Projects that need strict caps can set a positive
value.

## Output

The wrapper should print one JSON object to stdout:

```json
{
  "status": "human-review",
  "summary": "what changed or why blocked",
  "touched_files": ["relative/path"],
  "validation_evidence": [
    {"kind": "command", "summary": "command and result"}
  ],
  "metrics": {
    "token_count": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_input_tokens": 0,
    "cost_usd": 0
  },
  "links": [],
  "reusable_lessons": [],
  "blocked_reasons": []
}
```

Allowed `status` values are `human-review`, `blocked`, `failed`, and `accepted`.
Most real executor work should return `human-review`; Sula review and closeout
remain the acceptance gate.

## Minimal Claude-Style Wrapper Shape

The wrapper should build a prompt from `SULA_EXECUTOR_CONTRACT_JSON` and
`SULA_EXECUTION_PACKET_JSON`, call the local CLI, parse the CLI result envelope,
then print the Sula output JSON above. If the model's final text is itself JSON,
merge its `summary`, `touched_files`, `validation_evidence`, `links`, and
`blocked_reasons` into the final output.

Do not print raw provider secrets, command traces containing secrets, or full
large model transcripts.
