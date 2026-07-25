# GitHub Copilot Instructions

This project runs on the Sula Vector convention. **[AGENTS.md](AGENTS.md) is
the authoritative protocol** — read it first and follow it exactly.

Boot (two steps): note the current UTC time as your session start, then run

```bash
python3 tools/sula_vector/render.py . --for-agent
```

Record judgments with `tools/sula_vector/note.py`. Mechanical evidence (files
produced, commits made) is captured by `tools/sula_vector/skills/witness.py`;
do not narrate it by hand.

Nothing in this file overrides AGENTS.md. Legacy Sula 0.18.x instructions
(`scripts/sula.py`, `.sula/`, `STATUS.md`) are historical reference only.
