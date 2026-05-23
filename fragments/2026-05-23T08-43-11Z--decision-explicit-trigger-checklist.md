---
id: 2026-05-23T08-43-11Z--decision-explicit-trigger-checklist
time: 2026-05-23T08:43:11Z
kind: decision
refs: [2026-05-23T05-25-40Z--decision-enshrine-host-operating-protocol, 2026-05-23T06-22-58Z--correction-agents-md-legacy-vs-vector-ambiguity]
tags: [host-protocol, autonomy, agent-judgement, b8, c7]
author: jing
---
Operator feedback exposed a real protocol gap: the v1.0.1 host operating
protocol said "append fragments for any decision, intent, goal, fact,
artifact, annotation, or turn worth preserving (B8)". This was abstract.
Different LLMs interpreted "worth preserving" differently — some recorded
diligently, some deferred to the human ("you/agent decides what's worth
recording").

The user's framing was sharp: if the human still has to tell the agent
when to record, the system has not actually upleveled.

Fix at the right layer (C2): codify explicit triggers in the protocol
itself, so every LLM at every boot sees the same trigger list. The agent
is "told" exactly once — in the protocol — and thereafter operates
autonomously, without per-session reminders.

The new "Throughout the turn — when to append a fragment" section gives
8 positive triggers (decision, goal, fact, artifact, verification-fact,
correction, annotation, snapshot) and 5 explicit non-triggers (routine
formatting, cosmetic refactor, idempotent re-run, scheduler tick,
internal-only reasoning). C7 still limits churn; B8 still mandates
landing context. The new triggers operationalise both.

Distinction from auto-instrumentation: this is NOT "every git commit
becomes a fragment". That would violate C7 and overwhelm the signal.
The trigger list is per-EVENT, not per-commit. A 50-commit refactor
might emit one decision fragment ("decided to extract X into Y") and
one verification-fact fragment ("X-extraction tests passed"); it would
NOT emit 50 decision fragments.

Bulk applied to all 14 adopted projects on this device. migrate.py
suffix updated for future migrations.

The behavioural pattern this fixes: an agent reading AGENTS.md should
NEVER again say "human/agent decides what's worth recording". It should
say "I appended X, Y, Z because triggers 1, 4, 6 fired; I did not
append for these other things because they fall under non-triggers
2 and 3."
