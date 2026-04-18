# AGENTS.md

This file is the primary instruction source for AI agents working in this project.

If a tool-specific instruction file exists, treat it as a thin adapter to this file.
If any tool-specific file conflicts with this file, `AGENTS.md` wins.

## Project Identity

- Project root is `Client Service Drive Canary`.
- Project slug: `client-service-drive-canary`.
- Description: Client-service canary with Google Drive adapter metadata
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
