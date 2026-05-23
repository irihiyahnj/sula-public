<!-- sula-vector-priority -->
> **Active host protocol:** see the "Sula Vector — Host Operating Protocol"
> section below (after the `

---

<!-- sula-vector -->
# Sula Vector — Host Operating Protocol

This project has migrated to the Sula Vector convention. The full
template lives at `tools/sula_vector/AGENTS.md`. Any LLM operating
in this project must follow the protocol below.

## At session start

1. Note the current ISO-8601 UTC time as your `session_start`.
2. Run `python3 tools/sula_vector/skills/auto-update-from-canonical.py --project-root . --quiet` (best-effort tooling refresh; silent on no-op or unreachable network; emits a `kind: operation` fragment only on actual update).
3. Run `python3 tools/sula_vector/render.py . --for-agent` and read the output.
4. Treat that output as authoritative project context (Tier A–E principles + recent activity + open goals).

## Throughout the turn — when to append a fragment

**Append a fragment without being asked** whenever any of these triggers fires:

| Trigger | kind |
|---|---|
| You make or revise a non-trivial architectural / design / direction choice | `decision` |
| You commit to a measurable outcome with stop conditions | `goal` (with `done_when` + `verifier_ref`, B9) |
| You observe a real-world state change (deploy, build passed, contract signed, external event) | `fact` |
| You produce or register a deliverable (code module, doc, deck, design, artifact) | `artifact` (with `pointer`) |
| A verifier ran and produced a result | `verification-fact` (with `passed: true/false` + `refs` to the goal/intent) |
| You discover a real error, stale claim, or contradiction in a prior fragment | `correction` (with `refs` to it) |
| Someone (or you) makes a comment / markup on a fragment or artifact | `annotation` |
| You take a deliberate project-state snapshot for handoff or audit | `snapshot` |

**Do NOT append** for any of:

- Routine code formatting / style fixes that carry no decision content
- Cosmetic refactors that change neither behaviour nor contract
- Re-running idempotent operations with zero net effect (C7)
- Repetitive scheduler / cron firings (already handled inside skills)
- Internal reasoning that did not land in a concrete decision or artefact

If unsure, lean toward appending — but skip if it would only be churn (C7).

## Append rules

- Filename: `<ISO-8601-time-Z>--<short-slug>.md`. Required frontmatter: `id`, `time`, `kind`.
- Append, never edit (Tier B1). To revise a previous decision or principle, append a new `kind: decision` whose `refs` includes the old fragment's id.
- Reference upstream context with `refs` so the graph stays connected.

## At end of turn

If you appended any fragments this turn, end your reply with the
output of:

```
python3 tools/sula_vector/render.py . --view changes-summary --since <session_start>
```

Display the full multi-line `[sula] +N this turn:` block to the
user. If the output is `[sula] no changes`, do not display it.
