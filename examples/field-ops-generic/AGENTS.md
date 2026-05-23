<!-- sula-vector-priority -->
> **Active host protocol:** see the "Sula Vector — Host Operating Protocol"
> section below (after the `<!-- sula-vector -->` sentinel). It is the authoritative
> protocol for any LLM operating in this project. Any rules above the sentinel
> that conflict with the protocol below are legacy from prior project conventions
> and are superseded.

# AGENTS.md

This file is the primary instruction source for AI agents working in this project.

If a tool-specific instruction file exists, treat it as a thin adapter to this file.
If any tool-specific file conflicts with this file, `AGENTS.md` wins.

## Project Identity

- Project root is `Field Ops Generic Canary`.
- Project slug: `field-ops-generic-canary`.
- Description: Generic-project canary for Sula rollout validation
- Default agent: `Codex`

## Highest Rule

- `Preserve project-owned truth while using Sula as a removable operating kernel.`

## Mandatory Working Rules

- Read this file before making changes.
- Preserve project-owned truth and use Sula as a removable operating kernel.
- Keep current human-readable state in [STATUS.md](STATUS.md).
- Keep detailed change reasoning in [CHANGE-RECORDS.md](CHANGE-RECORDS.md).
- Keep machine-owned kernel state under `.sula/`.
- If work touches `STATUS.md`, `CHANGE-RECORDS.md`, `docs/change-records/*`, `.sula/state/current.md`, `.sula/events/log.jsonl`, or `.sula/memory-digest.md`, finish by running `python3 scripts/sula.py check --project-root .`.
- Treat `SULA CHECK OK` as the completion gate for state-sync work, and prefer rebuilding generated `.sula/*` files through Sula commands instead of hand-editing them.
- If the project uses Git, prefer working branches with the `codex/*` prefix.
- If this project enables deeper visible Sula docs later, keep their maps and operating docs updated in the same change.

## Current Anchors

- Project entry: [README.md](README.md)
- Current execution lane: [README.md](README.md)
- Current state snapshot: [.sula/state/current.md](.sula/state/current.md)

## Commands

```bash
n/a
n/a
n/a
n/a
```

Commands may remain `n/a` until the project defines stronger local automation.

---

<!-- sula-vector -->
# Sula Vector — Host Operating Protocol

This project has migrated to the Sula Vector convention. The full
template lives at `tools/sula_vector/AGENTS.md`. Any LLM operating
in this project must follow the protocol below.

## At session start

1. Note the current ISO-8601 UTC time as your `session_start`.
2. Run `python3 tools/sula_vector/render.py . --for-agent` and read the output.
3. Treat that output as authoritative project context (Tier A–E principles + recent activity + open goals).

## Throughout the turn

- Append new fragments under `fragments/` for any decision, intent, goal, fact, artifact, annotation, or turn worth preserving (Tier B8).
- Filename: `<ISO-8601-time-Z>--<short-slug>.md`. Required frontmatter: `id`, `time`, `kind`.
- Append, never edit (Tier B1). To revise a previous decision or principle, append a new `kind: decision` whose `refs` includes the old fragment's id.
- Do not append if nothing meaningful changed (Tier C7).

## At end of turn

If you appended any fragments this turn, end your reply with the
output of:

```
python3 tools/sula_vector/render.py . --view changes-summary --since <session_start>
```

Display the full multi-line `[sula] +N this turn:` block to the
user. If the output is `[sula] no changes`, do not display it.
